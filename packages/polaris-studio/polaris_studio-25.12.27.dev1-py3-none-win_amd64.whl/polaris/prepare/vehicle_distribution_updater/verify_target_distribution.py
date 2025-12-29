# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import pandas as pd


def verify_target_distribution(target_df: pd.DataFrame) -> pd.DataFrame:
    target_headers = list(target_df.index.names)
    target_list = ["POLARIS_ID", "VEHICLE_CLASS", "POWERTRAIN", "FUEL", "AUTOMATION", "CONNECTIVITY", "VINTAGE"]

    for t in [t for t in target_headers[:-1] if t is not None]:
        if str(t).upper() not in target_list:
            raise ValueError(f"ERROR: target file must be from the following list: {str(target_list)}")

    # make sure distribution is valid
    tot = target_df.PROPORTION.sum()
    if abs(tot - 1) > 0.01:
        raise ValueError(f"Error, total proportions specified for target distribution is too far from 100%: {tot:,.2f}")

    # Makes sure we are exactly at 100%
    target_df["PROPORTION"] /= tot

    indices = list(target_df.index.names)
    target_df = target_df.reset_index()
    upper_fields = [x for x in target_list if x in list(target_df.select_dtypes(include=['object', 'string']).columns)]
    for field in upper_fields:
        target_df[field] = target_df[field].str.upper()
    target_df = target_df.set_index(indices)
    return target_df.rename(columns={target_df.columns[-1]: "value"})
