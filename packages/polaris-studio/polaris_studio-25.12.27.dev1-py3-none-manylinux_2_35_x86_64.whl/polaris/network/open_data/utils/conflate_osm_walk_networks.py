# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
def conflate_osm_walk_network(tolerance=10):  # pragma: no cover
    """It moves the link ends from the OSM_WALK on top of nodes from the
    roadway whenever they are closer than the tolerance, while also
    re-populating node_a and node_b fields with values known to be unique
    and mutually consistent.
    Each node from the roadway network can only have one node from the
    OSM_WALK network moved on top of them in order to prevent links from the
    OSM_WALK network to have their start and end at the same node.
    Args:
        *tolerance* (:obj:`Float`): Maximum distance to move a link end
    """
    return tolerance
    # self.__data_tables.refresh_cache()
    #
    # network = self.__data_tables.get("OSM_WALK")
    # network.geo = network.geo.apply(shapely.wkb.loads)
    #
    # net_nodes = self.__data_tables.get("Node")
    # net_nodes.geo = net_nodes.geo.apply(shapely.wkb.loads)
    #
    # sql = """select link_id,
    #                 st_asbinary(startpoint(geo)) from_node, startpoint(geo) from_geo,
    #                 X(startpoint(geo)) from_x, Y(startpoint(geo)) from_y ,
    #                 st_asbinary(endpoint(geo)) to_node, endpoint(geo) to_geo,
    #                  X(endpoint(geo)) to_x, Y(endpoint(geo)) to_y
    #                 from OSM_Walk"""
    #
    # with commit_and_close(self._path_to_file, spatial=True) as conn:
    #     df = pd.read_sql(sql, conn)
    #
    #     sindex_status = conn.execute("select CheckSpatialIndex('OSM_Walk', 'geo')").fetchone()[0]
    #     if sindex_status is None:
    #         conn.execute("SELECT CreateSpatialIndex( 'OSM_Walk' , 'geo' );")
    #         conn.commit()
    #         if conn.execute("select CheckSpatialIndex('OSM_Walk', 'geo')").fetchone()[0] is None:
    #             raise ValueError("OSM_Walk has no spatial index and we were not able to add one")
    #     elif sindex_status == 1:
    #         pass
    #     elif sindex_status == 0:
    #         conn.execute('select RecoverSpatialIndex("OSM_Walk", "geo");')
    #         if conn.execute("select CheckSpatialIndex('OSM_Walk', 'geo')").fetchone()[0] == 0:
    #             raise ValueError("OSM_Walk has a broken spatial index and we were not able to recover it")
    #     elif sindex_status == -1:
    #         warnings.warn("There is something weird with the OSM_Walk spatial index. Better check it")
    #
    #     network = network.merge(df, on="link_id")
    #
    #     df = network.drop_duplicates(subset=["from_x", "from_y"])[["from_x", "from_y", "from_geo", "from_node"]]
    #     df.columns = ["x", "y", "orig_geo", "wkb"]
    #     df2 = network.drop_duplicates(subset=["to_x", "to_y"])[["to_x", "to_y", "to_geo", "to_node"]]
    #     df2.columns = ["x", "y", "orig_geo", "wkb"]
    #     osm_nodes = pd.concat([df, df2]).drop_duplicates(subset=["x", "y"])
    #     osm_nodes = osm_nodes.assign(node_id=np.arange(osm_nodes.shape[0]) + OSM_NODE_RANGE)
    #
    #     # We update the OSM_Walk network with the newly computed OSM node IDs
    #     sql = f"""update OSM_Walk set node_a=? WHERE
    #                     StartPoint(geo)=? AND
    #                     ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name = 'OSM_Walk'
    #                               AND search_frame = buffer(?, {tolerance}))"""
    #
    #     sql2 = f"""update OSM_Walk set node_b=? WHERE
    #                     EndPoint(geo)=? AND
    #                     ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name = 'OSM_Walk'
    #                               AND search_frame = buffer(?, {tolerance}))"""
    #
    #     aux = osm_nodes[["node_id", "orig_geo", "orig_geo"]]
    #     aux.columns = ["a", "b", "c"]
    #     aux = aux.to_records(index=False).tolist()
    #
    #     conn.executemany(sql, aux)
    #     conn.executemany(sql2, aux)
    #     conn.commit()
    #
    #     # Update node_a
    #     osm_nodes.drop(columns=["orig_geo"], inplace=True)
    #     osm_nodes.columns = ["from_x", "from_y", "point_geo", "node_id"]
    #
    #     osm_nodes.point_geo = osm_nodes.point_geo.apply(shapely.wkb.loads)
    #     network = network.merge(osm_nodes, how="left", on=["from_x", "from_y"])
    #     network.loc[:, "node_a"] = network.node_id
    #     network.drop(columns=["node_id", "point_geo"], inplace=True)
    #
    #     # update node_b
    #     osm_nodes.columns = ["to_x", "to_y", "point_geo", "node_id"]
    #     network = network.merge(osm_nodes, how="left", on=["to_x", "to_y"])
    #     network.loc[:, "node_b"] = network.node_id
    #     network.drop(columns=["node_id", "point_geo"], inplace=True)
    #
    #     # Build an index for the existing OSM nodes
    #     walk_node_idx = GeoIndex()
    #     walk_node_geos = {}
    #     for _, record in osm_nodes.iterrows():
    #         walk_node_idx.insert(feature_id=record.node_id, geometry=record.point_geo)
    #         walk_node_geos[record.node_id] = record.point_geo
    #
    #     # Search for node correspondences
    #     association = {}
    #     for idx, rec in net_nodes.iterrows():
    #         nearest_list = list(walk_node_idx.nearest(rec.geo, 10))
    #         for near in nearest_list:
    #             near_geo = walk_node_geos[near]
    #             dist = near_geo.distance(rec.geo)
    #             if dist > tolerance:
    #                 break
    #
    #             # Is that OSM node even closer to some other node?
    #             if idx == self.__geotool.get_geo_item("node", near_geo):
    #                 association[near] = idx
    #                 break
    #
    #     # update link geometries
    #     sql = """update OSM_Walk set geo = SetStartPoint(geo, GeomFromWKB(?,?)), node_a=? WHERE
    #                     StartPoint(geo)=GeomFromWKB(?,?) AND
    #                     ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name = 'OSM_Walk'
    #                               AND search_frame = GeomFromWKB(?,?))"""
    #
    #     sql2 = """update OSM_Walk set geo = SetEndPoint(geo, GeomFromWKB(?,?)), node_b=? WHERE
    #                     EndPoint(geo)=GeomFromWKB(?,?) AND
    #                     ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name = 'OSM_Walk'
    #                               AND search_frame = GeomFromWKB(?,?))"""
    #
    #     data_tot = []
    #     for near, node_from_net in association.items():
    #         old_geo = walk_node_geos[near]
    #         new_geo = net_nodes.geo.at[node_from_net]
    #         data_tot.append([new_geo.wkb, self.srid, node_from_net, old_geo.wkb, self.srid, old_geo.wkb, self.srid])
    #
    #     conn.executemany(sql, data_tot)
    #     conn.executemany(sql2, data_tot)
    #     conn.commit()
    #     conn.execute('select RecoverSpatialIndex("OSM_Walk", "geo");')
