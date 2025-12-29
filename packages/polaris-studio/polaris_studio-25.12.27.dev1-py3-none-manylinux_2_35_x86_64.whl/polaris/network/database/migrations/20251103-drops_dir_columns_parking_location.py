# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md

from packaging import version

from polaris.utils.database.db_utils import has_column, without_triggers


def migrate(conn):
    sql_ver = conn.execute("SELECT sqlite_version()").fetchone()[0]

    if version.parse(sql_ver) >= version.parse("3.35.0"):
        triggers = ["ISO_metadata_reference_row_id_value_update", "ISO_metadata_reference_row_id_value_insert"]
        with without_triggers(conn, triggers):
            # direct drop supported
            if has_column(conn, "Location", "dir"):
                conn.execute('ALTER TABLE "Location" DROP COLUMN "dir"')
            if has_column(conn, "Parking", "dir"):
                conn.execute('ALTER TABLE "Parking" DROP COLUMN "dir"')
    else:
        raise RuntimeError("SQLite version does not support dropping columns. Please upgrade to 3.35.0 or later.")
