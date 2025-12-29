# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from polaris.utils.database.db_utils import add_column_unless_exists, has_table
from polaris.utils.database.standard_database import DatabaseType, StandardDatabase


def migrate(conn):
    for lu in ["EDUCATION_PREK", "EDUCATION_K_8", "EDUCATION_9_12", "HIGHER_EDUCATION"]:
        conn.execute(
            f"""INSERT OR IGNORE INTO land_use(land_use, is_home, is_work, is_school, is_discretionary, notes)
                VALUES('{lu}',0,1,1,0,'Inserted by migration 20250614');"""
        )
    conn.execute("UPDATE Location SET land_use='EDUCATION_PREK' WHERE land_use == 'EDUCATION';")
    conn.execute("DELETE FROM land_use WHERE land_use='EDUCATION';")

    # Add enrolments column for locations
    if not has_table(conn, "Location_Attributes"):
        StandardDatabase.for_type(DatabaseType.Supply).add_table(conn, "Location_Attributes", None, add_defaults=False)
    add_column_unless_exists(conn, "Location_Attributes", "enrolments", "REAL")
