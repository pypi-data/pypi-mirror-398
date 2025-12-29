# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from os import PathLike
from pathlib import Path
from typing import List, Union

from polaris.utils.testing.model_comparison.compare_table_sets import compare_tables_all_scenarios, compare_table_dumps


def compare_supply_tables(old_path: Union[PathLike, Path], new_path: Union[PathLike, Path], base_only=False) -> List[
    str]:
    if base_only:
        return compare_table_dumps(Path(old_path) / "supply", Path(new_path) / "supply")
    else:
        return compare_tables_all_scenarios(old_path, new_path, "supply")


def compare_freight_tables(old_path: Union[PathLike, Path], new_path: Union[PathLike, Path], base_only=False) -> List[
    str]:
    if base_only:
        return compare_table_dumps(Path(old_path) / "freight", Path(new_path) / "freight")
    else:
        return compare_tables_all_scenarios(old_path, new_path, "freight")
