# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from pathlib import Path
from typing import List

from polaris.network.create.triggers import recreate_network_triggers
from polaris.network.starts_logging import logger
from polaris.utils.database.db_utils import commit_and_close
from polaris.utils.database.migration import Migration, migration_file_pattern
from polaris.utils.database.standard_database import DatabaseType, StandardDatabase
from polaris.utils.logging_utils import function_logging


class MigrationManager:
    @staticmethod
    @function_logging("Upgrading {db_type} database at location {db_path}")
    def upgrade(db_path: Path, db_type: DatabaseType, redo_triggers, max_migration=None, force_migrations=None):
        MM = MigrationManager
        migrations_dir = MM.migration_sql_dir(db_type)
        with commit_and_close(db_path, spatial=False) as conn:
            StandardDatabase.ensure_required_tables(conn)
            applicable_migrations = MM.find_applicable_migrations(conn, migrations_dir, max_migration, force_migrations)
            if not applicable_migrations:
                logger.info("No migrations to apply")
                return

        MM.apply_migrations(db_path, applicable_migrations)

        # Triggers are only available on Supply networks at the moment
        redo_triggers = redo_triggers or (db_type == DatabaseType.Supply)
        if redo_triggers and db_type == DatabaseType.Supply:
            with commit_and_close(db_path) as conn:
                recreate_network_triggers(conn)

    @staticmethod
    def apply_all_migrations(db_path, migrations_dir, max_migration=None, force_migrations=None):
        with commit_and_close(db_path, spatial=False) as conn:
            StandardDatabase.ensure_required_tables(conn)
            applicable_migrations = MigrationManager.find_applicable_migrations(
                conn, migrations_dir, max_migration, force_migrations
            )
        MigrationManager.apply_migrations(db_path, applicable_migrations)

    @staticmethod
    def apply_migrations(db_path: Path, applicable_migrations: List[Migration]):
        for m in applicable_migrations:
            m.run(db_path)

    @staticmethod
    def find_applied_migrations(conn):
        return [e[0] for e in conn.execute("SELECT migration_id from Migrations").fetchall()]

    @staticmethod
    def find_last_applied_migration(conn) -> int:
        result = conn.execute("SELECT MAX(migration_id) from Migrations").fetchone()
        return int(result[0]) if result and result[0] else 99999999

    @staticmethod
    def find_available_migrations(migrations_dir):
        files = [s for s in migrations_dir.glob("*") if s.is_file() and migration_file_pattern.match(s.name)]
        return sorted([Migration.from_file(f) for f in files])

    @staticmethod
    def find_applicable_migrations(conn, migrations_dir, max_migration=None, force_migrations=None):
        def in_range(x):
            return max_migration is None or x.migration_id <= max_migration

        applied = MigrationManager.find_applied_migrations(conn)
        available = MigrationManager.find_available_migrations(migrations_dir)
        force_migrations = force_migrations or []

        def should_apply(m):
            return m.migration_id in force_migrations or (m.migration_id not in applied and in_range(m))

        return [m for m in available if should_apply(m)]

    @staticmethod
    def migration_sql_dir(db_type):
        dir = Path(__file__).parent.parent.parent
        if db_type == DatabaseType.Supply:
            dir = dir / "network"
        elif db_type == DatabaseType.Demand:
            dir = dir / "demand"
        elif db_type == DatabaseType.Freight:
            dir = dir / "freight"
        else:
            raise RuntimeError(f"Unknown db type: {db_type}")
        return dir / "database" / "migrations"
