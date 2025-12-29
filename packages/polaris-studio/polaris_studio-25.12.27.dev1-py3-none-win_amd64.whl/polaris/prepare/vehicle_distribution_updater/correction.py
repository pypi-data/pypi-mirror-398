# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import pandas as pd


def correct_across_tracts(df: pd.DataFrame) -> pd.DataFrame:
    cols = df.columns.tolist()
    df2 = df.groupby(["TRACT"]).sum(numeric_only=True)[["PROPORTION"]].rename(columns={"PROPORTION": "FACTOR"})
    df = df.set_index(["TRACT"]).join(df2)
    df.PROPORTION /= df.FACTOR
    df.PROPORTION.fillna(0)
    return pd.DataFrame(df.reset_index()[cols])
