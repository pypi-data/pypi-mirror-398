# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from polaris.network.consistency.geo_consistency import GeoConsistency
from polaris.utils.database.db_utils import add_column_unless_exists, commit_and_close, has_nulls


def migrate(path_to_file):
    with commit_and_close(path_to_file, spatial=True) as conn:
        add_column_unless_exists(conn, "Location", "walk_setback", "REAL")
        add_column_unless_exists(conn, "Location", "bike_setback", "REAL")
        add_column_unless_exists(conn, "Parking", "walk_setback", "REAL")
        add_column_unless_exists(conn, "Parking", "bike_setback", "REAL")
        nulls = any(has_nulls(conn, t, c + "_setback") for c in ["walk", "bike"] for t in ["Location", "Parking"])

    if nulls:
        GeoConsistency.from_supply_file(path_to_file).update_active_network_association()
