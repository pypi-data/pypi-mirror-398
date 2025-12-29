# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from pathlib import Path

from polaris.network.utils.unzips_spatialite import jumpstart_spatialite
from polaris.utils.database.db_utils import commit_and_close, has_table


def start_cache(db_filename: Path) -> None:
    if not db_filename.exists():
        jumpstart_spatialite(db_filename)

    table_sql = [
        """CREATE TABLE IF NOT EXISTS osm_traffic_signals(
                                                          osm_id         INTEGER NOT NULL PRIMARY KEY,
                                                          download_id    TEXT
     );""",
        "select AddGeometryColumn( 'osm_traffic_signals', 'geo', 4326, 'POINT', 'XY', 1);",
        "select CreateSpatialIndex( 'osm_traffic_signals' , 'geo' );",
    ]
    downloads_sql = [
        """CREATE TABLE IF NOT EXISTS osm_traffic_signal_downloads(
                                                                   id             TEXT PRIMARY KEY,
                                                                   download_date  TEXT
        );""",
        "select AddGeometryColumn( 'osm_traffic_signal_downloads', 'geo', 4326, 'POLYGON', 'XY', 1);",
        "select CreateSpatialIndex( 'osm_traffic_signal_downloads' , 'geo' );",
    ]

    ovm_downloads_sql = [
        """CREATE TABLE IF NOT EXISTS overture_downloads(
                                                 table_name     TEXT PRIMARY KEY,
                                                 download_date  TEXT,
                                                 data_theme     TEXT
        );""",
    ]

    with commit_and_close(db_filename, spatial=True) as conn:
        sqls = [] if has_table(conn, "osm_traffic_signals") else table_sql
        sqls += [] if has_table(conn, "osm_traffic_signal_downloads") else downloads_sql
        sqls += [] if has_table(conn, "overture_downloads") else ovm_downloads_sql

        for sql in sqls:
            conn.execute(sql)
