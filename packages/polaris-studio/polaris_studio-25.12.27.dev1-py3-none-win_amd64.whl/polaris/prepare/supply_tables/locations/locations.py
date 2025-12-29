# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging
import sqlite3
from pathlib import Path
import math
import geopandas as gpd
import numpy as np
import pandas as pd
import pygris
from census import Census
from polaris.network.open_data.opendata import OpenData

from polaris.utils.database.data_table_access import DataTableAccess
from polaris.network.utils.srid import get_srid, get_table_srid
from polaris.network.network import Network
from polaris.utils.database.db_utils import commit_and_close, read_and_close
from polaris.utils.signals import SIGNAL


def add_locations(
    supply_path: Path,
    state_counties: gpd.GeoDataFrame,
    census_api_key: str,
    residential_sample_rate=0.25,
    other_sample_rate=1.0,
) -> None:
    """ """
    # Support data
    net = Network.from_file(supply_path, False)
    zone_layer = DataTableAccess(supply_path).get("Zone")

    # Retrieves OVM data
    open_data = OpenData(supply_path)

    if other_sample_rate > 0:
        # builds activity locations
        pois = open_data.get_pois()
        activities = pois[~pois.code_level2.isin(["RESIDENTIAL-SINGLE", "RESIDENTIAL-MULTI", "RES"])]
        activities = activities[~activities.code_level2.isna()]
        add_commercial(net, zone_layer, other_sample_rate, activities)

    if residential_sample_rate > 0:
        # Builds residential locations
        buildings = open_data.get_buildings()
        buildings.reset_index(drop=True, inplace=True)

        # We can now use these buildings to add residential and commercial locations
        add_residential(net, state_counties, zone_layer, residential_sample_rate, buildings, census_api_key)

    net.close(False)


