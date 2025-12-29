# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

from polaris import Polaris
from polaris.utils.checker_utils import check_critical
from polaris.utils.path_utils import tempdirpath


def critical_network_tests(city: str, model_text_folder: str, model_dir=None, scenario_name=None, upgrade=False):
    model_dir = model_dir or tempdirpath() / uuid4().hex
    shutil.copytree(model_text_folder, model_dir, dirs_exist_ok=True)

    pol = Polaris.restore(model_dir, city, scenario_name=scenario_name, upgrade=upgrade)

    if len(check_critical(pol, False)) > 0:
        raise RuntimeError("There are critical errors in the model. Please fix them before proceeding.")


def build_and_check_all_scenarios(city: str, model_text_folder: str, model_dir: Path, upgrade=False):
    out_pth = Path(model_dir)
    out_pth.mkdir(parents=True, exist_ok=True)

    # Build the base model
    critical_network_tests(city, model_text_folder, model_dir=out_pth / "base", upgrade=upgrade)

    scenario_file = Path(model_text_folder) / "scenario_files" / "model_scenarios.json"
    if not scenario_file.exists():
        print(f"NO MULTIPLE scenarios for {city}. Built base only")
        return

    with scenario_file.open() as file_:
        configs = json.load(file_)
    for scenario_name in configs.keys():
        critical_network_tests(city, model_text_folder, model_dir=out_pth / scenario_name, scenario_name=scenario_name)


if __name__ == "__main__":
    # critical_network_tests(sys.argv[1], sys.argv[2])
    build_and_check_all_scenarios(sys.argv[1], sys.argv[2], tempdirpath() / uuid4().hex)
