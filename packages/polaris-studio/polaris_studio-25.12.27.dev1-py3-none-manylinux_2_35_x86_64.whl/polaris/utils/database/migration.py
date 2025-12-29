# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import inspect
import logging
import re
from functools import total_ordering
from importlib.util import spec_from_file_location, module_from_spec
from os.path import exists
from pathlib import Path

from polaris.utils.database.db_utils import commit_and_close, run_sql_file
from polaris.utils.logging_utils import function_logging
from polaris.utils.str_utils import outdent

migration_file_pattern = re.compile(r"^([0-9]+(_[0-9\.]+)?)(-.*)?\.(py|sql)$")


@total_ordering
class Migration:
    def __init__(self, migration_id, description, type, file: Path):
        self.migration_id = migration_id
        self.description = description
        self.type = type
        self.file = file

    def __eq__(self, other):
        return self.migration_id == other.migration_id

    def __lt__(self, other):
        return self.migration_id < other.migration_id

    def __hash__(self):
        return int(self.migration_id)

    def __repr__(self):
        return f"Migration({self.migration_id} - {self.description})"

    @classmethod
    def from_file(cls, file: Path):
        if not exists(file):
            raise RuntimeError(f"No such migration: {file}")
        match = migration_file_pattern.match(file.name)
        if not match:
            raise RuntimeError(f"Not a validly named migration file: {file.name}")
        descr = match[3][1:] if match[3] else None  # drop the leading '-' that will be matched by the regex
        return cls(match[1], descr, match[4], file)

    @classmethod
    def from_id(cls, migration_id, migrations_dir: Path):
        files = [s for s in migrations_dir.glob("*") if s.is_file() and s.name.startswith(migration_id)]
        if len(files) == 1:
            return cls.from_file(files[0])
        msg = f"Can't find migration definition file for {migration_id} in {migrations_dir}: possibilities are {files}"
        raise FileNotFoundError(msg)

    @function_logging("Running migration {self.migration_id}: {self.description}", level=logging.DEBUG)
    def run(self, db_path):
        if self.file.name.endswith(".sql"):
            with commit_and_close(db_path, spatial=True) as conn:
                run_sql_file(self.file, conn)
        elif self.file.name.endswith(".py"):
            Migration._run_py(self.file, db_path)
        else:
            raise RuntimeError(f"Unsupported migration type for file {self.file}")

        with commit_and_close(db_path, spatial=False) as conn:
            description = "NULL" if self.description is None else f"'{self.description}'"
            sql = f"""
                INSERT INTO Migrations VALUES ('{self.migration_id}', {description}, DATETIME('now'))
                ON CONFLICT(migration_id) DO UPDATE SET applied_at=DATETIME('now');"""
            conn.execute(outdent(sql))

    @staticmethod
    def _run_py(migration_file, path_to_file):
        spec = spec_from_file_location(Path(migration_file).stem, migration_file)
        if spec is None:
            return
        loaded_module = module_from_spec(spec)
        spec.loader.exec_module(loaded_module)
        args = tuple(inspect.signature(loaded_module.migrate).parameters.keys())
        if "path_to_file" in args:
            return loaded_module.migrate(path_to_file)
        elif "conn" in args:
            with commit_and_close(path_to_file, spatial=True) as conn:
                return loaded_module.migrate(conn)
        raise RuntimeError(f"Migration {migration_file} has an invalid function signature: migrate({args})")
