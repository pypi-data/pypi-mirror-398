# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging
import os
from pathlib import Path
from typing import List, Any, Optional


from polaris.network.checker.checks.connection_table import CheckConnectionTable
from polaris.network.checker.checks.full_connectivity_auto import full_connectivity_auto
from polaris.utils.database.data_table_access import DataTableAccess
from polaris.utils.database.standard_database import DatabaseType
from polaris.utils.logging_utils import polaris_logging
from polaris.utils.model_checker import ModelChecker
from polaris.utils.optional_deps import check_dependency
from polaris.utils.signals import SIGNAL


class SupplyChecker(ModelChecker):
    """Network checker

    ::

        # We open the network
        from polaris.network.network import Network
        n = Network()
        n.open(source)

        # We get the checker for this network
        checker = n.checker

        # We can run the critical checks (those that would result in model crashing)
        checker.critical()

        # The auto network connectivity
        checker.connectivity_auto()

        # The connections table
        checker.connections_table()

    """

    checking = SIGNAL(object)

    def __init__(self, database_path: os.PathLike):
        ModelChecker.__init__(self, DatabaseType.Supply, Path(__file__).parent.absolute(), database_path)

        self._path_to_file = database_path
        self.__networks: Optional[Any] = None

        self.checks_completed = 0
        self.errors: List[Any] = []
        self._network_file = database_path
        self._test_list.extend(["connectivity_auto", "connections_table"])
        polaris_logging()

    def _other_critical_tests(self):
        self.connectivity_auto()
        # self.nodes_too_close()

    def connectivity_auto(self) -> None:
        """Checks auto network connectivity

        It computes paths between nodes in the network or between every single link/direction combination
        in the network
        """

        errors = full_connectivity_auto(self._path_to_file)
        if errors:
            self.errors.append(errors)
            logging.warning("There are locations in the auto network that are not fully connected")

    def nodes_too_close(self):
        if not check_dependency("geopandas", raise_error=False):
            logging.warning("Skipping nodes_too_close check, geopandas is not installed")
            return
        node = DataTableAccess(self._path_to_file).get("node")[["node", "geo"]]

        # Nodes cannot be closer than 0.1 meters from each toher, as that is MOST LIKELY an error in coding
        too_close = node.sjoin_nearest(
            node, distance_col="dist", max_distance=0.1, exclusive=True, lsuffix="1", rsuffix="2"
        )
        if not too_close.empty:
            logging.error("There are nodes that are too close to each other (less than 0.1 meters)")
            logging.error(too_close[["node_1", "node_2", "dist"]])
            self.errors.append(too_close[["node_1", "node_2", "dist"]])

    def connections_table(self, basic=True):
        """Includes
        * search for pockets that are not used in the connection table
        * search for pockets missing from the pockets table
        * search for lanes not connected to any other link at an intersection
        """

        checker = CheckConnectionTable(self._path_to_file)

        if basic:
            checker.lane_connection(False)
        else:
            checker.full_check()
        errors = checker.errors

        for key, val in errors.items():
            logging.error(key)
            logging.error(val)
