# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from aequilibrae.paths.graph import Graph
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from shapely.geometry.linestring import LineString

from polaris.utils.database.data_table_access import DataTableAccess


class StaticGraph:
    def __init__(self, supply_pth: Path):
        self.supply_pth = supply_pth
        self._graph = Graph()
        self.node_offset = 0

        self.links = DataTableAccess(self.supply_pth).get("Link")
        self.nodes = DataTableAccess(self.supply_pth).get("Node").drop(columns=["zone"])
        self.zones = DataTableAccess(self.supply_pth).get("Zone")
        self.__basic_net = pd.DataFrame([])

    def build_graph(self):
        # Make sure it is all in the same CRS, in case it was changed at some point
        self.__basic_graph_build()

    def __basic_graph_build(self):
        self.nodes = self.nodes.to_crs(self.links.crs)
        if not self.zones.empty:
            self.zones = self.zones.to_crs(self.links.crs)
            self.node_offset = self.zones.zone.max() + 1

        ltype = DataTableAccess(self.supply_pth).get("Link_type").reset_index()[["link_type", "use_codes"]]
        links = self.links.merge(ltype, left_on="type", right_on="link_type")

        # Filter links
        links = links[
            links.use_codes.str.lower().str.contains("auto") | links.use_codes.str.lower().str.contains("truck")
            ]

        # Let's assert some things about the links so we can get everything we need for a static traffic assignment
        # First, capacities
        links = links.assign(capacity_ab=0, capacity_ba=0)
        capacity_dict = {"MAJOR": 750, "RAMP": 800, "PRINCIPAL": 800, "FREEWAY": 1200, "EXPRESSWAY": 1200}
        capacity_dict = capacity_dict | {"FRONTAGE": 600, "BRIDGE": 600, "TUNNEL": 600, "EXTERNAL": 600, "OTHER": 600}
        capacity_dict = capacity_dict | {"LOCAL": 300, "LOCAL_THRU": 350, "COLLECTOR": 400, "MINOR": 600}

        for ltype, lanecap in capacity_dict.items():
            for capfield, lanesfield in [("capacity_ab", "lanes_ab"), ("capacity_ba", "lanes_ba")]:
                links.loc[links["type"].str.upper() == ltype, capfield] = (
                        links.loc[links["type"].str.upper() == ltype, lanesfield] * lanecap
                )

        zero_cap = list(links.query("capacity_ab + capacity_ba ==0")["type"].unique())
        if len(zero_cap) > 0:
            warnings.warn(f"Link types {','.join(zero_cap)} have zero capacity")

        # Now free-flow travel times in minutes
        links = links.assign(
            time_ab=(links["length"] / links.fspd_ab) / 60, time_ba=(links["length"] / links.fspd_ba) / 60
        )
        links.replace([np.inf, -np.inf], 0, inplace=True)
        # Division can return infinite values, so let's fix them

        # Now, directions
        links = links.assign(direction=0, source="supply_file")
        links.loc[links.lanes_ab == 0, "direction"] = -1
        links.loc[links.lanes_ba == 0, "direction"] = 1
        links = links[links.lanes_ab + links.lanes_ba > 0]
        if links.active_geometry_name != "geometry":
            links.rename_geometry("geometry", inplace=True)

        # Now we get only the columns we need
        cols = ["link", "length", "node_a", "node_b", "capacity_ab", "capacity_ba", "time_ab", "time_ba", "direction", "geometry"]
        lnks_net = links[cols]
        lnks_net = lnks_net.rename(
            columns={"link": "link_id", "node_a": "a_node_network", "node_b": "b_node_network", "length": "distance"}
        )

        lnks_net = lnks_net.assign(connector_penalty=0, a_node=lnks_net.a_node_network, b_node=lnks_net.b_node_network)

        # Polaris models do not have centroids and connectors, so we need to create them
        # Get nodes and zones
        if self.zones.empty:
            connectors = pd.DataFrame([])
            centroids = None
        else:
            # Let's shift the node IDs to make sure our zone numbers do not conflict with node IDs
            self.nodes.node += self.node_offset
            lnks_net.a_node += self.node_offset
            lnks_net.b_node += self.node_offset

            centr = self.zones.geometry.centroid
            centroids = gpd.GeoDataFrame(self.zones.zone, geometry=centr, crs=self.zones.crs)

            # Only get the nodes that are actually in the network
            nodes = self.nodes[(self.nodes.node.isin(lnks_net.a_node)) | (self.nodes.node.isin(lnks_net.b_node))]
            nodes = nodes[nodes.node.isin(node_candidates_for_connectors(lnks_net))]
            if nodes.active_geometry_name != "geometry":
                nodes.rename_geometry("geometry", inplace=True)

            connectors = centroids.sjoin_nearest(nodes, how="left", distance_col="distance").sort_values(by=["distance"])
            connectors = connectors.drop_duplicates(subset="distance", keep="first")
            connectors = connectors[["node", "zone", "distance", "geometry"]]
            connectors = connectors.rename(columns={"geometry": "geometry_from"})

            connectors = connectors.merge(nodes[["node", "geometry"]], on="node", how="left")
            connectors = connectors.rename(columns={"geometry": "geometry_to"})
            connectors["geometry"] = connectors.apply(
                lambda row: LineString([row.geometry_from, row.geometry_to]), axis=1
            )
            connectors = connectors.drop(columns=["geometry_from", "geometry_to"])

            missing = centroids[~centroids.zone.isin(connectors.zone)]
            if not missing.empty:
                # Makes sure that ALL centroids appear in the graph
                connectors2 = pd.DataFrame({"node": missing.zone, "zone": missing.zone, "distance": 0.001})
                connectors = pd.concat([connectors, connectors2], ignore_index=True)

            # Create connectors with speed of 12 m/s, or 43 km/h
            # This is to make sure that the connector to the closest node will be used, unless not actually connected
            connectors = connectors.assign(
                b_node_network=connectors["node"] - self.node_offset,
                direction=0,
                capacity_ab=1000000,
                capacity_ba=1000000,
                time_ab=connectors["distance"] / 12 / 60,
                time_ba=connectors["distance"] / 12 / 60,
                connector_penalty=connectors["distance"] * 20 + 0.001,
                source="centroid_connector",
            )
            connectors = connectors.assign(link_id=np.arange(connectors.shape[0]) + lnks_net.link_id.max() + 1)
            connectors = connectors.rename(columns={"zone": "a_node", "node": "b_node"})
            connectors["distance"] *= 2  # Compensates for the internal detour missed by using connectors
            centroids = centroids.zone.to_numpy()

        network = pd.concat([lnks_net, connectors], ignore_index=True)
        self._graph = Graph()
        self._graph.network = gpd.GeoDataFrame(network, geometry="geometry", crs=self.links.crs)
        self._graph.prepare_graph(centroids=centroids)
        self._graph.set_graph("time")
        self._graph.set_skimming(["distance", "time"])
        self._graph.set_blocked_centroid_flows(True)

    @property
    def graph(self) -> Graph:
        if self._graph.num_zones <= 0:
            self.build_graph()

        return self._graph


