# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from polaris.utils.pandas_utils import stochastic_round


def disaggregate_column(df, col_name, locations, seed=42, robust_rounding=False):
    df = pd.DataFrame(df[["zone_origin", "zone_dest", col_name]])

    tot_trips = df[col_name].sum()

    # Convert each row with "N" trips into N rows with 1 trip
    if robust_rounding:
        df = repeated_integerize(df, col_name)
    else:
        df[col_name] = stochastic_round(df[col_name])  # integerize the column first

    df = df.loc[df.index.repeat(df[col_name])]
    df = df.reset_index(drop=True)
    df["trip_id"] = np.arange(1, df.shape[0] + 1)

    df = df.assign(origin_location=np.nan, dest_location=np.nan)

    # Prepare the locations in a convenient format
    shuffled_locations, index_loc = locations_fw(locations, seed)

    # Disaggregate origins first, then destinations (the order is irrelevant)
    df = disaggregate_trip_end(df, "zone_origin", "origin_location", shuffled_locations, index_loc)
    df = disaggregate_trip_end(df, "zone_dest", "dest_location", shuffled_locations, index_loc)

    # Makes sure they are integers, then return it all
    df.dest_location = df.dest_location.astype(int)
    df.origin_location = df.origin_location.astype(int)
    new_tot = df.shape[0]
    logging.info(f"{tot_trips:,} trips disaggregated into {new_tot:,} trips")
    logging.info(f"Lost/gained {tot_trips - new_tot:,} trips due to rounding.")
    return df


def locations_fw(locations: pd.DataFrame, seed):
    # We want to shuffle the locations within each zone, but in a reproducible way
    # so we use the zone as the random seed
    # The index_loc array maintains the start and end index of each zone in the shuffled_locations array (similar to a forward star)
    # This allows us to quickly access all locations for a given zone
    shuffled = []
    for zone, df_ in locations.groupby("zone"):
        shuffled.append(df_.sample(frac=1, random_state=zone * seed).reset_index(drop=True))
    all_shuffled = pd.concat(shuffled, ignore_index=True)

    uniq_loc = np.unique(all_shuffled.zone.to_numpy())
    first_loc = np.searchsorted(all_shuffled.zone.to_numpy(), uniq_loc, side="left")
    last_loc = np.searchsorted(all_shuffled.zone.to_numpy(), uniq_loc, side="right")

    shuffled_locations = all_shuffled.location.to_numpy()
    index_loc = np.zeros((uniq_loc.max() + 1, 2), dtype=int)
    index_loc[uniq_loc, 0] = first_loc
    index_loc[uniq_loc, 1] = last_loc
    return shuffled_locations, index_loc


def disaggregate_trip_end(
        df: pd.DataFrame, zone_field: str, loc_field: str, shuffled_locations: np.ndarray, index_loc: np.ndarray
):
    df[zone_field] = df[zone_field].astype(int)

    # By ordering dataframe by the field (origin/destination zone), we can assign locations in bulk for each zone
    # This is much faster than iterating over each row or doing a group by
    df = df.sort_values(by=zone_field)

    # We use the same strategy of forward star indexing to quickly access all trips for a given zone
    # This way we don't really "loop" through the DataFrame
    uniq_zone = np.unique(df[zone_field].to_numpy()).astype(int)
    first_zone = np.searchsorted(df[zone_field].to_numpy(), uniq_zone, side="left")
    last_zone = np.searchsorted(df[zone_field].to_numpy(), uniq_zone, side="right")

    not_found_zones = []
    not_found_records = 0
    for zone, from_, to_ in zip(uniq_zone, first_zone, last_zone):  # type: ignore
        # These are the locations available for that zone
        if zone >= index_loc.shape[0]:
            available = np.array([], dtype=int)
        else:
            available = shuffled_locations[index_loc[zone, 0]: index_loc[zone, 1]]

        if available.shape[0] == 0:
            not_found_zones.append(zone)
            not_found_records += to_ - from_
            use_locations = -1
        else:
            # We start from a random point in the list
            start = np.random.randint(0, available.size)

            # And loop around as many times as we will need to assign locations to all trips
            use_locations = available[(np.arange(start, start + to_ - from_) % available.size)]

        # With those locations selected, we can assign them to the trips
        df.iloc[from_:to_, df.columns.get_loc(loc_field)] = use_locations

    if not_found_records > 0:
        logging.error(
            f"There were {not_found_records} trips for which no appropriate location could be found for {zone_field}."
            f"Zone(s) {[int(x) for x in not_found_zones]} have no appropriate location assigned."
        )
    return df


