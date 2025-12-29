# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging
from pathlib import Path
from typing import Optional

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from aequilibrae.matrix import AequilibraeMatrix
from scipy.sparse import coo_matrix

from polaris.analyze.mapping.flow_lines import delaunay_procedure

thousands = 1000


def demand_report(trips: pd.DataFrame, locations: gpd.GeoDataFrame):
    """
    Generate a demand report for a trip dataset.
    Particularly useful for analysing exogenous trips imported from external models.

    :param trips: DataFrame with Trips
    :param locations: GeoDataFrame of Locations
    """
    # Load demand data

    if trips.shape[0] == 0:
        logging.error("Trips dataframe is empty")
        return

    trips = add_mode_names(trips)

    rows = 4 + trips["mode"].nunique()
    fig, axs = plt.subplots(rows, 2, figsize=(20, rows * 6), sharey=False)

    trips = add_distances(trips, locations)

    _ = vmts(trips, locations, axs[0, 0])
    _ = time_distribution(trips, ax=axs[0, 1])
    _ = trips_by_mode(trips, cname="trips", ax=axs[1, 0], ax_table=axs[1, 1])
    _ = trips_by_type(trips, cname="trips", ax=axs[2, 0], ax_table=axs[2, 1])
    _ = trips_by_land_use(trips, locations, "origin", axs[3, 0], "origin")
    _ = trips_by_land_use(trips, locations, "destination", axs[3, 1], "destination")

    delaunay_results = builds_delaunay(trips, locations)
    for i, mode in enumerate(trips["mode"].unique()):
        # Plots the TLfD for each mode
        _ = tlfd(trips[trips["mode"] == mode], locations, ax=axs[4 + i, 0], data_filter=f"({mode})")  # type: ignore
        # Plots the Delaunay chart for each mode
        _ = delaunay_chart(delaunay_results, mode, ax=axs[4 + i, 1])
    plt.tight_layout()
    return fig


def add_mode_names(trips: pd.DataFrame) -> pd.DataFrame:
    modes = Path(__file__).parent.parent / "demand/database/default_values/Mode.csv"

    trips = trips.merge(pd.read_csv(modes), left_on="mode", right_on="mode_id", how="left")
    return trips.drop(columns=["mode_id", "mode"]).rename(columns={"mode_description": "mode"})


def add_distances(trips: pd.DataFrame, locations: gpd.GeoDataFrame) -> pd.DataFrame:
    geo_col = locations._geometry_column_name
    df_ = trips.merge(locations[["location", "zone", geo_col]], left_on="origin", right_on="location")
    df_ = df_.merge(locations[["location", "zone", geo_col]], left_on="destination", right_on="location",
                    suffixes=('_o', '_d'))

    geo_o = gpd.GeoSeries(data=df_[f"{geo_col}_o"], crs=locations.crs)
    geo_d = gpd.GeoSeries(data=df_[f"{geo_col}_d"], crs=locations.crs)
    euclidean = geo_o.distance(geo_d) / (1609.34)  # meters to miles
    manhatan = (np.abs(geo_o.x - geo_d.x) + np.abs(geo_o.y - geo_d.y)) / (1609.34)  # meters to miles

    return df_.assign(euclidean=euclidean, manhatan=manhatan)


def hide_axis_and_frame(ax):
    """
    Remove axis lines, ticks and background frame from a Matplotlib Axes
    without affecting other subplots (works when axes are shared).
    """
    # hide background patch and frame
    ax.patch.set_visible(False)
    ax.set_frame_on(False)

    # hide spines for this axis
    for spine in ax.spines.values():
        spine.set_visible(False)

    # hide ticklines and ticklabels for this axis only
    for item in ax.xaxis.get_ticklines() + ax.xaxis.get_ticklabels():
        item.set_visible(False)
    for item in ax.yaxis.get_ticklines() + ax.yaxis.get_ticklabels():
        item.set_visible(False)

    # clear tick locations and ensure no labels
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(axis="both", which="both", length=0, labelleft=False, labelbottom=False)

    ax.get_figure().canvas.draw_idle()


