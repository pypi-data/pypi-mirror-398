# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging
import os
from pathlib import Path
from typing import Optional

from polaris.freight.checker.freight_checker import FreightChecker
from polaris.utils.database.data_table_access import DataTableAccess
from polaris.utils.database.database_loader import GeoInfo
from polaris.utils.database.db_utils import commit_and_close


class Freight:
    """Polaris Freight Class"""

    def __init__(self, db_path: os.PathLike, supply_path: Optional[os.PathLike] = None):
        """Instantiates the object"""
        if not Path(db_path).exists():
            raise FileNotFoundError
        self.path_to_file = db_path
        self._supply_db_path = Path(supply_path) or Path(str(db_path).replace("-Freight.sqlite", "-Supply.sqlite"))
        if not self._supply_db_path.exists():
            logging.warning("   Set supply path using 'add_supply_database' to use the checker property")

    @staticmethod
    def from_file(db_path: os.PathLike):
        return Freight(db_path)

    def add_supply_database(self, supply_db_path: Path):
        """Adds supply database path to the freight object for checking purposes"""
        if not Path(supply_db_path).exists():
            raise FileNotFoundError
        self._supply_db_path = Path(supply_db_path).resolve()

    def connect(self):
        return commit_and_close(self.path_to_file)

    @staticmethod
    def create(db_path: str, srid: int) -> None:
        """Creates new empty freight file. Fails if file exists
        Args:
            *db_path* (:obj:`str`): Full path to the freight file to be created.
        """
        from polaris.utils.database.standard_database import StandardDatabase, DatabaseType

        if os.path.isfile(db_path):
            raise FileExistsError

        geo_info = GeoInfo.from_fixed(srid)
        StandardDatabase.for_type(DatabaseType.Freight).create_db(db_path, geo_info, add_defaults=True)

    @property
    def tables(self) -> DataTableAccess:
        if not self.__checks_valid():
            raise Exception("Not a valid network")
        return DataTableAccess(self.path_to_file)

    def upgrade(self) -> None:
        """Updates the network to the latest version available"""
        from polaris.utils.database.migration_manager import MigrationManager
        from polaris.utils.database.standard_database import DatabaseType

        MigrationManager.upgrade(self.path_to_file, DatabaseType.Freight, redo_triggers=False)

    @property
    def checker(self) -> FreightChecker:
        if not self._supply_db_path.exists():
            logging.error("   Set supply path using 'add_supply_database' to use the checker property")
            raise FileNotFoundError(self._supply_db_path)
        return FreightChecker(self.path_to_file, self._supply_db_path)

    def __checks_valid(self) -> bool:
        if not os.path.isfile(self.path_to_file):
            logging.error("You don't have a valid project open. Fix that and try again")
            return False
        return True
