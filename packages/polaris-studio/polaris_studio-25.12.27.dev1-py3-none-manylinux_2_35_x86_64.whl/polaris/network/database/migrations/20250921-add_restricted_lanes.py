# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from polaris.utils.database.db_utils import has_table, read_about_model_value, write_about_model_value
from polaris.utils.database.standard_database import DatabaseType, StandardDatabase


def migrate(conn):

    db = StandardDatabase.for_type(DatabaseType.Supply)
    if not has_table(conn, "Restricted_Lanes"):
        db.add_table(conn, "Restricted_Lanes", None, add_defaults=False)

    # Make sure that there is a record of the link ID offset for restricted lanes in the about_model table
    current_value = read_about_model_value(conn, "restricted_lanes_link_id_offset", default="100000000")
    write_about_model_value(conn, "restricted_lanes_link_id_offset", current_value)
