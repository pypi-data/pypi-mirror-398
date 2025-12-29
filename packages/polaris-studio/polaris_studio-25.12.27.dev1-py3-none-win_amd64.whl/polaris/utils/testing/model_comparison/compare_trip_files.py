# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import filecmp
import json
import logging
from pathlib import Path
from typing import Optional, Dict

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from polaris import Polaris
from polaris.analyze.demand_report import add_mode_names, vmts, time_distribution, trips_by_mode, trips_by_type
from polaris.analyze.demand_report import demand_report
from polaris.utils.database.data_table_access import DataTableAccess
from polaris.utils.plot_utils import text_figure
from polaris.utils.testing.model_comparison.get_csv_table import table_from_disk, geo_table_from_disk


def demand_comparison(trips_base: pd.DataFrame, trips_new: pd.DataFrame, locations: Optional[gpd.GeoDataFrame] = None):
    if min(trips_new.shape[0], trips_base.shape[0]) == 0:
        logging.error("One of the Trips dataframes is empty")
        return

    locs = gpd.GeoDataFrame([]) if locations is None else locations
    trips_base = add_mode_names(trips_base)
    trips_new = add_mode_names(trips_new)

    rows = 6
    fig, axs = plt.subplots(rows, 2, figsize=(20, rows * 6), sharey=False)

    # Compares trips by mode
    _ = trips_by_mode(trips_base, cname="Base", ax=axs[0, 0], ax_table=axs[1, 0])
    _ = trips_by_mode(trips_new, cname="New", ax=axs[0, 1], ax_table=axs[1, 1])

    # Compares VMTs
    cond1 = any(col not in trips_base.columns for col in ["euclidean", "manhatan"])
    cond2 = any(col not in trips_new.columns for col in ["euclidean", "manhatan"])
    if locations is None and cond1 and cond2:
        logging.error("VMT report is not possible without locations")
    else:
        _ = vmts(trips_base, locs, axs[2, 0], name=" (Base)")
        _ = vmts(trips_new, locs, axs[2, 1], name=" (NEW)")

    # Compares trips by type
    _ = trips_by_type(trips_base, cname="Base", ax=axs[3, 0], ax_table=axs[4, 0])
    _ = trips_by_type(trips_new, cname="New", ax=axs[3, 1], ax_table=axs[4, 1])

    # Compare time distributions
    _ = time_distribution(trips_base, field_name="Base", ax=axs[5, 0])
    _ = time_distribution(trips_new, field_name="New", ax=axs[5, 0])

    return fig


def get_demand_file(pth: Path) -> Path:
    files = [x for x in list(pth.glob("trip.*")) if x.suffix.lower() in [".zip", ".parquet", ".csv"]]
    if len(files) == 0:
        return (pth / "trip.zip")
    elif len(files) > 1:
        raise ValueError(f"More than one trip file found in {pth}: {files}")
    else:
        return files[0]


def get_locations(model_path: Path) -> gpd.GeoDataFrame:
    supply_file = Polaris.from_dir(model_path).supply_file
    if supply_file.exists():
        return DataTableAccess(supply_file).get("Location")
    else:
        return locations_from_dump(model_path / "supply")


def locations_from_dump(dump_path: Path) -> gpd.GeoDataFrame:
    if (dump_path / "location.parquet").exists():
        return geo_table_from_disk(dump_path / "location.parquet").reset_index()
    elif (dump_path / "location.csv").exists():
        return geo_table_from_disk(dump_path / "location.csv").reset_index()
    else:
        raise ValueError("No location file found in model supply folder.")


def compare_exogenous_trips(old_path: str, new_path: str, different_only=True, base_only=False) -> Dict[
    str, plt.Figure]:
    base_demand_path = get_demand_file(Path(old_path) / "demand")
    new_demand_path = get_demand_file(Path(new_path) / "demand")
    locations = gpd.GeoDataFrame([])
    report = {}
    if base_demand_path.exists() and new_demand_path.exists():
        if not filecmp.cmp(base_demand_path, new_demand_path, shallow=False) or not different_only:
            base_demand = table_from_disk(base_demand_path)
            new_demand = table_from_disk(new_demand_path)
            report["Base trips comparison"] = demand_comparison(base_demand, new_demand)

            # Create report of the newest demand data
            locations = get_locations(Path(new_path))
            report["New base trips full analysis"] = demand_report(trips=new_demand, locations=locations)
    elif base_demand_path.exists():
        report["New base trips full analysis"] = text_figure("Exogenous trip file was deleted from new model.")
    elif new_demand_path.exists():
        # Create report of the newest demand data
        new_demand = table_from_disk(new_demand_path)
        locations = get_locations(Path(new_path))
        report["New base trips full analysis"] = demand_report(trips=new_demand, locations=locations)

    if base_only:
        return report

    new_scenario_file = Path(new_path) / "scenario_files" / "model_scenarios.json"
    old_scenario_file = Path(old_path) / "scenario_files" / "model_scenarios.json"

    new_scenarios = old_scenarios = []
    if new_scenario_file.exists():
        with new_scenario_file.open() as file_:
            new_scenarios = sorted(json.load(file_).keys())

    if old_scenario_file.exists():
        with old_scenario_file.open() as file_:
            old_scenarios = sorted(json.load(file_).keys())

    if not new_scenarios and not old_scenarios:
        return report

    # Compare the tables for common scenarios
    full_report_required = []
    for scen_name in [x for x in new_scenarios if x in old_scenarios]:
        new_scen_pth = Path(new_path) / "scenario_files" / scen_name / "demand"
        old_scen_pth = Path(old_path) / "scenario_files" / scen_name / "demand"

        if new_scen_pth.exists() or old_scen_pth.exists():
            old_scen_pth = get_demand_file(old_scen_pth)
            new_scen_pth = get_demand_file(new_scen_pth)
            if not filecmp.cmp(old_scen_pth, new_scen_pth, shallow=False) or not different_only:
                base_demand = table_from_disk(old_scen_pth)
                new_demand = table_from_disk(new_scen_pth)
                report[f"Trips comparison for scenario {scen_name}"] = demand_comparison(base_demand, new_demand)
                full_report_required.append(scen_name)
        elif old_scen_pth.exists():
            report[f"trips {scen_name}"] = text_figure(f"Exogenous trip file was deleted from scenario {scen_name}.")
        elif new_scen_pth.exists():
            full_report_required.append(scen_name)

    # Checks if there are demand files for new scenarios
    for scen_name in [x for x in new_scenarios if x not in old_scenarios]:
        if get_demand_file(Path(new_path) / "scenario_files" / scen_name / "demand").exists():
            full_report_required.append(scen_name)

    # Create demand reports for new scenarios
    for scen_name in full_report_required:
        new_scen_pth = get_demand_file(Path(new_path) / "scenario_files" / scen_name / "demand")
        new_demand = table_from_disk(new_scen_pth)
        if locations.empty:
            locations = get_locations(Path(new_path))
        fig = demand_report(trips=new_demand, locations=locations)
        fig.suptitle(f"Exogenous trips for {scen_name}")
        report[f"trips {scen_name}"] = fig
    return report