def add_residential(
    net: Network,
    state_counties: gpd.GeoDataFrame,
    zone_layer: gpd.GeoDataFrame,
    residential_sample_rate: float,
    all_buildings: gpd.GeoDataFrame,
    census_api_key: str,
) -> gpd.GeoDataFrame:
    logging.info("pre-processing residential locations")
    with read_and_close(net.path_to_file) as conn:
        max_loc = conn.execute("Select coalesce(max(location) + 1, 1) from Location").fetchone()[0]
        srid = get_srid(conn=conn)

    # We filter out non-residential buildings
    buildings = all_buildings[(all_buildings.land_use == "residential") | (all_buildings.land_use.isna())]

    # Roughly decide those that may or may not be small or large
    buildings = buildings.assign(is_large=1, is_small=1)
    buildings.loc[((buildings.floor_area < 1000) | (buildings.height < 6)), "is_large"] = 0
    buildings.loc[((buildings.floor_area > 1000) | (buildings.height > 9)), "is_small"] = 0
    location_candidates = buildings.to_crs(srid)

    # Let's compute the percentage of single and multi-family households in our area
    c = Census(census_api_key)

    # Get the number of housing units as distributed throughout the modeling area
    census_data = []
    for _, rec in state_counties.iterrows():
        census_data.extend(c.sf1.state_county_tract("H001001", rec["STATEFP"], rec["COUNTYFP"], Census.ALL))
    hholds = pd.DataFrame([[dt["tract"], dt["H001001"]] for dt in census_data], columns=["TRACTCE10", "housing_units"])
    hholds.housing_units = np.ceil(hholds.housing_units * residential_sample_rate).astype(int)

    geographies = []
    for state in state_counties.state_name.unique():
        gdf = pygris.tracts(state=state, year=2010, cache=True).rename(columns={"COUNTYFP10": "COUNTYFP"})
        gdf = gdf[gdf.COUNTYFP.isin(state_counties[state_counties.state_name == state].COUNTYFP)]
        geographies.append(gdf)
    tracts = pd.concat(geographies)

    ctrl_tot = tracts.merge(hholds, on="TRACTCE10")
    ctrl_tot = ctrl_tot.assign(density=ctrl_tot.housing_units / ctrl_tot.geometry.to_crs(3857).area)
    ctrl_tot = ctrl_tot.assign(prob_multi=0.1 + (ctrl_tot.density / ctrl_tot.density.max()) * 0.9)
    ctrl_tot = ctrl_tot.assign(prob_single=1 - ctrl_tot.prob_multi)
    ctrl_tot = ctrl_tot.to_crs(srid)

    # It turns out that this overlay is impossibly time-consuming for large models, but no much way around it
    # # We guarantee that there are locations in every zone by overlaying the zones with the tracts
    # # And later generating locations for each one of the sub-polygons
    ctrl_tot = gpd.overlay(zone_layer, ctrl_tot, how="intersection", keep_geom_type=False)
    ctrl_tot.loc[:, "housing_units"] = np.ceil(ctrl_tot.density * ctrl_tot.geometry.to_crs(3857).area)

    # Get the total number of households in the area by building size
    fields = {
        "total": "DP04_0001E",
        "single_family": "DP04_0007E",
        "single_family_attached": "DP04_0008E",
        "two_units": "DP04_0009E",
        "three_to_four_units": "DP04_0010E",
        "five_to_nine_units": "DP04_0011E",
        "ten_to_nineteen_units": "DP04_0012E",
        "twenty_or_more_units": "DP04_0013E",
        "mobile_homes": "DP04_0014E",
        "boat_rv_van_etc": "DP04_0015E",
    }

    hh_data = dict.fromkeys(fields.keys(), 0)
    for _, state_fips, county_fips in state_counties[["STATEFP", "COUNTYFP"]].drop_duplicates().to_records():
        for k, x in fields.items():
            hh_data[k] += c.acs5dp.state_county(("NAME", x), state_fips, county_fips)[0][x]

    multi_distribution = np.array(
        [
            hh_data["two_units"],
            hh_data["three_to_four_units"],
            hh_data["five_to_nine_units"],
            hh_data["ten_to_nineteen_units"],
            hh_data["twenty_or_more_units"],
        ]
    )
    multi_distribution = np.cumsum(multi_distribution) / multi_distribution.sum()
    multi_multipliers = np.array([2, 3.5, 7, 14.5, 40])

    # Randomly distribute locations for each tract in the modeling region, picking them from buildings
    np.random.seed(1)
    all_locations = []
    tot_elements = 0
    ctrl_tot.reset_index(drop=True, inplace=True)

    signal = SIGNAL(object)
    signal.emit(["start", "master", ctrl_tot.shape[0], "Adding residential locations"])  # type: ignore

    for idx, rec in ctrl_tot.iterrows():
        signal.emit(["update", "master", idx + 1, "Adding residential locations"])  # type: ignore
        if not rec.geometry.area:
            continue
        tot = 0
        sizes = []
        while tot < rec.housing_units:
            if np.random.rand() <= rec.prob_single:
                tot += 1
                sizes.append(1)
            else:
                # We find the size of the multi-family in a random fashion
                # considering that the probability of each size is always the same for the entire region
                size_index = np.nonzero(multi_distribution > np.random.rand())[0][0]
                found_size = multi_multipliers[size_index]
                if np.floor(tot + found_size) > rec.housing_units:
                    tot += 1
                    sizes.append(1)
                    continue
                tot += found_size
                sizes.append(found_size)

        tot_elements += len(sizes)
        locs = location_candidates[location_candidates.intersects(rec.geometry)]
        small = min(locs.is_small.sum(), len([x for x in sizes if x == 1]))
        large = min(locs.is_large.sum(), len([x for x in sizes if x > 1]))
        loc_add = [
            locs[locs.is_small == 1].sample(n=small).assign(luse="RESIDENTIAL-SINGLE"),
            locs[locs.is_large == 1].sample(n=large).assign(luse="RESIDENTIAL-MULTI"),
        ]
        all_locations.extend(loc_add)
    signal.emit(["update", "master", ctrl_tot.shape[0], "Adding residential locations"])  # type: ignore
    locs = pd.concat(all_locations)
    remaining_buildings = all_buildings[~all_buildings.index.isin(locs.index)]
    locs = locs.assign(
        loc_id=1 + np.arange(max_loc, max_loc + locs.shape[0]), geo_wkb=locs.geometry.to_wkb(), srid=srid
    )
    lu_base = "INSERT OR IGNORE INTO land_use(land_use, is_home, is_work,is_school,is_discretionary) VALUES(?,1,0,0,1);"
    with commit_and_close(net.path_to_file, spatial=True) as conn:
        remove_constraints(conn)
        conn.executemany(lu_base, [["RESIDENTIAL-SINGLE"], ["RESIDENTIAL-MULTI"]])

        zones = DataTableAccess(net.path_to_file).get("Zone", conn)[["zone", "geo"]]
        links = DataTableAccess(net.path_to_file).get("Link", conn)[["link", "geo"]]
        locs = locs.sjoin_nearest(zones)[["loc_id", "luse", "zone", "geo_wkb", "srid", "geometry"]]
        locs = locs.drop_duplicates(subset="loc_id")
        if links.empty:
            locs = locs.assign(link=-1)
        else:
            locs = locs.sjoin_nearest(links, how="left")
            locs = locs.drop_duplicates(subset="loc_id")

        res_locations = locs[["loc_id", "luse", "link", "zone", "geo_wkb", "srid"]]
        conn.executemany(
            "INSERT INTO Location (location, land_use, link, zone, geo) VALUES (?, ?, ?, ?, GeomFromWKB(?, ?))",
            res_locations.to_records(index=False),
        )
    return remaining_buildings


