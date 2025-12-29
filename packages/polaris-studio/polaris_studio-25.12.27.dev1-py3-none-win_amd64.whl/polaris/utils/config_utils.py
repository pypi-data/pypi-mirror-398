# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import json
import re
from pathlib import Path
from typing import Optional

import yaml

from polaris.utils.dict_utils import denest_dict_recursive


def from_file(model_cls, file):
    file = Path(file)
    if file.suffix.lower() in [".yaml", ".yml", ".conf"]:
        return from_yaml_file(model_cls, file)
    if file.suffix.lower() in [".json", ".jsn"]:
        return from_json_file(model_cls, file)
    raise NotImplementedError(f"Don't know how to handle file {file}")


def from_json_file(model_cls, file):
    with open(file, "r") as f:
        return model_cls(**json.loads(f.read()))


def from_yaml_file(model_cls, file):
    with open(file, "r") as f:
        return model_cls(**yaml.load(f, Loader=yaml.FullLoader))


def from_dict(model_cls, dict):
    return model_cls(**dict)


def find_sf1(model_path: Path, model_config: Path) -> Optional[Path]:
    model_config = model_config if model_config.exists() and model_config.is_file() else model_path / model_config
    print(model_config)
    with open(model_config, "r") as fl:
        configs = denest_dict_recursive(json.load(fl))

    linker_file = model_path / configs.get("popsyn_control_file", "NOT.FOUND")

    if not linker_file.exists():
        return None
    pattern = re.compile(r'^\s*ZONEFILE\b', re.IGNORECASE)
    with open(linker_file, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if pattern.match(line):
                # remove leading key, then strip inline comments and whitespace
                rest = re.sub(r'^\s*ZONEFILE\b', '', line, flags=re.IGNORECASE).strip()
                # drop anything after a # (inline comment)
                rest = re.split(r'\s+#', rest, maxsplit=1)[0].strip()
                return model_path / rest if rest else None
    return None
