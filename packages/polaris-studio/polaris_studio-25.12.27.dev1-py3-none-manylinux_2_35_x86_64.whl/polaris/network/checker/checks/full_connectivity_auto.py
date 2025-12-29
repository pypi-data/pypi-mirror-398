# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from polaris.utils.database.db_utils import read_and_close


def full_connectivity_auto(supply_db):
    """Checks auto network connectivity

    It computes paths between nodes in the network or between every single link/direction combination
    in the network
    """

    link_sql = """select l.link, l.lanes_ab, l.lanes_ba from Link l
                   INNER JOIN link_type lt on l.type=lt.link_type
                   where (l.lanes_ab>0 OR l.lanes_ba>0) AND (lt.use_codes like '%BUS%' or lt.use_codes like '%HOV%' or
                          lt.use_codes like '%AUTO%' or lt.use_codes like '%TRUCK%' or lt.use_codes like '%TAXI%')"""

    get_qry = "SELECT link flink, dir fdir, to_link tlink, to_dir tdir, 1.0 distance from Connection"

    with read_and_close(supply_db) as conn:
        records = pd.read_sql(get_qry, conn)
        links = pd.read_sql(link_sql, conn)

    if records.empty:
        return {"connectivity auto": "NO CONNECTIONS IN THE NETWORK"}

    all_link_ids = links.link.to_numpy()
    auto_net = records.assign(fnode=records.flink * 2 + records.fdir, tnode=records.tlink * 2 + records.tdir)

    # The graph is composed by connections, which behave as the edges, and link/directions, which represent
    # the vertices in the connected component analysis
    fnodes = auto_net.fnode.astype(np.int64).to_numpy()
    tnodes = auto_net.tnode.astype(np.int64).to_numpy()
    n = max(fnodes.max() + 1, tnodes.max() + 1)
    csr = coo_matrix((auto_net.distance.to_numpy(), (fnodes, tnodes)), shape=(n, n)).tocsr()

    n_components, labels = connected_components(csgraph=csr, directed=True, return_labels=True, connection="strong")

    # We then identify all the link/directions that have the highest connectivity degree (i.e. the biggest island)
    bc = np.bincount(labels)
    max_label = np.where(bc == bc.max())[0][0]
    isconn = np.where(labels == max_label)[0]

    start_point = np.floor(isconn / 2).astype(np.int64)
    end_point = np.ceil(isconn / 2).astype(np.int64)

    # If that link is one-way, we add it as "connected" in the opposite direction as well
    start_point = np.unique(np.hstack((start_point, links.query("lanes_ba == 0").link.to_numpy())))
    end_point = np.unique(np.hstack((end_point, links.query("lanes_ab == 0").link.to_numpy())))

    connected = np.intersect1d(start_point, end_point)

    disconn = np.setdiff1d(all_link_ids, connected)
    return {"Disconnected links": [int(x) for x in disconn]} if disconn.shape[0] > 0 else []