def node_candidates_for_connectors(edges: pd.DataFrame):
    edges_ab = edges[edges.direction>-1]
    edges_ba = pd.DataFrame(edges[edges.direction<1], copy=True)
    edges_ba["aa_node"]= edges_ba["a_node"]
    edges_ba["a_node"] = edges_ba["b_node"]
    edges_ba["b_node"] = edges_ba["aa_node"]
    edges = pd.concat([edges_ab, edges_ba]).drop(columns=["aa_node"])

    nodes = pd.Index(pd.concat([edges["a_node"], edges["b_node"]]).unique())
    node_to_idx = pd.Series(np.arange(len(nodes)), index=nodes)

    row_idx = node_to_idx.loc[edges["a_node"]].to_numpy()
    col_idx = node_to_idx.loc[edges["b_node"]].to_numpy()
    data = np.ones(len(edges), dtype=np.uint8)

    adjacency = csr_matrix((data, (row_idx, col_idx)), shape=(len(nodes), len(nodes)))
    n_components, labels = connected_components(csgraph=adjacency, directed=True, connection="strong")

    # We then identify all the nodes that have the highest connectivity degree (i.e. the biggest island)
    bc = np.bincount(labels)
    max_label = np.where(bc == bc.max())[0][0]
    isconn = np.where(labels == max_label)[0]

    return nodes[isconn]
