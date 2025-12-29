# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import filecmp
import json
import logging
import tempfile
from os import PathLike
from pathlib import Path
from typing import List, Union


from polaris.utils.testing.model_comparison.compare_tables import compare_tables
from polaris.utils.testing.model_comparison.get_csv_table import table_from_disk


def compare_table_dumps(old_path: Path, new_path: Path) -> List[str]:
    npath = Path(new_path)
    opath = Path(old_path)

    new_files = [x.stem for x in npath.glob("*.csv")] + [x.stem for x in npath.glob("*.parquet")]
    old_files = [x.stem for x in opath.glob("*.csv")] + [x.stem for x in opath.glob("*.parquet")]
    report = []

    dropped_files = [x for x in old_files if x not in new_files]
    if dropped_files:
        report.extend(["**Dropped tables**:\n", f"{', '.join(dropped_files)}\n"])
    else:
        report.append("**No dropped tables**\n")

    added_files = [x for x in new_files if x not in old_files]
    if added_files:
        report.extend(["**New tables**:\n", f"{', '.join(added_files)}\n"])
    else:
        report.append("**No new tables**\n")

    # Compares one table at a time
    no_change = []
    table_changes = []
    for table in new_files:
        if table not in old_files:
            continue
        logging.info(f"Comparing: {table}")
        old_table = table_path(opath, table)
        new_table = table_path(npath, table)
        table_report = []
        if not filecmp.cmp(old_table, new_table, shallow=False):
            table_report = compare_tables(table_from_disk(old_table), table_from_disk(new_table))

        if len(table_report):
            table_changes.append(f"\n * {table}:\n")
            table_changes.extend(table_report)
        else:
            no_change.append(table)

    if no_change:
        report.extend(["**Tables with no changes**:\n", f"{', '.join(no_change)}\n"])

    if table_changes:
        report.append("\n\n**Tables with changes**:")
        report.extend(table_changes)

    return report


def table_path(pth: Path, table_name: str):
    return pth / f"{table_name}.csv" if (pth / f"{table_name}.csv").exists() else pth / f"{table_name}.parquet"


def compare_tables_all_scenarios(old_path: Union[PathLike, Path], new_path: Union[PathLike, Path], db: str) -> List[
    str]:
    report = compare_table_dumps(Path(old_path) / db, Path(new_path) / db)

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
        report.append("\n\n**Model contains no additional scenario**:\n")
        return report

    # Check which scenarios were added or removed
    added = [x for x in new_scenarios if x not in old_scenarios]
    dropped = [x for x in old_scenarios if x not in new_scenarios]
    if added:
        report.extend(["**New scenarios**:\n", f"{', '.join(added)}\n"])
    if dropped:
        report.extend(["**Dropped scenarios**:\n", f"{', '.join(dropped)}\n"])
    if len(added) + len(dropped) == 0:
        report.extend(["\n\n**No scenario was added or removed**:\n", f"{', '.join(old_scenarios)}\n"])

    with tempfile.TemporaryDirectory() as temp_dir:
        # Compare the tables for added scenarios against empty folders
        for scenario_name in added:
            scen_table = Path(new_path) / "scenario_files" / scenario_name / db
            if not scen_table.exists():
                report.append(f"**Scenario added {scenario_name} does not have {db} tables**\n")
                continue
            # Since we added the scenario, we use the temp folder as the empty "old path"
            report.append(f"**Scenario added {scenario_name} has new {db}  tables**\n")
            report.extend(compare_table_dumps(Path(temp_dir), scen_table))

        # Compare the tables for dropped scenarios against empty folders
        for scenario_name in dropped:
            scen_table = Path(old_path) / "scenario_files" / scenario_name / db
            if not scen_table.exists():
                report.append(f"**Removed Scenario {scenario_name} did not have {db} tables**\n")
                continue
            # Since we removed the scenario, we use the temp folder as the empty "new path"
            report.extend(compare_table_dumps(scen_table, Path(temp_dir)))

        # Compare each of the scenarios that exist in both old and new paths
        for scenario_name in set(new_scenarios) & set(old_scenarios):
            report.append(f"**Scenario: {scenario_name}**:\n")

            new_scen_dir = Path(new_path) / "scenario_files" / scenario_name / db
            old_scen_dir = Path(old_path) / "scenario_files" / scenario_name / db

            if new_scen_dir.exists() and old_scen_dir.exists():
                report.extend(compare_table_dumps(old_scen_dir, new_scen_dir))
            elif new_scen_dir.exists():
                report.extend(compare_table_dumps(Path(temp_dir), new_scen_dir))
            elif old_scen_dir.exists():
                report.extend(compare_table_dumps(old_scen_dir, Path(temp_dir)))
            else:
                report.append(f"**No {db} tables for this scenario:**:\n")
    return report
