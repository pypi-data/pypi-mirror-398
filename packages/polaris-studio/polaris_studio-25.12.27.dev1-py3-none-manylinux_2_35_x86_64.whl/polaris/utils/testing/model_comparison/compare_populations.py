# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import filecmp
import json
import logging
from pathlib import Path
from typing import Dict

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from polaris import Polaris
from polaris.utils.config_utils import find_sf1
from polaris.utils.database.data_table_access import DataTableAccess
from polaris.utils.plot_utils import text_figure
from polaris.utils.testing.model_comparison.get_csv_table import geo_table_from_disk


def pop_comparison(sf1_: pd.DataFrame, sf1_new: pd.DataFrame, popsyn_regions: gpd.GeoDataFrame) -> plt.Figure:
    if min(sf1_.shape[0], sf1_new.shape[0]) == 0:
        return text_figure("One of the Trips dataframes is empty")

    sf1_.columns = sf1_.columns.str.lower()
    sf1_new.columns = sf1_new.columns.str.lower()

    geo_id = list(sf1_.columns)[0]
    sf1_ = sf1_.rename(columns={"persons": "pop_before", "pop": "pop_before"}) # type: ignore
    if "pop_before" not in sf1_.columns:
        return text_figure("Could not find the expected fields in the new sf1 file")
    sf1_ = sf1_.set_index(geo_id)

    sf1_new = sf1_new.rename(columns={"persons": "pop_new", "pop": "pop_new"}) # type: ignore
    if "pop_new" not in sf1_new.columns or geo_id not in sf1_new.columns:
        return text_figure("Could not find the expected fields in the new sf1 file")
    sf1_new=sf1_new.set_index(geo_id)

    pop = sf1_new[["pop_new"]].join(sf1_[["pop_before"]])
    pop = pop.assign(difference=pop.pop_new - pop.pop_before).reset_index()
    if pop.difference.abs().max() < 1:
        logging.info("No significant population differences found between the two scenarios.")
        return text_figure("No significant population differences found between the two scenarios")

    gdf_plot = popsyn_regions.merge(pop[[geo_id, "difference"]], left_on="popsyn_region", right_on=geo_id)

    ax = gdf_plot.plot(column="difference", legend=True, figsize=(8, 6))  # type: ignore
    ax.set_title("Population Change (new population minus old)", fontsize=14)
    return ax.get_figure()


def get_popsyn_regions(model_path: Path) -> gpd.GeoDataFrame:
    supply_file = Polaris.from_dir(model_path).supply_file
    if supply_file.exists():
        return DataTableAccess(supply_file).get("popsyn_region")
    else:
        return popsyn_region_from_dump(model_path / "supply")


def popsyn_region_from_dump(dump_path: Path) -> gpd.GeoDataFrame:
    if (dump_path / "popsyn_region.parquet").exists():
        return geo_table_from_disk(dump_path / "popsyn_region.parquet").reset_index()
    elif (dump_path / "popsyn_region.csv").exists():
        return geo_table_from_disk(dump_path / "popsyn_region.csv").reset_index()
    else:
        raise ValueError("No popsyn_region file found in model supply folder.")


def compare_populations(old_path: str, new_path: str, base_only=False) -> Dict[str, plt.Figure]:
    report = {}
    old_pth = Path(old_path)
    new_pth = Path(new_path)

    base_sf1_pth = find_sf1(old_pth, old_pth / "scenario_abm.json")
    new_sf1_pth = find_sf1(new_pth, new_pth / "scenario_abm.json")

    popsyn_regions = get_popsyn_regions(new_pth)

    if base_sf1_pth.exists() and new_sf1_pth.exists():
        if not filecmp.cmp(base_sf1_pth, new_sf1_pth, shallow=False):
            base_sf1_df = pd.read_csv(base_sf1_pth, sep="\t" if base_sf1_pth.suffix == ".txt" else ",")
            new_sf1_df = pd.read_csv(new_sf1_pth, sep="\t" if new_sf1_pth.suffix == ".txt" else ",")
            report["Base population comparison"] = pop_comparison(base_sf1_df, new_sf1_df, popsyn_regions)
    if base_only:
        return report

    new_scenario_file = new_pth / "scenario_files" / "model_scenarios.json"
    old_scenario_file = old_pth / "scenario_files" / "model_scenarios.json"

    new_scenarios = old_scenarios = []
    if new_scenario_file.exists():
        with new_scenario_file.open() as file_:
            new_scenarios = sorted(json.load(file_).keys())

    if old_scenario_file.exists():
        with old_scenario_file.open() as file_:
            old_scenarios = sorted(json.load(file_).keys())

    # Compare the tables for common scenarios
    new_rel_pth = new_sf1_pth.relative_to(new_pth)
    old_rel_pth = base_sf1_pth.relative_to(old_pth)
    for scenario_name in [x for x in new_scenarios if x in old_scenarios]:
        new_sf1_scen_pth = new_pth / "scenario_files" / scenario_name / new_rel_pth
        old_sf1_scen_pth = old_pth / "scenario_files" / scenario_name / old_rel_pth
        base_path = f"Scenario '{scenario_name}' population comparison"
        if new_sf1_scen_pth.exists() and old_sf1_scen_pth.exists():
            if not filecmp.cmp(old_sf1_scen_pth, new_sf1_scen_pth, shallow=False):
                base_sf1_df = pd.read_csv(old_sf1_scen_pth, sep="\t" if old_sf1_scen_pth.suffix == ".txt" else ",")
                new_sf1_df = pd.read_csv(new_sf1_scen_pth, sep="\t" if new_sf1_scen_pth.suffix == ".txt" else ",")
                report[base_path] = pop_comparison(base_sf1_df, new_sf1_df, popsyn_regions)
        elif int(new_sf1_scen_pth.exists()) + int(old_sf1_scen_pth.exists()) == 1:
            base_path = f"Scenario '{scenario_name}' population"
            report[base_path] = text_figure("No population in at least one branch. Can't compare it as such")
    return report
