# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging
import sqlite3
from importlib import util as iutil
from os import PathLike
from typing import Dict

import pandas as pd

from polaris.utils.database.db_utils import read_and_close
from polaris.utils.logging_utils import polaris_logging
from polaris.utils.structure_finder import find_table_fields, find_table_index


class DataTableAccess:
    def __init__(self, database_file: PathLike):
        polaris_logging()
        self.__data_tables: Dict[str, pd.DataFrame] = {}
        self.__table_indices: Dict[str, pd.DataFrame] = {}
        self._database_file = database_file

    # def get_table(self, table_name: str, conn=None):  # type: ignore

    def get(self, table_name: str, conn=None, from_cache_ok=False, filter=""):  # type: ignore
        """Returns a pandas dataframe for a project table. For geo-enabled tables, it returns a Pandas GeoDataFrame

        It always caches tables for repeated access by setting *from_cache_ok*=True.

        Args:
            *table_name* (:obj:`str`): Network table name
            *conn* `Optional` (:obj:`sqlite3.Connection`): Connection to the network database
            *from_cache_ok* `Optional` (:obj:`Bool`): Returns cached dataframe if available
            *filter* `Optional` (:obj:`str`): SQL filter to apply when reading the data
        Return:
            *dataframe* (:obj:`pd.DataFrame`): Corresponding to the database
        """
        from_cache_ok = from_cache_ok and len(filter) == 0  # disable cache when filtering

        tn = table_name.lower()
        if tn not in self.__data_tables or not from_cache_ok:
            with conn or read_and_close(self._database_file, spatial=True) as connec:
                df = self.__build_layer(table_name, connec, filter)
                if len(filter) == 0:
                    self.__data_tables[tn] = df
                return df
        else:
            return self.__data_tables[tn]

    def table_index(self, table_name: str, conn=None):
        if table_name not in self.__table_indices:
            with conn or read_and_close(self._database_file, spatial=True) as connec:
                self.__table_indices[table_name] = find_table_index(connec, table_name)
        return self.__table_indices[table_name]

    def __build_layer(self, table_name: str, conn: sqlite3.Connection, filter: str):
        with conn or read_and_close(self._database_file, spatial=True) as conn:
            fields, _, geo_field = find_table_fields(conn, table_name)
            if geo_field is not None and iutil.find_spec("geopandas") is None:
                logging.warning("Geopandas is not installed. Returning a Pandas DataFrame instead of a GeoDataFrame.")
            if geo_field is None or iutil.find_spec("geopandas") is None:
                return pd.read_sql(f"SELECT * FROM '{table_name}' {clean_filter_df(filter)}", conn)
            return self.__geo_table_builder(table_name, conn, filter)

    def __geo_table_builder(self, table_name: str, conn: sqlite3.Connection, filter=""):
        from polaris.utils.gpd_utils import read_spatialite_layer

        return read_spatialite_layer(table_name, conn, filter=filter)

    def refresh_cache(self, table_name="") -> None:
        """Refreshes a table in memory. Necessary when a table has been edited in disk

        Args:
           *table_name* (:obj:`str`) Name of the table to be refreshed in memory. Defaults to '', which refreshes
           all tables
        """
        if table_name == "":
            self.__data_tables.clear()
        else:
            _ = self.__data_tables.pop(table_name.lower(), None)


def clean_filter_df(filter: str) -> str:
    if filter.strip() == "":
        return ""
    if not filter.lower().strip().startswith("where"):
        return f"WHERE {filter}"
    return filter.strip()
