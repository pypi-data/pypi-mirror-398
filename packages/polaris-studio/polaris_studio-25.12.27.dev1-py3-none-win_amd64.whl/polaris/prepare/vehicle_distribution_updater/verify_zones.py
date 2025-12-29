# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import pandas as pd


def verify_zone_input(zone_df: pd.DataFrame) -> pd.DataFrame:
    # check that the zone_df is a two column file - should be Tract, Count
    zone_headers = list(zone_df.columns)
    if len(zone_headers) > 2:
        raise ValueError("Error, too many columns in the zone vehicle count file. Should be only Tract, Count")
    return zone_df.set_index("TRACT")