def repeated_integerize(df, col_name, threshold=1e-3, repetitions=100):
    total_dfs = []
    df = df.assign(int_trips=np.floor(df[col_name]), frac_trips=df[col_name] % 1)
    df.int_trips = df.int_trips.astype(int)
    for _, df_ in df.groupby("zone_origin"):
        df__ = pd.DataFrame(df_, copy=True)
        tot = df_.frac_trips.sum()
        if tot.sum() > 0:
            best = np.random.rand(df_.shape[0])
            diff_best = np.inf
            for _ in range(repetitions):
                rands = np.random.rand(df_.shape[0])
                diff = abs((df_.frac_trips > rands).sum() - tot)
                if diff_best < diff:
                    diff_best = diff
                    best = rands
                if diff / tot < threshold or diff < 1:
                    break
                if diff < 1:
                    break
            df__["int_trips"] += (df_.frac_trips > best).astype(int)
        total_dfs.append(df__.drop(columns=["frac_trips"]))
    df = pd.concat(total_dfs, ignore_index=True)
    df[col_name] = df["int_trips"]
    return df.drop(columns=["int_trips"])


def assign_random_start_time(trips, temporal_dist):
    assert sorted(temporal_dist.columns.tolist()) == [
        "end_hour",
        "proportion",
        "start_hour",
    ], f"temporal_dist df has incorrect fields, {temporal_dist.columns}. You should have ['start_hour', 'end_hour', 'proportion']"

    assert abs(temporal_dist.proportion.sum() - 1.0) < 1e-6, "Proportions do not add sufficiently close to 1.0"

    assert temporal_dist.start_hour.max() < 24, "start_hour values should be less than 24"
    assert temporal_dist.end_hour.max() <= 24, "end_hour values should be less than or equal to 24"

    # We make sure we loop-around the periods that go passed midnight
    temporal_dist.loc[temporal_dist.start_hour > temporal_dist.end_hour, "end_hour"] += 24
    temporal_dist = temporal_dist.sort_values(by="start_hour")
    temporal_dist = temporal_dist.reset_index()

    # Check if we have overlapping intervals
    s = temporal_dist.start_hour.to_numpy()
    e = temporal_dist.end_hour.to_numpy()
    assert np.all(s[1:] >= e[:-1]), "Overlapping time intervals in the temporal distribution are not allowed"

    # We randomly assign each trip to a time period based on the proportions we have for them
    p = np.random.choice(temporal_dist.index.to_numpy(), size=trips.shape[0], p=temporal_dist.proportion)

    # Knowing the period for each trip, we can assign a random time within that period
    # We do that by selecting a random fraction of the period length
    from_time = (temporal_dist.start_hour[p] * 3600).to_numpy()
    to_time = (temporal_dist.end_hour[p] * 3600).to_numpy()
    period_length = to_time - from_time
    random_departure = np.random.random(size=period_length.shape[0])

    #  Then we multiply that proportion by the length of the period and add it to the start time
    # We also make sure to only get the rest of the division by 86400 seconds (number of seconds in a day)
    # to avoid going over midnight
    trips["start"] = (random_departure * period_length + from_time).astype(int) % 86400
    return trips


def plot_temporal_dist(df, label):
    df = df.copy()
    df["hour"] = round(df.minute / 60.0, 1)
    plt.gca().plot(df.hour, 60.0 * df.proportion, label=label)
