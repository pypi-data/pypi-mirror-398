# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from pathlib import Path
import tempfile


def tempdirpath() -> Path:
    return Path(tempfile.gettempdir())


def resolve_relative(path: Path, relative_to: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else (relative_to / path).resolve()
