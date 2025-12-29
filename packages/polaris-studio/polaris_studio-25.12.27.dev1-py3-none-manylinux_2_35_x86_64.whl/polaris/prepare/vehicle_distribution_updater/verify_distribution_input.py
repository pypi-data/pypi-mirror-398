# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from typing import List

import pandas as pd


def verify_veh_dist_input(dist_df: pd.DataFrame, controls: List[str], fleet_mode=False) -> pd.DataFrame:
    # check required fields
    req_fields = ["POLARIS_ID", "VINTAGE", "PROPORTION"] + controls
    if not fleet_mode:
        req_fields.append("TRACT")
    for r in req_fields:
        found = False
        for c in dist_df.columns:
            if r in c.upper():
                found = True
                dist_df=dist_df.rename({c: r}, axis=1)
                break
        if not found:
            raise ValueError(f"Error, missing field '{r}' in source vehicle distribution data file.")

    upper_fields = [x for x in req_fields if x in list(dist_df.select_dtypes(include=['object', 'string']).columns)]
    for field in upper_fields:
        dist_df[field] = dist_df[field].str.upper()
    return dist_df
