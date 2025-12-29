# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from pathlib import Path
import re
from sqlite3 import Connection
from typing import NamedTuple

from polaris.network.starts_logging import logger
from polaris.utils.database.db_utils import has_table
from polaris.utils.database.standard_database import StandardDatabase, DatabaseType


def recreate_network_triggers(conn: Connection, current_version=None) -> None:
    from polaris.utils.database.migration_manager import MigrationManager as MM

    current_version = current_version or MM.find_last_applied_migration(conn)
    delete_triggers(StandardDatabase.for_type(DatabaseType.Supply), conn)
    create_triggers(StandardDatabase.for_type(DatabaseType.Supply), conn, current_version)


def recreate_freight_triggers(conn: Connection, current_version=None) -> None:
    from polaris.utils.database.migration_manager import MigrationManager as MM

    current_version = current_version or MM.find_last_applied_migration(conn)
    delete_triggers(StandardDatabase.for_type(DatabaseType.Freight), conn)
    create_triggers(StandardDatabase.for_type(DatabaseType.Freight), conn, current_version)


def create_network_triggers(conn: Connection, current_version=None) -> None:
    from polaris.utils.database.migration_manager import MigrationManager as MM

    current_version = current_version or MM.find_last_applied_migration(conn)
    create_triggers(StandardDatabase.for_type(DatabaseType.Supply), conn, current_version)


def create_triggers(db: StandardDatabase, conn: Connection, current_version: int) -> None:
    logger.info(f"  Creating triggers for version {current_version}")
    trigger_list_file = db.base_directory / "triggers/list_triggers.txt"
    if not trigger_list_file.exists():
        return

    with open(trigger_list_file) as f:
        trigger_list = [line.rstrip() for line in f.readlines()]

    for table in trigger_list:
        logger.debug(f"     creating triggers for {table}")
        qry_file = db.base_directory / "triggers" / f"{table}.sql"

        create_triggers_from_file(qry_file, conn, current_version)


def create_triggers_from_file(qry_file: Path, conn: Connection, current_version: int):
    with open(qry_file, "r") as sql_file:
        return create_triggers_from_str(sql_file.read(), conn, current_version)


def create_triggers_from_str(query_list: str, conn: Connection, current_version: int):
    triggers = split_triggers(query_list.split("\n"))

    # Running one query/command at a time helps debugging in the case a particular command fails
    for t in triggers:
        if current_version >= 0 and not (t.from_version <= current_version <= t.to_version):
            continue

        if not t.query:
            continue  # don't run empty queries

        if t.table_name and not has_table(conn, t.table_name):
            logger.error(f"Could not find table {t.table_name}. Skipping trigger creation {t.query=}")
            continue

        try:
            conn.execute(t.query)
        except Exception as e:
            logger.error(f"Failed adding triggers table - > {e.args}")
            logger.error(f"Point of failure - > {t.query}")
            raise e
    conn.commit()


sep_pattern = re.compile(r"--##.*")
from_pattern = re.compile(r"from_version:\s*(\d+)")
to_pattern = re.compile(r"to_version:\s*(\d+)")


class TriggerDef(NamedTuple):
    from_version: int
    to_version: int
    lines: list = []

    @staticmethod
    def from_separator(line: str):
        def f(pattern, default):
            ver = int(m.groups()[-1]) if (m := pattern.search(line)) else -1
            return ver if ver >= 0 else default

        return TriggerDef(f(from_pattern, 0), f(to_pattern, 99999999), [])

    @property
    def query(self):
        return "\n".join([e for e in self.lines if not e.startswith("--") and e != ""])

    @property
    def table_name(self):
        if "create trigger if not exists" not in self.lines[0].lower():
            return None

        return self.lines[0].split(" on ")[1]


def split_triggers(lines):
    groups = []
    cur = None
    for line in lines:
        line = line.strip()
        if not line or line == "--" or line.startswith("-- "):
            continue
        if sep_pattern.search(line):
            if cur:
                groups.append(cur)
            cur = TriggerDef.from_separator(line)
        else:
            if not cur:
                raise ValueError(f"Query line before separator: {line}")
            cur.lines.append(line)
    if cur:
        groups.append(cur)
    return groups


def delete_network_triggers(conn: Connection) -> None:
    delete_triggers(StandardDatabase.for_type(DatabaseType.Supply), conn)


def delete_triggers(db: StandardDatabase, conn: Connection) -> None:
    logger.info("  Deleting triggers")
    trigger_list_file = db.base_directory / "triggers/list_triggers.txt"
    if not trigger_list_file.exists():
        return
    with conn:
        with open(trigger_list_file) as f:
            trigger_list = [line.rstrip() for line in f.readlines()]
        for table in trigger_list:
            qry_file = db.base_directory / "triggers" / f"{table}.sql"

            with open(qry_file, "r") as sql_file:
                query_list = sql_file.read()

            # Running one query/command at a time helps debugging in the case a particular command fails
            for cmd in query_list.split("--##"):
                for qry in cmd.split("\n"):
                    if qry[:2] == "--":
                        continue
                    if "create trigger if not exists " in qry:
                        qry = qry.replace("create trigger if not exists ", "")
                        qry = "DROP trigger if exists " + qry.split(" ")[0]
                        try:
                            conn.execute(qry)
                        except Exception as e:
                            logger.error(f"Failed removing triggers table - > {e.args}")
                            logger.error(f"Point of failure - > {qry}")
