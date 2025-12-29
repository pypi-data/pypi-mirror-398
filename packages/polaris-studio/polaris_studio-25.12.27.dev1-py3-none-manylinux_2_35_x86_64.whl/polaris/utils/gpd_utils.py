# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import re
import sqlite3
from typing import Optional

import geopandas as gpd

from polaris.network.utils.srid import get_table_srid
from polaris.utils.database.db_utils import commit_and_close, has_table, read_and_close
from polaris.utils.structure_finder import find_table_fields
from polaris.utils.type_utils import AnyPath


def write_spatialite_layer(
        gdf: gpd.GeoDataFrame,
        table_name: str,
        conn=None,
        db_path=None,
        overwrite: bool = False,
):
    geo_type = gdf.geometry.values[0].geom_type.upper()
    geo_type = "MULTIPOLYGON" if geo_type == "POLYGON" else geo_type
    srid = gdf.crs.to_epsg()

    with conn or commit_and_close(db=db_path, spatial=True) as conn:
        if has_table(conn, table_name):
            if overwrite:
                conn.execute(f"DROP TABLE {table_name}")
                conn.commit()
            else:
                raise ValueError(f"Table {table_name} already exists. Use overwrite=True to replace it.")

        cols = list(gdf.columns)
        cols.remove("geometry")

        s = f"CREATE TABLE IF NOT EXISTS {table_name}("
        for col in cols:
            if gdf[col].dtype in ["float64", "float32"]:
                s += f"{col} NUMERIC,"
            elif gdf[col].dtype in ["int64", "int32"]:
                s += f"{col} INTEGER,"
            else:
                s += f"{col} TEXT,"
                gdf[col] = gdf[col].astype(str)

        queries = [
            s[:-1] + ");",
            f"select AddGeometryColumn( '{table_name}', 'geo', {srid}, '{geo_type}', 'XY', 1);",
            f"select CreateSpatialIndex( '{table_name}' , 'geo' );",
        ]

        insert_sql = f"INSERT INTO {table_name}({','.join(cols + ['geo'])}) VALUES ({','.join(['?'] * (len(cols)))},"
        insert_sql += "CastToMulti(GeomFromWKB(?, ?)))" if "MULTI" in geo_type else "GeomFromWKB(?, ?))"

        gdf = gdf.assign(geo_wkb=gdf.geometry.to_wkb(), srid=srid)
        data = gdf[cols + ["geo_wkb", "srid"]].to_records(index=False)
        for s in queries:
            conn.execute(s)
        conn.executemany(insert_sql, data)
        conn.commit()


def read_spatialite_layer(
        table_name: str,
        conn: Optional[sqlite3.Connection] = None,
        db_path: Optional[AnyPath] = None,
        filter="",
) -> gpd.GeoDataFrame:
    with conn or read_and_close(db_path, spatial=True) as conn:
        if not has_table(conn, table_name):
            raise ValueError(f"Table {table_name} does not exist in the database.")

        fields, _, geo_field = find_table_fields(conn, table_name)
        fields = [f'"{x}"' for x in fields]
        fields.append(f"Hex(ST_AsBinary({geo_field})) as {geo_field}")
        keys = ",".join(fields)

        sql = f"select {keys} from '{table_name}' WHERE {geo_field} IS NOT null {clean_filter_gdf(filter)};"
        return gpd.GeoDataFrame.from_postgis(sql, conn, geom_col=geo_field, crs=get_table_srid(conn, table_name))


def clean_filter_gdf(filter: str) -> str:
    if filter.strip() == "":
        return ""
    if filter.lower().strip().startswith("where"):
         return re.sub(r'where', 'AND', filter, flags=re.IGNORECASE).strip()
    elif filter.lower().strip().startswith("and"):
        return filter.strip()
    return f"AND {filter}"
