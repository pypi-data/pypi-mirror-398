# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.wkt import loads as wkt_loads

from polaris.utils.file_utils import df_from_file


def table_from_disk(table_path: Path) -> pd.DataFrame:
    def clear_colum_index_name(df: pd.DataFrame):
        df.columns = [x.replace("index", "_index") for x in df.columns]  # type: ignore
        return df

    schema_path = table_path.parent / (str(table_path.stem) + ".schema")
    if schema_path.exists():
        schema = pd.read_csv(schema_path)
        if schema.pk.sum():
            pk = schema[schema.pk == 1].name.values[0]
            return df_from_file(table_path, low_memory=True).set_index(pk.lower())
    return clear_colum_index_name(df_from_file(table_path, low_memory=True))


def geo_table_from_disk(table_path: Path) -> gpd.GeoDataFrame:
    df = table_from_disk(table_path)
    assert "geo_wkt" in df.columns, "Geo table must have a geo_wkt column"

    table_name = table_path.stem.lower()
    srids = pd.read_csv(table_path.parent / "srids.csv")
    srid = int(srids.loc[srids.table_name == table_name, "srid"].values[0])
    geometries = df["geo_wkt"].apply(wkt_loads)  # type: ignore
    return gpd.GeoDataFrame(df.drop(columns=["geo_wkt"]), geometry=geometries, crs=f"EPSG:{srid}")