def format_df_numbers(df, float_fmt='{:,.2f}'):
    """Return a DataFrame of strings with thousand separators for numbers."""

    def fmt(x):
        if isinstance(x, (float, np.floating)):
            return float_fmt.format(float(x))
        return str(x)

    return df.map(fmt)


def time_distribution(trips, field_name="Trips", ax=None):
    hour = np.floor(trips.start / 3600).astype(int)
    by_hour = np.bincount(hour)

    df_ = pd.DataFrame({"Hour": np.arange(by_hour.shape[0]), field_name: by_hour})
    return df_.plot(y=field_name, x="Hour", title="Trips per hour", ax=ax)


def total_trips_single_class(trips, cname, ax, ax_table, field_total):
    cname = f"{cname} (1,000s)"
    by_field = pd.DataFrame(trips.groupby(field_total).size())
    by_field.columns = [cname]
    by_field[cname] = (by_field[cname]).astype(float)
    by_field[cname] /= thousands
    by_field = by_field.round(1)
    by_field2 = format_df_numbers(by_field, float_fmt='{:,.1f}')
    by_field2=by_field2.reset_index()
    if ax_table is not None:
        hide_axis_and_frame(ax_table)
        table = ax_table.table(cellText=by_field2.values, colLabels=by_field2.columns, cellLoc="center",
                               colLoc="center", loc="center")
        table.set_fontsize(12)
        table.scale(1.0, 2.0)

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))

    by_field.plot(kind='bar', title=f"Trips (thousands) by {field_total}", ax=ax)
    return ax


def trips_by_mode(trips: pd.DataFrame, cname='trips', ax=None, ax_table=None):
    total_trips_single_class(trips, cname, ax, ax_table, "mode")


def trips_by_type(trips: pd.DataFrame, cname='trips', ax=None, ax_table=None):
    total_trips_single_class(trips, cname, ax, ax_table, "type")


def vmts(trips: pd.DataFrame, locations: gpd.GeoDataFrame, ax=None, name=""):
    if any(col not in trips.columns for col in ["euclidean", "manhatan"]):
        trips = add_distances(trips, locations)

    vmt = pd.DataFrame(trips[["mode", "euclidean", "manhatan"]].groupby("mode").sum())
    vmt[["euclidean", "manhatan"]] /= thousands
    vmt = vmt.round(2).rename(columns={"euclidean": f'Euclidean VMT (1,000s){name}', "manhatan": f'Manhatan VMT (1,000s){name}'})
    vmt = format_df_numbers(vmt, float_fmt='{:,.2f}')

    vmt=vmt.reset_index()

    if ax is None:
        _, ax = plt.subplots(figsize=(max(6, 3 * 1.2), max(2, vmt.shape[0] * 0.3)))

    table = ax.table(cellText=vmt.values, colLabels=vmt.columns, cellLoc="center", colLoc="center", loc="center")
    table.set_fontsize(12)
    table.scale(1.0, 2.0)

    hide_axis_and_frame(ax)
    return ax


def trips_by_land_use(trips: pd.DataFrame, locations: gpd.GeoDataFrame, field="origin", ax=None, series_name=None):
    series_name = series_name or field

    df_ = trips[[field]].merge(locations[['location', 'land_use']], left_on=field, right_on="location")
    trips_by_o_lu = pd.DataFrame(df_.groupby(["land_use"]).size())
    trips_by_o_lu.columns = [series_name]
    trips_by_o_lu=trips_by_o_lu.sort_values(by=series_name, ascending=False)

    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))

    return trips_by_o_lu.plot(kind="bar", ax=ax, title=f"Trips (1,000s) by Land-Use of {field}")


