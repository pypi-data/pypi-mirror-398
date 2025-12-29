# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import os
from pathlib import Path

import pandas as pd

from polaris.utils.database.db_utils import read_and_close
from polaris.utils.database.standard_database import DatabaseType
from polaris.utils.logging_utils import polaris_logging
from polaris.utils.model_checker import ModelChecker
from polaris.utils.signals import SIGNAL


class FreightChecker(ModelChecker):
    """Freight checker

    ::

        # We open the network
        from polaris.freight import Freight
        n = Freight()
        n.open(source)

        # The freight database depends heavily on the supply database, so we need to
        # provide it for checking
        n.add_supply_database(supply_source)

        # We get the checker for this network
        checker = n.checker

        # We can run the critical checks (those that would result in model crashing)
        checker.critical()

    """

    checking = SIGNAL(object)

    def __init__(self, database_path: os.PathLike, supply_database_path: os.PathLike):
        ModelChecker.__init__(self, DatabaseType.Freight, Path(__file__).parent.absolute(), database_path)
        self._supply_file = supply_database_path
        self._path_to_file = database_path
        polaris_logging()

    def _other_critical_tests(self):
        self._airports_valid_locations()
        self._railports_valid_locations()
        self._international_ports_valid_locations()
        self._truck_poe_valid_county_and_locations()
        self.check_counties_populated()

    def check_location_fk(self, table_name):
        with read_and_close(self._path_to_file) as conn:
            locations = pd.read_sql(f"SELECT DISTINCT(location) FROM {table_name}", conn)
            if locations.empty:
                return []
        with read_and_close(self._supply_file) as conn:
            supply_locations = pd.read_sql("SELECT location from Location", conn)

        if locations[~locations.location.isin(supply_locations.location)].empty:
            return []

        return [f"Table {table_name} refers to locations that do not exist in the supply database"]

    def check_complete_truck_poe_set(self, table_name):
        with read_and_close(self._supply_file) as conn:
            internal_counties = pd.read_sql("SELECT county FROM Counties", conn)

        with read_and_close(self._path_to_file) as conn:
            all_counties = pd.read_sql("SELECT DISTINCT county_orig AS county FROM County_Skims", conn)
            external_counties = all_counties[~all_counties["county"].isin(internal_counties["county"])]
            poe_table = pd.read_sql(f"SELECT internal_county, external_county FROM {table_name}", conn)
            poes = set(poe_table.internal_county.astype(str) + "-" + poe_table.external_county.astype(str))

        # We expect a fully cross product of internals to externals
        expected_poes = {f"{i}-{e}" for i in internal_counties["county"] for e in external_counties["county"]}

        if expected_poes == poes:
            return []

        missing = expected_poes.difference(poes)
        extra = poes.difference(expected_poes)
        return [f"{table_name} table does not cover all counties (missing={len(missing)}, extra={len(extra)})"]


    def _airports_valid_locations(self):
        self.errors.extend(self.check_location_fk("Airport_Locations"))

    def _railports_valid_locations(self):
        self.errors.extend(self.check_location_fk("Railport_Locations"))

    def _international_ports_valid_locations(self):
        self.errors.extend(self.check_location_fk("International_Port_Locations"))

    def _truck_poe_valid_county_and_locations(self):
        self.errors.extend(self.check_location_fk("Truck_Poe"))
        self.errors.extend(self.check_complete_truck_poe_set("Truck_Poe"))


    def check_counties_populated(self):
        with read_and_close(self._supply_file) as conn:
            counties_loc = pd.read_sql("SELECT DISTINCT(county) FROM Location", conn)
            counties_gis = pd.read_sql("SELECT DISTINCT(county) FROM Counties", conn)

        if counties_loc.empty:
            self.errors.append("There is no county information attached to Locations")
        if counties_gis.empty:
            self.errors.append("The Counties table is not populated, it is required for freight analysis")
