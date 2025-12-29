# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging
import warnings
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import pandas as pd

from polaris.network.consistency.consistency import Consistency
from polaris.network.open_data.opendata import OpenData
from polaris.network.utils.srid import get_srid, get_table_srid
from polaris.prepare.supply_tables.ev_chargers.ev_charging import ev_chargers
from polaris.prepare.supply_tables.network.net_constructor import NetworkConstructor
from polaris.prepare.supply_tables.utils.state_county_candidates import get_state_counties, counties_for_model
from polaris.prepare.supply_tables.zones.popsyn import add_popsyn_regions
from polaris.prepare.supply_tables.zones.zoning import add_zoning
from polaris.utils.database.data_table_access import DataTableAccess
from polaris.utils.database.db_utils import commit_and_close, count_table
from polaris.utils.user_configs import UserConfig


class Populator:
    def __init__(self, supply_path) -> None:
        self.supply_path = supply_path
        self._state_counties = gpd.GeoDataFrame()

    def add_zoning_system(
        self, model_area: gpd.GeoDataFrame, zone_level: str, census_api_key: Optional[str] = None, year: int = 2021
    ):
        """Create zoning system based on census subdivisions. Population data is extracted from The ACS 5 year. For
        mode details see https://github.com/datamade/census

        Args:
            model_area (GeoDataFrame): GeoDataFrame containing polygons with the model area
            zone_level (str): Census subdivision level to use for zoning -> tracts or block_groups
            year (int): Year of the population data. Defaults to 2021
            census_api_key (`Optional`: str): API key for the census. If not provided we will attempt to retrieve from
            the user configuration file.
        """

        assert zone_level in ["tracts", "block_groups"]

        key = census_api_key or UserConfig().census_api
        if not key:
            raise ValueError("No Census API found. Please obtain one at https://api.census.gov/data/key_signup.html")
        warnings.warn(key)
        self._state_counties = get_state_counties(model_area, year=year)
        add_zoning(model_area, self.state_counties(year), zone_level, self.supply_path, year, key)

    def add_popsyn_regions(self, model_area: gpd.GeoDataFrame, census_type: str, year: int = 2021, replace=False):
        """Populate the Population Synthesis Region geography table based on census subdivisions.

        Args:
            model_area (GeoDataFrame): GeoDataFrame containing polygons with the model area
            census_type (str): Census subdivision level to import -> tracts or block_groups
            year (int): Year of the population data. Defaults to 2021
        """

        assert census_type in ["tracts", "block_groups"]

        self._state_counties = get_state_counties(model_area, year=year)
        add_popsyn_regions(model_area, self.state_counties(year), census_type, self.supply_path, year, replace)

    def add_school_locations(self, enrolments: Union[Path, gpd.GeoDataFrame]):
        """Populate schools into Locations and Location_Attributes from a parquet file or GeoDataFrame

        Args:
            enrolments_file (Path): Path to a parquet file containing school locations and enrolments
        """

        if isinstance(enrolments, (Path, str)):
            logging.info(f"Adding school locations from {enrolments}")
            enrolments = gpd.read_parquet(enrolments)
        elif not isinstance(enrolments, gpd.GeoDataFrame):
            raise ValueError("enrolments must be a file path or a GeoDataFrame")
        assert "enrolments" in enrolments.columns, "enrolments column not found in input"
        assert "school_type" in enrolments.columns, "school_type column not found in input"

        srid = get_srid(database_path=self.supply_path)

        data_tables = DataTableAccess(self.supply_path)

        # Find Overture POI childcare locations to complement the institutional pre-K locations
        # add these with average enrolment based on the institutional locations across the whole country
        zones = data_tables.get("zone")[["zone", "geo"]]

        prek_places = OpenData(self.supply_path).get_pois(["EDUCATION_PREK"])
        mean_num_prek = enrolments.loc[enrolments["school_type"] == "num_prek", "enrolments"].mean().round()
        logging.info(
            f"Found {prek_places.shape[0]} childcare centres from Overture maps POI, adding these with "
            f"an average enrolment of {mean_num_prek} students"
        )
        prek_locs = prek_places[["geometry"]].assign(enrolments=mean_num_prek, school_type="num_prek").to_crs(zones.crs)
        enrolments = gpd.GeoDataFrame(pd.concat([enrolments.to_crs(prek_locs.crs), prek_locs], ignore_index=True))

        assert enrolments.crs == zones.crs, "CRS of education locations must match the model zones"
        enrolments = gpd.sjoin(enrolments, zones, how="left", predicate="within").drop(columns=["index_right"])
        national_count = enrolments.shape[0]
        enrolments = enrolments.loc[~enrolments.zone.isna()]
        enrolments["zone"] = enrolments["zone"].astype("int")  # zone is float after spatial join
        model_count = enrolments.shape[0]
        logging.info(f"{model_count} out of {national_count} nation-wide education locations are in model area")

        assert (enrolments["enrolments"] > 0).all()

        school_type_map = {
            "num_prek": "EDUCATION_PREK",
            "num_k_8": "EDUCATION_K_8",
            "num_9_12": "EDUCATION_9_12",
            "tertiary": "HIGHER_EDUCATION",
        }
        enrolments["school_type"] = enrolments["school_type"].map(school_type_map)

        next_location_id = data_tables.get("location", from_cache_ok=False)["location"].max() + 1
        new_location_ids = pd.RangeIndex(next_location_id, next_location_id + enrolments.shape[0])

        enrolments = enrolments.assign(loc_id=new_location_ids, geo_wkb=enrolments.geometry.to_wkb(), srid=srid)

        # Attach closest link information
        links = data_tables.get("Link")[["link", "geo"]]
        if links.empty:
            enrolments = enrolments.assign(link=-1)
        else:
            enrolments = enrolments.sjoin_nearest(links, how="left")
            enrolments = enrolments.drop_duplicates(subset="loc_id").drop(columns=["index_right"])

        # Get the relevant columns and prepare for import to the database
        loc_attributes = enrolments[["loc_id", "enrolments"]]
        enrolments = enrolments[["loc_id", "school_type", "link", "zone", "geo_wkb", "srid"]]

        with commit_and_close(self.supply_path, spatial=True) as conn:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("PRAGMA ignore_check_constraints=1")

            # Remove any existing education locations and remove the landuse category from the landuse table
            conn.execute("DELETE FROM Location where land_use = ?", ("EDUCATION",))
            conn.execute("DELETE FROM Location_Attributes where location not in (SELECT location from Location);")
            conn.execute("DELETE FROM Land_Use where land_use = ?", ("EDUCATION",))

            # Make sure we have zero enrolments for all non-school locations
            if count_table(conn, "location_attributes") == 0:
                logging.info("Inserting blank enrolment data for all non-school locations")
                conn.execute("INSERT INTO Location_Attributes SELECT location, 0 as enrolments FROM Location;")

            logging.info(f"Inserting {enrolments.shape[0]} new education locations")
            conn.executemany(
                "INSERT INTO Location (location, land_use, link, zone, geo) VALUES (?, ?, ?, ?, GeomFromWKB(?, ?))",
                enrolments.to_records(index=False),
            )

            logging.info(f"Inserting enrolment data for {loc_attributes.shape[0]} school locations")
            conn.executemany(
                "INSERT INTO Location_Attributes (location, enrolments) VALUES (?, ?)",
                loc_attributes.to_records(index=False),
            )

        logging.info("Running consistency checks on the supply database")
        Consistency(self.supply_path).enforce()  # update location links, parking, etc. Takes about 5 minutes to run.

    def add_counties(self, year=2022):
        logging.warning(
            f"You have imported counties for {year}. Make sure the data is consistent with the data used for the freight model component"
        )

        model_area = DataTableAccess(self.supply_path).get("Zone")

        counties = counties_for_model(model_area, year).to_crs(model_area.crs)
        if counties.empty:
            logging.error("No counties found for the model area")
            return
        counties["county"] = counties["GEOID"].astype(int)

        sql = (
            'Insert into Counties("county", "x", "y", "name", "statefp", "state", "geo")'
            + "VALUES(?, ?, ?, ?, ?, ?, CastToMulti(GeomFromText(?, ?)))"
        )

        with commit_and_close(self.supply_path, spatial=True) as conn:
            assert sum(conn.execute("SELECT count(*) from Counties").fetchone()) == 0

            srid = get_table_srid(conn, "zone")
            counties = counties.to_crs(srid)
            counties = counties.assign(
                x=counties.geometry.centroid.x,
                y=counties.geometry.centroid.y,
                geo_wkt=counties.geometry.to_wkt(rounding_precision=6),
                srid=srid,
            )

            data = counties[["county", "x", "y", "name", "statefp", "state", "geo_wkt", "srid"]].to_records(index=False)
            conn.executemany(sql, data)

    def add_ev_chargers(self, nrel_api_key: Optional[str] = None, max_dist=100, clustering_attempts=5):
        """Adds EV Chargers

        Args:
            nrel_api_key (str): API key for the NREL API to retrieve location of EV chargers. If not provided it will be
            read from the user configuration file.
            max_dist (float):
            clustering_attempts (int):
        """
        key = nrel_api_key or UserConfig().nrel_api

        if not key:
            raise ValueError("No NREL API key provided. Please obtain one at https://developer.nrel.gov/signup/")

        assert max_dist > 0, "Minimum clustering must be non-negative. Use 0.1 if you must. That's in meters"

        model_area = DataTableAccess(self.supply_path).get("Zone")
        ev_chargers(model_area, self.supply_path, key, max_dist, clustering_attempts)

    def add_parking(self, sample_rate: float = 1.0):
        """Adds Parking facilities from data coming from Overture maps

        Args:
           sample_rate (str): Share of parking facilities to import. Defaults to 1.0 (all facilities)
        """
        from polaris.prepare.supply_tables.park.parking import add_parking

        add_parking(self.supply_path, sample_rate)

    def add_locations(
        self,
        census_api_key: Optional[str] = None,
        residential_sample_rate=0.05,
        other_sample_rate=1.0,
    ):
        from polaris.prepare.supply_tables.locations.locations import add_locations

        key = census_api_key or UserConfig().census_api
        if not key:
            raise ValueError("No Census API found. Please obtain one at https://api.census.gov/data/key_signup.html")

        add_locations(
            supply_path=self.supply_path,
            state_counties=self.state_counties(),
            census_api_key=key,
            residential_sample_rate=residential_sample_rate,
            other_sample_rate=other_sample_rate,
        )

    def create_network(
        self,
        simplification_parameters={  # noqa: B006
            "simplify": True,
            "keep_transit_links": True,
            "accessibility_level": "zone",
            "maximum_network_capacity": False,
        },
        imputation_parameters={"algorithm": "knn", "max_iter": 10},  # noqa: B006
        year: int = 2021,
    ) -> NetworkConstructor:
        """ """
        if self._state_counties.empty:
            self._state_counties = get_state_counties(DataTableAccess(self.supply_path).get("Zone"), year)

        return NetworkConstructor(
            polaris_network_path=self.supply_path,
            simplification_parameters=simplification_parameters,
            imputation_parameters=imputation_parameters,
            state_counties=self._state_counties,
        )

    def state_counties(self, year: int = 2021):
        if self._state_counties.empty:
            model_area = DataTableAccess(self.supply_path).get("Zone")
            self._state_counties = get_state_counties(model_area, year=year)
        return self._state_counties
