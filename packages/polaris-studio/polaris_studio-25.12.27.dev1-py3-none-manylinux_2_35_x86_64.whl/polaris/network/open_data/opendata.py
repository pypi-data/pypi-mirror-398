# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import datetime
import hashlib
import logging
import os
import warnings
from pathlib import Path
from time import sleep
from typing import Dict, Any, List, Optional, Union

import geopandas as gpd
import pandas as pd

from polaris.network.open_data.open_data_utils import start_cache
from polaris.network.open_data.overture_data import get_overture_elements
from polaris.network.open_data.traffic_light import TrafficLight
from polaris.network.open_data.utils.bbox_builder import build_bounding_boxes
from polaris.network.starts_logging import logger
from polaris.network.tools.geo_index import GeoIndex
from polaris.network.utils.srid import get_srid
from polaris.utils.database.data_table_access import DataTableAccess
from polaris.utils.database.db_utils import commit_and_close, read_and_close
from polaris.utils.logging_utils import polaris_logging
from polaris.utils.user_configs import UserConfig


class OpenData:
    """Suite of geo-operations to retrieve data from Open-Street Maps

    **FOR LARGE MODELLING AREAS IT IS RECOMMENDED TO DEPLOY YOUR OWN OVERPASS SERVER**

    ::

        from os.path import join
        import sqlite3
        from datetime import timedelta
        from polaris.network.network import Network

        root = 'D:/Argonne/GTFS/CHICAGO'
        network_path = join(root, 'chicago2018-Supply.sqlite')

        net = Network()
        net.open(network_path)

        osm = net.osm

        # The first call to osm.get_traffic_signal() will download data for
        # the entire modelling area

        # Here we default to our own server
        osm.url = 'http://192.168.0.105:12345/api'
        # And we also set the wait time between queries to zero,
        # as we are not afraid of launching a DoS attack on ourselves
        osm.sleep_time = 0

        # If we want to list all nodes in the network that have traffic lights
        # We can get the distance to the closest traffic signal on OSM, including their OSM ID

        for node, wkb in net.conn.execute('Select node, ST_asBinary(geo) from Node').fetchall():
            geo = shapely.wkb.loads(wkb)
            tl = osm.get_traffic_signal(geo)
            print(f'{node}, {tl.distance}, {tl.osm_id}'

        # A more common use is within the Intersection/signal API
        # We would ALSO assign the url and sleep time EXACTLY as shown above
        for node in net.conn.execute('Select node from Node').fetchall():
            intersection = net.get_intersection(node)

            if intersection.osm_signal():
                intersection.delete_signal():
                sig = intersection.create_signal()
                sig.re_compute()
                sig.save()
    """

    #: URL of the Overpass API
    url = UserConfig().osm_url
    #: Pause between successive queries when assembling OSM dataset
    sleep_time = 1
    __tile_sz = 500
    __cache_db = UserConfig().open_data_cache

    def __init__(self, path_to_file: os.PathLike) -> None:
        from pyproj import Transformer
        from polaris.utils.database.data_table_access import DataTableAccess
        from polaris.network.tools.geo import Geo
        import geopandas as gpd

        polaris_logging()
        self.srid = get_srid(database_path=path_to_file)
        self.__data_tables = DataTableAccess(path_to_file)
        self.__geotool = Geo(path_to_file)

        self.links = {}  # type: Dict[int, Any]

        self.mode_link_idx: Dict[str, GeoIndex] = {}
        self._outside_zones = 0
        self.__traffic_lights: gpd.GeoDataFrame = gpd.GeoDataFrame([])
        self.graphs: Dict[str, Any] = {}
        self.failed = True
        self._path_to_file = path_to_file
        self.__model_area_polyg: Optional[Any] = None
        self.__model_boundaries: Optional[Any] = None

        self.__back_transform = Transformer.from_crs(self.srid, 4326, always_xy=True)
        self.__transformer = Transformer.from_crs(4326, self.srid, always_xy=True)
        self.__poi_class = pd.DataFrame([])
        self.__bldg_class = pd.DataFrame([])
        self.__data: Dict[str, pd.DataFrame] = {}

    @property
    def poi_classifications(self) -> pd.DataFrame:
        src_dir = Path(__file__).parent
        self.__poi_class = pd.read_csv(src_dir / "ovm_poi_categ.csv") if self.__poi_class.empty else self.__poi_class
        return self.__poi_class

    @property
    def building_classifications(self) -> pd.DataFrame:
        src_dir = Path(__file__).parent
        self.__bldg_class = pd.read_csv(src_dir / "ovm_bldg_cat.csv") if self.__bldg_class.empty else self.__bldg_class
        return self.__bldg_class

    def get_buildings(self):
        df = self.__get_overture_data("buildings")
        return df.merge(self.building_classifications, left_on="land_use", right_on="category_code", how="left")

    def get_pois(self, land_use_types: Optional[Union[List[str], str]] = None):
        df = self.__get_overture_data("places")
        df = df.merge(self.poi_classifications, left_on="main_category", right_on="category_code", how="left")
        if land_use_types is None:
            return df
        lu_types = [land_use_types] if isinstance(land_use_types, str) else land_use_types
        return df[df.code_level2.isin(list(lu_types))]

    def __get_overture_data(self, theme: str):
        import geopandas as gpd

        if theme in self.__data:
            return

        model_area_gdf = gpd.GeoDataFrame({"model": [1]}, geometry=gpd.GeoSeries(self.model_boundaries), crs=self.srid)
        gdf = get_overture_elements(model_area_gdf, theme)
        self.__data[theme] = gdf.to_crs(self.srid)
        return self.__data[theme]

    def get_traffic_signal(self, point) -> TrafficLight:
        """Returns the traffic light object closest to the point provided

        Args:
            *point* (:obj:`Point`): A Shapely Point object

        Return:
            *traffic_light* (:obj:`TrafficLight`): Traffic light closest to the provided point
        """

        if self.__traffic_lights.empty:
            msg = "Geometry is in a geographic CRS. Results from 'area' are likely incorrect."
            warnings.filterwarnings("ignore", message=msg)
            self.__load_traffic_light_data()
            warnings.resetwarnings()

        t = TrafficLight()
        if self.__traffic_lights.empty or not isinstance(self.__traffic_lights, gpd.GeoDataFrame):
            return t

        nearest_idx = list(self.__traffic_lights.sindex.nearest(point, return_all=False))[1][0]
        nearest_gdf = self.__traffic_lights.iloc[nearest_idx]

        if not nearest_gdf.empty:
            t.distance = nearest_gdf.geo.distance(point)
            t.osm_id = nearest_gdf.osm_id
            t.geo = nearest_gdf.geo

        return t

    def clear_disk_cache(self):
        """Clears the OSM cache on disk"""
        self.__cache_db.unlink(True)
        self.__traffic_lights.clear()

    @property
    def model_boundaries(self):
        from shapely.geometry import Polygon, box

        self.__model_boundaries = self.__model_boundaries or Polygon(box(*self.__geotool.model_area.bounds))
        return self.__model_boundaries

    def __load_traffic_light_data(self):
        queries = ['[out:json][timeout:180];(node["highway"="traffic_signals"]["area"!~"yes"]({});>;);out;']
        """Loads data from OSM or cached to disk"""
        import requests
        from shapely.geometry import box

        self.failed = False

        start_cache(self.__cache_db)
        self.__model_area_strict()
        if self.__check_enough_cached():
            self.__load_from_cache()
            return

        # We won't download any area bigger than 25km by 25km
        bboxes = build_bounding_boxes(
            self.model_boundaries, self.__tile_sz, self.__back_transform, self.__model_area_polyg
        )
        logging.debug(f"Downloading OSM data. {len(bboxes)} bounding boxes for traffic signals")
        headers = requests.utils.default_headers()
        headers.update({"Accept-Language": "en", "format": "json"})
        for bbox in bboxes:
            bbox_str = ",".join([str(round(x, 6)) for x in bbox])
            cache_name = self.__cache_name(bbox_str)

            if self.__check_signals_cached(cache_name):
                logging.debug(f"Found download {cache_name} in cache, skipping download")
                continue
            logging.info(f"Downloading tile {cache_name} for traffic signals with bbox {bbox_str}")

            for query in queries:
                if len(bboxes) * len(queries) > 2:
                    sleep(self.sleep_time)
                dt = {"data": query.format(bbox_str)}
                response = requests.post(f"{self.url}/interpreter", data=dt, timeout=180, headers=headers, verify=False)
                if response.status_code != 200:
                    self.__traffic_lights = pd.DataFrame([])
                    Warning("Could not download data")
                    logger.error("Could not download data for traffic lights")
                    self.failed = True
                    self.__traffic_lights = pd.DataFrame([])
                    return

                # get the response size and the domain, log result
                json_data = response.json()
                if "elements" in json_data:
                    self.__ingest_json(json_data, cache_name)

            with commit_and_close(self.__cache_db, spatial=True) as conn:
                box_wkb = box(bbox[1], bbox[0], bbox[3], bbox[2]).wkb
                idx_data = [cache_name, datetime.date.today().isoformat(), box_wkb]
                conn.execute(
                    """INSERT OR IGNORE INTO osm_traffic_signal_downloads (id, download_date, geo)
                                 VALUES (?, ?, GeomFromWKB(?, 4326))""",
                    idx_data,
                )

        self.__load_from_cache()

    def __check_signals_cached(self, cache_name):
        with read_and_close(self.__cache_db, spatial=False) as conn:
            data = conn.execute(
                "SELECT count(*) FROM osm_traffic_signal_downloads WHERE id = ?", (cache_name,)
            ).fetchone()
            return sum(data) > 0

    def __check_enough_cached(self) -> bool:
        downloaded = DataTableAccess(self.__cache_db).get("osm_traffic_signal_downloads", from_cache_ok=False)
        downloaded = downloaded.clip(self.__model_area_polyg)

        if downloaded.empty or downloaded.geo.area.sum() / self.__model_area_polyg.area < 0.999:  # type: ignore
            return False
            # Tiny (0.1%) slivers missing are not enough to consider the download invalid
        return True

    def __load_from_cache(self):
        data = DataTableAccess(self.__cache_db).get("osm_traffic_signals", from_cache_ok=False)
        self.__traffic_lights = data.clip(self.__model_area_polyg).to_crs(self.srid)

    def __ingest_json(self, json_data, cache_name):
        elements = json_data["elements"]
        node_index = {x["id"]: [x["lon"], x["lat"]] for x in elements if x.get("type", {}) == "node"}
        data = []
        for x in elements:
            id = x.get("id", None)
            if x.get("tags", {}).get("highway", "") != "traffic_signals" or id is None:
                continue
            if "lon" not in x and "nodes" in x:
                lons = []
                lats = []
                # We get the geo-center of the points
                for nid in x["nodes"]:
                    if nid not in node_index:
                        continue
                    lons.append(node_index[nid][0])
                    lats.append(node_index[nid][1])
                lon = sum(lons) / max(len(lons), 1)
                lat = sum(lats) / max(len(lats), 1)
            else:
                lon = x.get("lon", 0)
                lat = x.get("lat", 0)

            data.append([id, lon, lat])
        df = pd.DataFrame(data, columns=["osm_id", "x", "y"])
        if df.empty:
            return

        with commit_and_close(self.__cache_db, spatial=True) as conn:
            df = df.assign(download_id=cache_name)
            rec_data = df[["osm_id", "download_id", "x", "y"]].to_records(index=False)
            conn.executemany(
                """INSERT OR IGNORE INTO osm_traffic_signals (osm_id, download_id, geo)
                                         VALUES (?, ?, MakePoint(?, ?, 4326))""",
                rec_data,
            )

    def __model_area_strict(self):
        zones = self.__data_tables.get("Zone").to_crs(4326)
        source = zones if not zones.empty else self.__data_tables.get("Link").to_crs(4326)
        self.__model_area_polyg = source.union_all().convex_hull

    def __cache_name(self, bbox_str: str):
        m = hashlib.md5()
        m.update(bbox_str.encode())
        return m.hexdigest()
