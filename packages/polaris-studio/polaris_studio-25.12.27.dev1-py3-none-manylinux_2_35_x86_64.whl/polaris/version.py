# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
# from datetime import datetime, date
from datetime import date
import logging
import subprocess
from pathlib import Path

try:
    git_sha = str(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(Path(__file__).parent.parent)))
except:  # noqa: E722
    recorded = Path(__file__).parent / "sha.txt"
    if recorded.exists():
        with open(recorded, "r") as f:
            git_sha = recorded.read_text().strip()
    else:
        git_sha = "NO GIT SHA FOUND"
        logging.error("NO GIT SHA FOUND")

today = date.today()
__version__ = '25.12.27.dev1'