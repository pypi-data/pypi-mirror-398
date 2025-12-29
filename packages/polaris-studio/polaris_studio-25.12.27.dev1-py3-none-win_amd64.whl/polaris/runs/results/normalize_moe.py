# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import tables
import os
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from polaris.utils.database.db_utils import read_and_close


@dataclass
class MOEDataToNormalize:
    # --- Supply tables ---
    supply_link_df: Optional[pd.DataFrame] = field(default=None)
    supply_turn_df: Optional[pd.DataFrame] = field(default=None)

    # --- MOE tables ---
    moe_link_df: Optional[pd.DataFrame] = field(default=None)
    moe_turn_df: Optional[pd.DataFrame] = field(default=None)

    # --- MOE raw arrays ---
    link_ttimes: Optional[np.ndarray] = field(default=None)
    turn_penalties: Optional[np.ndarray] = field(default=None)

    # --- Individual arrays ---
    link_uids: Optional[np.ndarray] = field(default=None)
    link_lengths: Optional[np.ndarray] = field(default=None)
    turn_uids: Optional[np.ndarray] = field(default=None)


def fill_data(supply_conn, moe_file: tables.File) -> MOEDataToNormalize:
    data = MOEDataToNormalize()

    # --- Restricted_Lanes table ---
    df_restricted = pd.read_sql("SELECT link, direction, lanes, speed FROM Restricted_Lanes", supply_conn)

    # --- Supply link table ---
    df_link = pd.read_sql("SELECT link, length, fspd_ab, fspd_ba, lanes_ab, lanes_ba, type FROM Link", supply_conn)
    data.supply_link_df = expand_supply_links(df_link, df_restricted)
    data.supply_link_df["link"] = data.supply_link_df["link"].astype(int)

    # --- MOE link data ---
    data.link_uids = np.asarray(moe_file.root.link_moe.link_uids[:]).ravel()
    data.link_lengths = np.asarray(moe_file.root.link_moe.link_lengths[:]).ravel()
    data.link_ttimes = moe_file.root.link_moe.link_travel_time[:]

    data.moe_link_df = pd.DataFrame({"link": data.link_uids, "length": data.link_lengths})
    data.moe_link_df["link"] = data.moe_link_df["link"].astype(int)

    # --- Supply turn table ---
    df_turn = pd.read_sql("SELECT conn AS turn, penalty FROM Connection", supply_conn)
    data.supply_turn_df = df_turn
    data.supply_turn_df["turn"] = data.supply_turn_df["turn"].astype(int)

    # --- MOE turn data ---
    data.turn_uids = np.asarray(moe_file.root.turn_moe.turn_uids[:]).ravel()
    data.turn_penalties = moe_file.root.turn_moe.turn_penalty_by_entry[:]
    data.moe_turn_df = pd.DataFrame({"turn": data.turn_uids})
    data.moe_turn_df["turn"] = data.moe_turn_df["turn"].astype(int)

    return data


def expand_supply_links(df_link: pd.DataFrame, df_restricted: pd.DataFrame) -> pd.DataFrame:
    restricted_lanes_offset = 10_000_000
    allowed_types = [
        "FREEWAY",
        "EXPRESSWAY",
        "PRINCIPAL",
        "MAJOR",
        "MINOR",
        "COLLECTOR",
        "LOCAL_THRU",
        "LOCAL",
        "FRONTAGE",
        "RAMP",
        "BRIDGE",
        "TUNNEL",
        "EXTERNAL",
        "BUSWAY",
        "OTHER",
    ]

    # ---- Filter allowed link types ----
    filtered = df_link[df_link["type"].isin(allowed_types)]

    # ---- Expand AB (0) and BA (1) directions ----
    ab = filtered.loc[filtered["lanes_ab"] > 0, ["link", "length", "fspd_ab"]].copy()
    ab["dir"] = 0
    # Compute ttime = length / speed
    ab["ttime"] = ab["length"] / ab["fspd_ab"].astype(float)
    ab.drop(columns=["fspd_ab"], inplace=True)

    ba = filtered.loc[filtered["lanes_ba"] > 0, ["link", "length", "fspd_ba"]].copy()
    ba["dir"] = 1
    ba["ttime"] = ba["length"] / ba["fspd_ba"].astype(float)
    ba.drop(columns=["fspd_ba"], inplace=True)

    # Standard directional link ID for supply table
    expanded = pd.concat([ab, ba], ignore_index=True)
    expanded["link"] = expanded["link"] * 2 + expanded["dir"]
    expanded = expanded[["link", "dir", "length", "ttime"]]
    expanded.sort_values(["link"], inplace=True, ignore_index=True)

    # ---- Prepare Restricted_Lanes mapping ----
    df_res = df_restricted.copy()

    # Keep base link for length lookup
    df_res["base_link"] = df_res["link"]
    df_res["link"] = (df_res["link"] + restricted_lanes_offset) * 2 + df_res["direction"]
    df_res.rename(columns={"direction": "dir"}, inplace=True)

    # Lookup length from filtered links
    length_map = filtered.set_index("link")["length"]
    df_res["length"] = df_res["base_link"].map(length_map)

    # Compute ttime = length / speed
    df_res["ttime"] = df_res["length"] / df_res["speed"].astype(float)
    df_res = df_res[["link", "dir", "length", "ttime"]]

    # ---- Merge restricted values ----
    merged = pd.concat([expanded, df_res], ignore_index=True)

    return merged