def add_commercial(
    net: Network,
    zone_layer: gpd.GeoDataFrame,
    other_sample_rate: float,
    pois: gpd.GeoDataFrame,
):
    logging.info("pre-processing non-residential locations")
    with read_and_close(net.path_to_file) as conn:
        srid = get_table_srid(conn, "Location")
        max_loc = conn.execute("Select coalesce(max(location) + 1, 1) from Location").fetchone()[0]

    zone_layer = zone_layer.to_crs(srid)[["zone", "geo"]]
    pois = pois.to_crs(srid)

    pois = pois.sjoin(zone_layer, how="inner", predicate="intersects")

    def pick(g):
        n = max(1, math.ceil(len(g) * other_sample_rate))
        n = min(n, len(g))  # safety
        return g.sample(n=n, random_state=42)

    if other_sample_rate < 1.0:
        signal = SIGNAL(object)
        gpb = pois.groupby("zone")
        signal.emit(["start", "master", len(gpb), "Adding Adding non-residential locations"])  # type: ignore
        all_data = []
        for idx, (_, df) in enumerate(gpb):
            signal.emit(["update", "master", idx + 1, "Adding Adding non-residential locations"])  # type: ignore
            all_data.append(df.groupby("code_level2", group_keys=False).apply(pick))
        pois = pd.concat(all_data)
        signal.emit(["update", "master", len(gpb), ""])  # type: ignore

    locs = pois.assign(geo_wkb=pois.geometry.to_wkb(), srid=srid, loc_id=np.arange(max_loc, max_loc + pois.shape[0]))
    locs = locs.rename(columns={"code_level2": "luse"})

    sql_qry = "INSERT INTO Location (location, land_use, link, zone, geo) VALUES (?, ?, ?, ?, GeomFromWKB(?, ?))"
    with commit_and_close(net.path_to_file, spatial=True) as conn:
        remove_constraints(conn)
        links = DataTableAccess(net.path_to_file).get("Link", conn)[["link", "geo"]].to_crs(srid)
        if links.empty:
            locs = locs.assign(link=-1)
        else:
            locs = locs.sjoin_nearest(links, how="left")
            locs = locs.drop_duplicates(subset="loc_id")
        conn.executemany(sql_qry, locs[["loc_id", "luse", "link", "zone", "geo_wkb", "srid"]].to_records(index=False))


def remove_constraints(conn: sqlite3.Connection):
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("PRAGMA ignore_check_constraints=1")
