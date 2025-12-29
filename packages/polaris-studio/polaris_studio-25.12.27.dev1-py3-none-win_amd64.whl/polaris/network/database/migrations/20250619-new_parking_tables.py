# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from polaris.utils.database.db_utils import add_column_unless_exists, drop_column_if_exists, has_table, without_triggers
from polaris.utils.database.standard_database import DatabaseType, StandardDatabase
import pandas as pd


def migrate(conn):
    db = StandardDatabase.for_type(DatabaseType.Supply)

    read_parking_query = """SELECT * FROM Parking """
    parking = pd.read_sql_query(read_parking_query, conn)

    # Add Parking_Pricing if doesn't exist
    if not has_table(conn, "Parking_Pricing"):
        db.add_table(conn, "Parking_Pricing", None, add_defaults=False)
    # Add Parking_Rule if doesn't exist
    if not has_table(conn, "Parking_Rule"):
        db.add_table(conn, "Parking_Rule", None, add_defaults=False)

    # Check if Parking_Pricing table is empty. If empty, update it using the Parking table
    read_parking_pricing_query = "SELECT COUNT(*) FROM Parking_Pricing"
    parking_pricing_count = conn.execute(read_parking_pricing_query).fetchone()

    if parking_pricing_count[0] == 0:
        sql = (
            'Insert into Parking_Pricing("parking", "parking_rule", "entry_start", "entry_end", "price")'
            + "VALUES(?, ?, ?, ?, ?)"
        )

        required_cols = {"time_in", "time_out", "hourly"}
        if required_cols.issubset(parking.columns):
            parking_pricing = parking[["parking", "time_in", "time_out", "hourly"]].copy()
        else:
            parking_pricing = parking[["parking"]].copy()
            parking_pricing["time_in"] = 0
            parking_pricing["time_out"] = 86400
            parking_pricing["hourly"] = 0
        # rules should be unique (for now one unique rule for each parking)
        parking_pricing["parking_rule"] = parking_pricing["parking"]
        parking_pricing = parking_pricing.rename(
            columns={"hourly": "price", "time_in": "entry_start", "time_out": "entry_end"})

        data = parking_pricing[["parking", "parking_rule", "entry_start", "entry_end", "price"]].to_records(index=False)
        conn.executemany(sql, data)

    # Check if Parking_Rule table is empty. If empty, update it using the Parking table
    read_parking_rule_query = "SELECT COUNT(*) FROM Parking_Rule"
    parking_rule_count = conn.execute(read_parking_rule_query).fetchone()

    if parking_rule_count[0] == 0:
        sql = (
            'Insert into Parking_Rule("parking_rule", "parking", "rule_type", "rule_priority", "min_cost", "min_duration", "max_duration")'
            + "VALUES(?, ?, ?, ?, ?, ?, ?)"
        )
        required_cols = {"time_in", "time_out"}
        if required_cols.issubset(parking.columns):
            parking_rule = parking[["parking", "time_in", "time_out"]].copy()
            parking_rule["max_duration"] = parking["time_out"] - parking["time_in"]
            parking_rule["min_cost"] = parking["hourly"]
        else:
            parking_rule = parking[["parking"]].copy()
            parking_rule["max_duration"] = 86400
            parking_rule["min_cost"] = 0
        # rules should be unique (for now one unique rule for each parking)
        parking_rule["parking_rule"] = parking_rule["parking"]
        parking_rule["rule_type"] = 3
        parking_rule["rule_priority"] = 1
        parking_rule["min_duration"] = 0

        data = parking_rule[
            ["parking_rule", "parking", "rule_type", "rule_priority", "min_cost", "min_duration", "max_duration"]
        ].to_records(index=False)
        conn.executemany(sql, data)

    # Delete columns (if exist) that are outdated from Parking
    triggers = [
        "ISO_metadata_reference_row_id_value_update",
        "ISO_metadata_reference_row_id_value_insert",
    ]

    columns_to_delete = ["start", "end", "time_in", "time_out", "hourly", "daily", "monthly"]

    with without_triggers(conn, triggers):
        for column in columns_to_delete:
            drop_column_if_exists(conn, "Parking", f"{column}")

    # Add num_escooters column into Parking
    add_column_unless_exists(conn, "Parking", "num_escooters", "INTEGER", "DEFAULT 0")
    add_column_unless_exists(conn, "Parking", "close_time", "INTEGER", "DEFAULT 864000")

    read_parking_query = "SELECT COUNT(*) FROM Parking WHERE close_time > 0"
    parking_closetime_count = conn.execute(read_parking_query).fetchone()

    if parking_closetime_count[0] == 0:
        required_cols = {"time_out"}
        if required_cols.issubset(parking.columns):
            parking["time_out"] = parking["time_out"].astype(int)
            parking.loc[parking["time_out"] == 86400, "time_out"] = 864000
            data = parking[["time_out", "parking"]].to_records(index=False)
            query = "UPDATE Parking SET close_time = ? WHERE parking = ?"
            conn.executemany(query, data)
