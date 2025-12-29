# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from contextlib import contextmanager
from sqlite3 import Connection

from polaris.network.starts_logging import logger
from polaris.utils.database.standard_database import StandardDatabase


@contextmanager
def without_table_indices(conn: Connection, db: StandardDatabase):
    import pandas as pd

    sql = "SELECT name as tr_name, tbl_name, sql as qry FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%'"
    data_indices = pd.read_sql(sql, conn)
    data_indices = data_indices[data_indices.tr_name.str.contains("idx_polaris")]

    try:
        logger.info("  Deleting indices")
        for _, rec in data_indices.iterrows():
            conn.execute(f"DROP INDEX IF EXISTS {rec.tr_name};")
        for table in db.geo_tables:
            conn.execute(f"SELECT DisableSpatialIndex('{table}', 'geo');")
        conn.commit()
        yield
    finally:
        logger.info("  Recreating indices")
        for _, rec in data_indices.iterrows():
            conn.execute(rec["qry"])
        conn.commit()
        for table in db.geo_tables:
            conn.execute(f"SELECT CreateSpatialIndex('{table}', 'geo');")
        conn.commit()
        conn.execute("select RecoverSpatialIndex();")