def tlfd(trips: pd.DataFrame, locations: Optional[gpd.GeoDataFrame] = None, ax=None, data_filter=""):
    """
    Generate a time-of-day profile for trips.

    :param trips: DataFrame with Trips
    :param time_field: Field name for trip start time in seconds from midnight
    :return: DataFrame with time-of-day profile
    """
    if "manhatan" not in trips.columns:
        if locations is None:
            raise ValueError("locations must be provided if trips do not have distance information")
        trips = add_distances(trips, locations)

    distances = trips.manhatan
    bins = np.arange(0, 76, 2)
    bins = np.hstack((bins, [100, 250]))

    # compute histogram counts and percentages
    counts, _ = np.histogram(distances, bins=bins)
    counts = counts.astype(float) / thousands
    pct = counts / counts.sum() * 100
    cum_pct = np.cumsum(pct)

    # dataframe with frequency table
    freq_df = pd.DataFrame({
        "bin_left_km": bins[:-1],
        "bin_right_km": bins[1:],
        "bin_mid_point": (bins[:-1] + bins[1:]) / 2,
        "trips": counts,
        "percent": np.round(pct, 2),
        "cumulative_percent": np.round(cum_pct, 2),
    })

    freq_df = freq_df.query("cumulative_percent <=95")

    # plot: bars = counts, line = cumulative percent
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    ax.bar(freq_df.bin_left_km.values, freq_df.trips.values,
           width=freq_df.bin_right_km.to_numpy() - freq_df.bin_left_km.to_numpy(), align="edge", color="C0",
           edgecolor="black", alpha=0.8)
    ax.set_xlabel("Trip length (Miles)")
    ax.set_ylabel("Trip count (thousands)")
    ax.set_title(f"Trip length (Manhatan) frequency distribution {data_filter}")

    # twin axis for cumulative percent
    ax2 = ax.twinx()
    ax2.plot(freq_df.bin_mid_point.values, freq_df.cumulative_percent.values, marker="o", color="C1", linewidth=2)
    ax2.set_ylabel(r"Cumulative \%")

    ax2.set_ylim(0, 100)
    return ax


def delaunay_chart(dlny_gdf: gpd.GeoDataFrame, mode_name: str, ax=None):
    max_val = dlny_gdf[f"{mode_name}_tot"].max()
    ax = dlny_gdf.plot(linewidth=4 * dlny_gdf[f"{mode_name}_tot"] / max_val, color="blue", ax=ax)
    ax.set_title(f"Delaunay assignment for {mode_name}")
    hide_axis_and_frame(ax)
    ax.set_frame_on(True)
    ax.patch.set_visible(True)
    return ax


def builds_delaunay(trips: pd.DataFrame, locations: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    geo_col = locations._geometry_column_name
    locs2 = locations.assign(x=locations[geo_col].x, y=locations[geo_col].y)
    centr_ = locs2.groupby("zone").agg({"x": "mean", "y": "mean"}).reset_index()
    geo = gpd.points_from_xy(centr_.x, centr_.y, crs=locations.crs)
    centroids = gpd.GeoDataFrame(centr_, geometry=geo)

    idx = np.empty(centroids.zone.max() + 1, dtype=int)
    idx[centroids.zone.values] = np.arange(centroids.shape[0])

    tot_trips = pd.DataFrame(trips.groupby(["zone_o", "zone_d", "mode"]).size())
    tot_trips.columns = ["trips"]
    tot_trips = tot_trips.reset_index()

    mat = AequilibraeMatrix()
    mat.create_empty(memory_only=True, zones=centroids.shape[0], matrix_names=list(tot_trips["mode"].unique()))
    mat.index[:] = centroids.zone.values

    for i, mode in enumerate(tot_trips["mode"].unique()):
        mode_trips = tot_trips[tot_trips["mode"] == mode]
        coo_ = coo_matrix(
            (mode_trips.trips.values,
             (idx[mode_trips.zone_o.values], idx[mode_trips.zone_d.values])),
            shape=(centroids.shape[0], centroids.shape[0])).todense()
        mat.matrices[:, :, i] = coo_
    mat.computational_view()

    return delaunay_procedure(centroids.rename(columns={"zone": "node_id"}), mat)
