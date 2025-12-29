# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import hashlib
import logging
import os
from tempfile import gettempdir

import duckdb
import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon

from polaris.network.open_data.open_data_utils import start_cache
from polaris.utils.database.db_utils import read_and_close, commit_and_close
from polaris.utils.gpd_utils import write_spatialite_layer, read_spatialite_layer


def get_overture_elements(model_area: gpd.GeoDataFrame, theme: str) -> gpd.GeoDataFrame:
    from polaris.utils.user_configs import UserConfig

    transformed_ma = model_area.to_crs(4326)
    unary_union = transformed_ma.union_all()

    cache_name = tempfile_cache(unary_union, theme)
    start_cache(UserConfig().open_data_cache)
    with read_and_close(UserConfig().open_data_cache, spatial=True) as conn:
        if cache_name in pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn).values:
            return read_spatialite_layer(cache_name, conn)

    overture_url = UserConfig().overture_url

    tempfile_name = os.path.join(gettempdir(), cache_name + f"_{theme}.parquet")

    # Otherwise we download it
    minx, miny, maxx, maxy = unary_union.bounds
    conn = duckdb.connect()
    c = conn.cursor()

    c.execute("""INSTALL spatial; INSTALL httpfs; INSTALL parquet;""")
    c.execute("""LOAD spatial; LOAD parquet; SET s3_region='us-west-2';""")

    logging.info(f"Downloading {theme} from Overture maps. Sit tight! This may take a while.")
    qrys = {
        "buildings": f"""COPY (
                    SELECT id, height, class, subtype as land_use, num_floors_underground, num_floors, names, geometry
                    FROM read_parquet('{overture_url}/theme=buildings/type=*/*', filename=true, hive_partitioning=1, union_by_name = true)
                    WHERE bbox.xmin BETWEEN {minx} AND {maxx} AND bbox.ymin BETWEEN {miny} AND {maxy}
                    ) TO '{tempfile_name}'
                WITH (FORMAT 'parquet', COMPRESSION 'ZSTD');""",
        "places": f"""COPY (
                    SELECT id, names.primary AS name, categories.primary as main_category, categories.alternate as other_categories, confidence, geometry
                    FROM read_parquet('{overture_url}/theme=places/type=*/*')
                    WHERE bbox.xmin BETWEEN {minx} AND {maxx} AND bbox.ymin BETWEEN {miny} AND {maxy}
                    ) TO '{tempfile_name}'
                WITH (FORMAT 'parquet', COMPRESSION 'ZSTD');""",
        "land_use": f"""COPY (
                    SELECT subtype, class AS land_use_class, names.primary AS name, surface, geometry
                    FROM read_parquet('{overture_url}/theme=base/type=land_use/*')
                    WHERE bbox.xmin BETWEEN {minx} AND {maxx} AND bbox.ymin BETWEEN {miny} AND {maxy}
                    ) TO '{tempfile_name}'
                WITH (FORMAT 'parquet', COMPRESSION 'ZSTD');""",
    }

    _ = c.execute(qrys[theme])

    logging.info(f"{theme} data downloaded. Basic geo-processing")
    df = pd.read_parquet(tempfile_name)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkb(df.geometry, crs=4326))
    joined = gdf.sjoin(transformed_ma)
    gdf = gdf[gdf.index.isin(joined.index.unique())]

    if theme.lower() == "buildings":
        # Add floor area to buildings
        gdf = gdf.assign(floor_area=gdf.geometry.to_crs(3857).area)

    # Now we save the data downloaded to cache
    with commit_and_close(UserConfig().open_data_cache, spatial=True) as conn:
        data = [cache_name, pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), theme]
        conn.execute("INSERT INTO overture_downloads (table_name, download_date, data_theme) VALUES (?,?,?)", data)
        write_spatialite_layer(gdf, cache_name, conn=conn)

    # Return the data
    return gdf


def tempfile_cache(unary_union: MultiPolygon, theme) -> str:
    # Create the hash object
    hash_object = hashlib.md5(str(round(sum(unary_union.bounds), 5)).encode())
    return f"{theme}_{hash_object.hexdigest()[:10]}"