def normalize_moe(supply_path: Path, h5_path: Path) -> bool:
    new_file = h5_path.name + ".new"
    new_path = h5_path.parent / new_file

    with read_and_close(supply_path) as supply_conn, tables.open_file(str(h5_path), "r") as src:
        data = fill_data(supply_conn, src)

        print(f"Comparing Link tables from {h5_path.name} to {supply_path.name}")
        link_mismatched, turn_mismatched, link_within_bounds, link_lengths_ok = check_for_mismatch(data)
        if (link_mismatched and link_within_bounds and link_lengths_ok) or turn_mismatched:
            with tables.open_file(str(new_path), "w") as dst:
                # Normalize links
                new_link_uids, new_link_lengths, new_link_ttimes = normalize_links(data)
                # Normalize turns
                new_turn_uids, new_turn_penalties = normalize_turns(data)
                # Write all datasets to new file
                create_new_moe(
                    src, dst, new_link_uids, new_link_lengths, new_link_ttimes, new_turn_uids, new_turn_penalties
                )
        else:
            msg = []
            if not link_mismatched:
                msg.append("MOE link data matches supply data, no need to normalize.")
            if not link_within_bounds:
                msg.append("MOE link data is not similar enough to supply data to normalize.")
            if not link_lengths_ok:
                msg.append("Link lengths are not similar enough to consider this a compatible Results file.")
            if not turn_mismatched:
                msg.append("MOE turn data matches supply data, no need to normalize.")
            print("\n".join(msg))
            return False

    count = 1
    renamed_old = h5_path.parent / str(h5_path.stem + "-old" + ".h5")
    renamed_new = h5_path.parent / h5_path.name
    while os.path.exists(renamed_old):
        renamed_old = h5_path.parent / str(h5_path.stem + "-old-" + str(count) + ".h5")
        count += 1
    os.rename(h5_path, renamed_old)
    os.rename(new_path, renamed_new)
    print(f"Normalized MOE data, moved older version into {renamed_old.name}")
    return True


# --- Updated Mismatch Check ---
def check_for_mismatch(data: MOEDataToNormalize, match_threshold: float = 90.0):
    def _merge_and_compare(supply_df, moe_df, id_col, length_col=None):
        merged = pd.merge(supply_df, moe_df, on=id_col, how="outer", suffixes=("_sql", "_moe"), indicator=True)
        id_match = (merged["_merge"] == "both").mean() * 100
        length_match = None
        if length_col and not merged[merged["_merge"] == "both"].empty:
            matched = merged[merged["_merge"] == "both"]
            length_match = (
                np.isclose(matched[f"{length_col}_sql"], matched[f"{length_col}_moe"], rtol=1e-3).mean() * 100
            )
        return merged, id_match, length_match

    # --- Link comparison ---
    link_merged, link_id_match, link_length_match = _merge_and_compare(
        data.supply_link_df, data.moe_link_df, "link", "length"
    )

    # --- Turn comparison ---
    turn_merged, turn_id_match, _ = _merge_and_compare(data.supply_turn_df, data.moe_turn_df, "turn")

    # --- Print results ---
    print("\n🔍 MOE Mismatch Report")
    print("----------------------")
    print(f"Link ID Match:      {link_id_match:.2f}%")
    print(f"Link Length Match:  {link_length_match if link_length_match is not None else 0:.2f}%")
    print(f"Turn ID Match:      {turn_id_match:.2f}%")

    # --- Logical results ---
    link_mismatched = link_id_match < 100.0
    turn_mismatched = turn_id_match < 100.0
    within_bounds = min(link_id_match, turn_id_match) >= match_threshold
    lengths_ok = link_length_match >= match_threshold

    if not within_bounds:
        print(f"⚠️  Warning: Match below threshold ({match_threshold:.1f}%).")
    if not lengths_ok:
        print("⚠️  Warning: Link length differences exceed tolerance.")

    return link_mismatched, turn_mismatched, within_bounds, lengths_ok


