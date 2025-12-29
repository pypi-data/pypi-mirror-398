# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import random
from pathlib import Path

from polaris.network.network import Network
from polaris.utils.database.db_utils import commit_and_close, read_and_close
from polaris.network.utils.srid import get_srid


def add_parking(supply_path: Path, sample_rate):
    random.seed(42)
    net = Network.from_file(supply_path, False)
    geotool = net.geotools
    open_data = net.open_data
    with read_and_close(supply_path) as conn:
        max_park = conn.execute("Select coalesce(max(parking) + 1, 1) from Parking").fetchone()[0]
        srid = get_srid(conn=conn)

    model_area = geotool.model_area

    od_parking, osm_parking_pricing_rule = [], []
    gdf = open_data.get_pois()
    gdf = gdf[gdf.category_code == "parking"]
    if gdf.empty:
        return

    for geo in gdf.geometry.tolist():
        if not model_area.contains(geo):
            continue
        if random.random() > sample_rate:
            continue
        od_parking.append([max_park, geo.wkb, srid])
        osm_parking_pricing_rule.append([max_park, max_park])
        max_park += 1

    parking_sql = """insert into Parking(parking, link, zone, offset, setback, "type", space, walk_link, walk_offset, bike_link, bike_offset, num_escooters, close_time, geo)
                                 values (?, -1, -1, -1, 0, 'OSM', 1, -1, -1, -1, -1, 0, 86400, GeomFromWKB(?, ?));"""

    parking_pricing_sql = """insert into Parking_Pricing("parking", "parking_rule", "entry_start", "entry_end", "price")
                            values(?, ?, 0, 86400, 0);"""

    parking_rule_sql = """Insert into Parking_Rule("parking_rule", "parking", "rule_type", "rule_priority", "min_cost", "min_duration", "max_duration")
                            values(?, ?, 3, 1, 0, 0, 86400);"""

    if len(od_parking) > 0:
        with commit_and_close(supply_path, spatial=True) as conn:
            conn.executemany(parking_sql, od_parking)
            conn.executemany(parking_rule_sql, osm_parking_pricing_rule)
            conn.executemany(parking_pricing_sql, osm_parking_pricing_rule)

            num_links = conn.execute("Select count(*) from Link").fetchone()[0]
            num_active1 = conn.execute("Select count(*) from Transit_Walk").fetchone()[0]
            num_active2 = conn.execute("Select count(*) from Transit_Bike").fetchone()[0]
            num_zones = conn.execute("Select count(*) from Zone").fetchone()[0]

    if num_zones > 0:
        net.geo_consistency.update_zone_association(do_tables=["Parking"])
    if num_links > 0:
        net.geo_consistency.update_link_association(do_tables=["Parking"])
    if min(num_active1, num_active2) > 0:
        net.geo_consistency.update_active_network_association(do_tables=["Parking"])
    net.close(False)