def create_new_moe(
    src: tables.File, dst: tables.File, link_uids, link_lengths, link_travel_times, turn_uids, turn_penalties
):
    # --- Link datasets ---
    n_links = link_uids.shape[0]
    link_uids = link_uids.reshape((1, n_links))
    link_lengths = link_lengths.reshape((1, n_links))
    grp = dst.create_group(dst.root, "link_moe")
    dst.create_array(grp, "link_uids", link_uids.astype(np.uint64))
    dst.create_array(grp, "link_lengths", link_lengths.astype(np.float32))
    dst.create_array(grp, "link_travel_time", link_travel_times.astype(np.float32))
    for attr_name in src.root.link_moe._v_attrs._f_list():
        grp._v_attrs[attr_name] = src.root.link_moe._v_attrs[attr_name]
    grp._v_attrs["num_records"] = int(n_links)

    # Turn datasets
    n_turns = turn_uids.shape[0]
    turn_uids = turn_uids.reshape((1, n_turns))
    grp_turn = dst.create_group(dst.root, "turn_moe")
    dst.create_array(grp_turn, "turn_uids", turn_uids.astype(np.uint64))
    dst.create_array(grp_turn, "turn_penalty_by_entry", turn_penalties.astype(np.float32))
    for attr_name in src.root.turn_moe._v_attrs._f_list():
        grp_turn._v_attrs[attr_name] = src.root.turn_moe._v_attrs[attr_name]
    grp_turn._v_attrs["num_records"] = int(n_turns)

    # Copy Paths and file-level attributes
    src.copy_node(src.root.paths, dst.root)
    for attr_name in src.root._v_attrs._f_list():
        dst.root._v_attrs[attr_name] = src.root._v_attrs[attr_name]

    print(f"📋 Created new MOE file with {n_links} links and {n_turns} turns")


def normalize_links(data: MOEDataToNormalize):
    sql_ids = data.supply_link_df["link"].to_numpy()
    sql_len = data.supply_link_df["length"].to_numpy()
    sql_spd = data.supply_link_df["ttime"].to_numpy()

    timesteps = data.link_ttimes.shape[0]
    new_uids = []
    new_lengths = []
    new_ttime_cols = []

    moe_uid_to_idx = {uid: i for i, uid in enumerate(data.moe_link_df["link"])}

    for uid, length, ff_speed in zip(sql_ids, sql_len, sql_spd):
        if uid in moe_uid_to_idx:
            i = moe_uid_to_idx[uid]
            new_uids.append(uid)
            new_lengths.append(length)  # updated to SQL length
            new_ttime_cols.append(data.link_ttimes[:, i])
        else:
            # new link → insert with default speed column
            new_uids.append(uid)
            new_lengths.append(length)
            new_ttime_cols.append(np.full(timesteps, ff_speed, dtype=data.link_ttimes.dtype))

    new_uids = np.array(new_uids, dtype=int)
    new_lengths = np.array(new_lengths, dtype=float)
    new_ttimes = np.stack(new_ttime_cols, axis=1)  # shape: (timesteps, num_links)
    return new_uids, new_lengths, new_ttimes


def normalize_turns(data: MOEDataToNormalize):
    sql_turns = data.supply_turn_df["turn"].to_numpy()
    sql_penalties = data.supply_turn_df["penalty"].to_numpy()

    timesteps = data.turn_penalties.shape[0]
    new_turn_uids = []
    new_penalty_cols = []
    moe_turn_to_idx = {uid: i for i, uid in enumerate(data.moe_turn_df["turn"])}

    for uid, penalty in zip(sql_turns, sql_penalties):
        if uid in moe_turn_to_idx:
            i = moe_turn_to_idx[uid]
            new_turn_uids.append(uid)
            new_penalty_cols.append(data.turn_penalties[:, i])
        else:
            new_turn_uids.append(uid)
            new_penalty_cols.append(np.full(timesteps, penalty, dtype=data.turn_penalties.dtype))

    new_turn_uids = np.array(new_turn_uids, dtype=int)
    new_penalties = np.stack(new_penalty_cols, axis=1)
    return new_turn_uids, new_penalties
