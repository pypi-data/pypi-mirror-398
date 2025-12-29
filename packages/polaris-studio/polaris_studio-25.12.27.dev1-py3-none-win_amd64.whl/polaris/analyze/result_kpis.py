# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md

import logging
import re
import time
import traceback
from pathlib import Path
from shutil import rmtree
from typing import Tuple, Optional

import diskcache as dc  # type: ignore
import numpy as np
import pandas as pd
import psutil

from polaris.analyze.activity_metrics import ActivityMetrics
from polaris.analyze.kpi_utils import KPIFilter, kpi_type, KPITag, standard_kpis
from polaris.analyze.path_metrics import PathMetrics
from polaris.demand.demand import Demand
from polaris.runs.calibrate import (
    activity_generation,
    destination_choice,
    mode_choice,
    timing_choice,
    speed_by_funcl,
)
from polaris.runs.calibrate.utils import calculate_normalized_rmse
from polaris.runs.convergence.config.convergence_config import ConvergenceConfig
from polaris.runs.convergence.convergence_iteration import ConvergenceIteration
from polaris.runs.gap_reporting import load_gaps
from polaris.runs.polaris_inputs import PolarisInputs
from polaris.runs.polaris_version import parse_polaris_version
from polaris.runs.results.h5_results import H5_Results
from polaris.runs.scenario_compression import ScenarioCompression
from polaris.runs.summary import load_summary
from polaris.runs.validate import count_validation
from polaris.runs.wtf_runner import render_wtf_file, render_sql, sql_dir
from polaris.utils.database.db_utils import (
    attach_to_conn,
    commit_and_close,
    has_table,
    read_and_close,
    read_table,
    run_sql,
    load_link_types,
)
from polaris.utils.database.standard_database import DatabaseType
from polaris.utils.dict_utils import denest_dict
from polaris.utils.file_utils import readlines
from polaris.utils.optional_deps import check_dependency


class ResultKPIs:
    """
    This class provides an easy way to extract relevant metrics for a single simulation run of POLARIS.
    The easiest way to generate an instance is via the factory method `from_iteration` which takes the path to the
    outputs of a simulation run (or a :func:`~Polaris.runs.convergence.ConvergenceIteration`)

    ::

        from polaris.analyze.result_kpi import ResultKPIs

        kpis = ResultKPIs.from_iteration(ref_project_dir / f"{city}_iteration_2")

    Metric comparison plots can then be generated in a notebook using:

    ::

        results = KpiComparator()
        results.add_run(kpis, 'an-arbitrary-label')
        results.plot_mode_share()
        results.plot_vmt()
        results.plot_vmt_by_link_type()

    Any number of runs can be added using `add_run` up to the limit of readability on the generated plots.
    """

    result_time_step = 3600

    def __init__(
        self,
        inputs: PolarisInputs,
        cache_dir: Path,
        population_scale_factor: float,
        include_kpis: Tuple[KPITag, ...],
        exclude_kpis: Tuple[KPITag, ...] = (
            KPITag.HIGH_MEMORY,
            KPITag.BROKEN,
        ),
    ):
        self.cache = self._load_cache(cache_dir)
        self._cache_dir = cache_dir
        self.inputs = inputs
        self.population_scale_factor = population_scale_factor
        self.__trip_data = pd.DataFrame([])
        self.__activity_data = pd.DataFrame([])
        self.__path_data = pd.DataFrame([])
        self.kpi_filter = KPIFilter(include_kpis, exclude_kpis)

    @classmethod
    def from_iteration(cls, iteration: ConvergenceIteration, **kwargs):
        """Create a KPI object from a ConvergenceIteration object.

        :param iteration: Iteration object for which a KPI object is created
        """
        if iteration.output_dir is None or iteration.files is None:
            raise RuntimeError("Given iteration doesn't have a defined output dir")
        return cls.from_args(iteration.files, iteration.output_dir, **kwargs)

    @classmethod
    def from_dir(cls, iteration_dir: Path, **kwargs):
        """Create a KPI object from a given directory.

        :param iteration_dir: Iteration directory for which a KPI object is created
        """
        if "db_name" in kwargs:
            inputs = PolarisInputs.from_dir(iteration_dir, db_name=kwargs["db_name"])
            del kwargs["db_name"]
        else:
            inputs = PolarisInputs.from_dir(iteration_dir)
        return cls.from_args(inputs, iteration_dir, **kwargs)

    @classmethod
    def from_args(
        cls,
        files: PolarisInputs,
        iteration_dir: Path,
        cache_name: str = "kpi.cache",
        clear_cache=False,
        exit_if_no_cache=False,
        population_scale_factor=None,
        include_kpis: Tuple[KPITag, ...] = standard_kpis,
        exclude_kpis: Tuple[KPITag, ...] = (KPITag.HIGH_MEMORY, KPITag.BROKEN),
    ):
        """Create a KPI object using a detailed set of arguments."""
        cache_dir = Path(iteration_dir) / cache_name
        if cache_dir.exists() and clear_cache:
            rmtree(cache_dir)

        if population_scale_factor is None:
            population_scale_factor = ConvergenceConfig.from_dir(iteration_dir).population_scale_factor

        if not cache_dir.exists() and exit_if_no_cache:
            return None

        return cls(files, cache_dir, population_scale_factor, include_kpis=include_kpis, exclude_kpis=exclude_kpis)

    def _load_cache(self, cache_dir) -> Optional[dc.Cache]:
        """Load cached set of KPIs from the KPI cache directory

        :param cache_dir: Directory path for storing KPIs in a cache
        """
        if cache_dir is None:
            return None

        # make sure we never leave open connections to the cache lying around
        def create_and_close(cache_dir_):
            c = dc.Cache(cache_dir_)
            c.close()
            return c

        try:
            return create_and_close(cache_dir)
        except Exception:
            (Path(cache_dir) / "cache.db").unlink(missing_ok=True)
            return create_and_close(cache_dir)

    def cache_all_available_metrics(self, verbose=False, metrics_to_cache=None, skip_cache=False):
        """Cache available metrics into a KPI cache directory

        :param verbose: `Optional`, Enable verbose logging
        :param metrics_to_cache: `Optional`, A list of metrics to cache if not all available metrics
        :param skip_cache: `Optional`, Skip using the cache directory and generate metrics
        """
        metrics_to_cache = self.available_metrics() if metrics_to_cache is None else set(metrics_to_cache)
        metrics_to_cache = (m for m in metrics_to_cache if self.kpi_filter.allows(m))
        verbose and logging.info(f"Caching KPI metrics: {metrics_to_cache}")

        durations = {}
        for m in metrics_to_cache:
            start_time = time.time()
            try:
                verbose and logging.info(f"  => {m}")
                self.get_cached_kpi_value(m, skip_cache=skip_cache)
                memory_info = psutil.Process().memory_info()
                verbose and logging.info(f"     {memory_info.rss / (1024 ** 2):.2f} MB")
            except Exception:
                logging.warning(f"KPI failed: {m}")
                if verbose:
                    tb = traceback.format_exc()
                    print(tb, flush=True)
            durations[m] = round(time.time() - start_time, 1)
        self.cache.close()

        # Timing report
        timing_file = self._cache_dir / "cache_all_metric_timing.csv"
        logging.info(f"Saving precaching KPIs runtime report to {timing_file}")
        df = pd.DataFrame(data=list(durations.items()), columns=["metric name", "duration (s)"])
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(timing_file, index=False)

    @classmethod
    def available_metrics(self):
        """Return a dictionary of available metrics that can be computed"""
        return {e.replace("metric_", "") for e in dir(self) if e.startswith("metric_")}

    def close(self):
        """Close access to the KPI cache database"""
        self.cache.close()

    def get_kpi_value(self, kpi_name):
        """Compute a metric that is requested, if defined

        :param kpi_name: Name of the metric to be retrieved
        """
        attr_name = f"metric_{kpi_name}"
        if hasattr(self, attr_name) and callable(self.__getattribute__(attr_name)):
            return self.__getattribute__(attr_name)()
        raise RuntimeError(f"it seems we don't have a way to compute: {kpi_name}")

    def get_cached_kpi_value(self, kpi_name, skip_cache=False, force_cache=False):
        """Get the cached value of a metric

        :param kpi_name: Name of the metric to be retrieved
        :param skip_cache: `Optional`, skip cache and compute the metric before retrieval
        :param force_cache: `Optional`, force only the use of a stored value and skip if it does not exist
        """
        try:
            if self.cache is None:
                return self.get_kpi_value(kpi_name)

            def generate():
                logging.debug(f"Generating KPI value {kpi_name}")
                self.cache.set(kpi_name, self.get_kpi_value(kpi_name))

            if skip_cache:
                generate()
            elif kpi_name not in self.cache:
                if force_cache:
                    return None
                generate()

            return self.cache.get(kpi_name)
        finally:
            # Any time we read or write to the cache - we need to close it!
            self.cache.close()

    def has_cached_kpi(self, kpi_name):
        """Check if KPI is cached

        :param kpi_name: String name of metric to check if cached
        """
        try:
            return self.cache is not None and kpi_name in self.cache
        finally:
            # Any time we read or write to the cache - we need to close it!
            self.cache.close()

    def cached_metrics(self):
        """Obtain a set of cached metrics for the KPI object"""
        try:
            return set() if self.cache is None else set(self.cache.iterkeys())
        finally:
            # Any time we read or write to the cache - we need to close it!
            self.cache.close()

    @kpi_type(KPITag.SYSTEM)
    def metric_summary(self):
        """Metric that captures the summary of the iteration such as number of vehicles in network, run time, memory usage."""
        return load_summary(self.inputs.summary, raise_on_error=False)

    @kpi_type(KPITag.SYSTEM)
    def metric_file_sizes(self):
        """Metric provides the size of generated SQLite and H5 files"""
        iter_dir = self.inputs.result_h5.parent

        def f(pattern):
            files = list(iter_dir.glob(f"*{pattern}*"))
            if len(files) == 1:
                return (files[0].name, files[0].stat().st_size)
            logging.info(f"Can't find a file matching pattern: {pattern}")
            return None

        file_sizes = ["Supply.sqlite", "Demand.sqlite", "Result.sqlite", "Result.h5", "Freight.sqlite"]
        file_sizes = [f(e) for e in file_sizes]
        return pd.DataFrame([e for e in file_sizes if e], columns=["filename", "filesize"])

    @kpi_type(KPITag.SYSTEM)
    def metric_polaris_exe(self):
        """Metric provides the GIT branch, SHA, build date, and URL of the POLARIS executable used to generate the outputs"""
        log_head = readlines(self._cache_dir.parent / "log" / "polaris_progress.log", 30)
        branch, sha, build_date = parse_polaris_version("\n".join(log_head))
        url = f"https://git-out.gss.anl.gov/polaris/code/polaris-linux/-/commit/{sha}"
        return pd.DataFrame({"branch": [branch], "sha": [sha], "build_date": [build_date], "url": [url]})

    @kpi_type(KPITag.CONVERGENCE)
    def metric_gaps(self):
        """Metric provides the routing gaps from the run"""
        return load_gaps(self.inputs.gap)

    @staticmethod
    def one_value(conn, query, default=0):
        """Provide one value from a SQL query evaluated on a connection or return a default

        :param conn: SQLite connection to a database
        :param query: String SQL query to be evaluated
        :param default: `Optional`, default value returned if query evaluates to None
        """
        return conn.execute(query).fetchone()[0] or default

    @kpi_type(KPITag.POPULATION)
    def metric_population(self):
        """Metric provides population summary simulated"""
        columns = ["num_persons", "num_adults", "num_employed"]
        where_clauses = ["1==1", "person.age > 16", "work_location_id > 1"]
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            vals = [
                ResultKPIs.one_value(
                    conn, render_sql(f"SELECT count(*) FROM person WHERE {w};", self.population_scale_factor)
                )
                for w in where_clauses
            ]
            return pd.DataFrame([vals], columns=columns)

    @kpi_type(KPITag.POPULATION)
    def metric_num_persons_by_age_band_5(self):
        """Metric provides persons by age 5-year age bands"""
        return self._metric_num_persons_by_age_band_x(5)

    @kpi_type(KPITag.POPULATION)
    def metric_num_persons_by_age_band_10(self):
        """Metric provides persons by age 10-year age bands"""
        return self._metric_num_persons_by_age_band_x(10)

    def _metric_num_persons_by_age_band_x(self, x):
        query = f""" SELECT {x} * (person.age / {x}) as bucket, count(*) * scaling_factor as count
                     FROM person
                     GROUP BY (person.age / {x}); """
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            return pd.read_sql(render_sql(query, self.population_scale_factor), conn)

    @kpi_type((KPITag.POPULATION, KPITag.SCALAR))
    def metric_num_hh(self):
        """Metric provides number of households simulated in iteration"""
        query = """ SELECT count(*) * scaling_factor as num_hh
                    FROM household;"""
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            return conn.execute(render_sql(query, self.population_scale_factor)).fetchone()[0] or 0

    @kpi_type(KPITag.POPULATION)
    def metric_num_hh_by_hh_size(self):
        """Metric provides number of households by household size"""
        query = """ SELECT q.hh_size, count(*) * scaling_factor as num_hh
                     FROM (SELECT person.household, count(*) as hh_size
                           FROM person
                           GROUP BY person.household) as q
                     GROUP BY q.hh_size;"""
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            return pd.read_sql(render_sql(query, self.population_scale_factor), conn)

    @kpi_type((KPITag.TRIPS, KPITag.SCALAR))
    def metric_tts(self):
        """Metric provides total travel time for all trips in simulation"""
        # If Trip table is empty we return 0 as the execute.fetchone()[0] will return None
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            return conn.execute('SELECT SUM(end-start) from trip WHERE "end">"start"').fetchone()[0] or 0

    @kpi_type(KPITag.ACTIVITIES)
    def metric_distance_by_act_type(self):
        """Metric provides average trip distance by activity type"""
        query = """ SELECT activity.type as acttype, avg(trip.travel_distance)/1609.3 as dist_avg
                    FROM trip
                    JOIN person ON trip.person = person.person
                    JOIN household ON person.household = household.household
                    JOIN activity ON activity.trip = trip.trip_id
                    WHERE person.age > 16
                      AND trip.end - trip.start > 0
                      AND trip.end - trip.start < 10800
                    GROUP BY ACTTYPE; """
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            return pd.read_sql(query, conn)

    @kpi_type(KPITag.ACTIVITIES_PLANNED)
    def metric_planned_modes(self):
        """Metric provides summary of planned modes BEFORE dynamic traffic assignment"""
        query = """Select activity.mode, count(*) as mode_count
                   FROM activity
                            JOIN person ON activity.person = person.person
                   WHERE activity.start_time > 122
                     and activity.trip = 0
                     and person.age > 16
                   GROUP BY activity.mode"""
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            return pd.read_sql(query, conn)

    @kpi_type(KPITag.ACTIVITIES)
    def metric_executed_modes(self):
        """Metric provides summary of executed modes AFTER dynamic traffic assignment"""
        query = """Select activity.mode, count(*) as mode_count
                   FROM activity JOIN person ON activity.person = person.person
                   WHERE activity.start_time > 122 and activity.trip <> 0 and person.age > 16
                   GROUP BY activity.mode"""
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            return pd.read_sql(query, conn)

    @kpi_type(KPITag.TRIPS)
    def metric_mode_shares(self):
        """Metric provides the aggregate mode shares by trip purposes of HBW, HBO, NHB, and total"""
        df = self._add_mode_names(self._slow_fast(sql_dir / "mode_share.template.sql", "mode_distribution_adult"))

        cols = ["HBW", "HBO", "NHB", "total"]
        df[[f"{c}_pr" for c in cols]] = df[cols] / df[cols].sum()
        return df

    def _add_mode_names(self, df):
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            mode_lookup = Demand.load_modes(conn)
        df["mode"] = df["mode"].apply(lambda m: mode_lookup.get(m, f"{m}_Unknown"))
        return df

    @kpi_type(KPITag.ACTIVITIES)
    def metric_executed_activity_mode_share_by_income(self):
        """Metric provides the executed mode share by income quintiles"""
        sql = """
            Select
                income_quintile_fn as INCOME_QUINTILE,
                sum (case when activity.mode in (transit_modes) then 1.0 else 0.0 end)/(count(*) + 0.0) as transit_share,
                sum (case when activity.mode in ('TAXI') then 1.0 else 0.0 end)/(count(*) + 0.0) as tnc_share,
                sum (case when activity.mode in ('SOV', 'HOV') then 1.0 else 0.0 end)/(count(*) + 0.0) as auto_share,
                sum (case when activity.mode in ('WALK', 'BIKE') then 1.0 else 0.0 end)/(count(*) + 0.0) as active_share,
                sum (case when activity.mode not in (transit_modes, 'TAXI', 'SOV', 'HOV', 'WALK', 'BIKE') then 1.0 else 0.0 end)/(count(*) + 0.0) as other_share
            FROM
                activity, person, trip, household
            WHERE
                activity.start_time > 122 and
                activity.trip = trip.trip_id and
                trip."end" - trip."start" > 2 and
                activity.person = person.person and
                person.household = household.household and
                activity.mode not like 'FAIL%'
            GROUP BY
                INCOME_QUINTILE;
        """
        return self._slow_fast(sql, "executed_activity_mode_share_by_income")

    @kpi_type(KPITag.ACTIVITIES)
    def metric_activity_start_distribution(self):
        """Metric provides the activity start distribution of all activity purposes in the simulation"""
        return self._slow_fast(sql_dir / "activity_start_distribution.template.sql", "Activity_Start_Distribution")

    @kpi_type(KPITag.ACTIVITIES)
    def metric_activity_rate_distribution(self):
        """Metric provides the activity rate distribution of all activity purposes in the simulation"""
        return self._slow_fast(sql_dir / "activity_distribution.template.sql", "activity_rate_distribution")

    @kpi_type(KPITag.ACTIVITIES)
    def metric_activity_duration_distribution(self):
        """Metric provides the activity duration distribution for all activity purposes in the simulation"""
        sql = """
            SELECT
                type as act_type,
                cast(start_time/3600 as int) as start_time,
                avg(duration) as average_duration,
                scaling_factor * count(*) as num_activities
            FROM Activity
            WHERE start_time > 122 and trip <> 0
            GROUP BY 1,2;
        """
        return self._slow_fast(sql, "Activity_Duration_Distribution")

    @kpi_type(KPITag.TRAFFIC)
    def metric_vmt_vht(self):
        """Metric provides the aggregate vehicle miles traveled (VMT), vehicle hours traveled (VHT), average speed, and count by all modes in simulation"""
        sql_slow = """
            SELECT mode, type,
                   scaling_factor*sum(travel_distance)/1609.3/1000000.0 as million_VMT,
                   scaling_factor*sum(end-start-access_egress_ovtt)/3600.0/1000000.0 as million_VHT,
                   sum(travel_distance)/1609.3 / (sum(end-start-access_egress_ovtt)/3600.0) as speed_mph,
                   scaling_factor*count(*) as count
            FROM trip
            WHERE "end" > "start"
            AND (
                    (mode IN (0,9) AND has_artificial_trip <> 1)  -- skip stuck auto trips
                 OR (mode NOT IN (0,9))                           -- non-auto modes
            )
            GROUP BY 1,2;
        """
        return self._add_mode_names(self._slow_fast(sql_slow, "vmt_vht_by_mode_type")).set_index(["mode", "type"])

    @kpi_type(KPITag.VEHICLES)
    def metric_autoai_energy(self):
        """Metric provides the energy use and emissions if Autonomie AI was run on KPI object"""
        autoai_file = self.inputs.result_h5.parent / "autoai" / "emissions.csv"
        if not autoai_file.exists():
            logging.warning("Autonomi AI not run for this folder")
            return
        df = pd.read_csv(autoai_file)

        heating_values = {"elec": 0, "conv": 43.05, "hev": 43.05, "isg": 43.05, "h2": 120}

        if "H2_heating_value" not in df.columns:
            df["H2_heating_value"] = df.pwt.map(heating_values).fillna(0)

        df["fuel_MJ"] = df.fuel_mass / 1e3 * df.H2_heating_value
        df["electric_consumption_MJ"] = df.electric_consumption / 1e6
        df["total_energy_MJ"] = df["fuel_MJ"] + df["electric_consumption_MJ"]
        df = df.groupby(["clazz", "pwt"]).agg(
            {
                "electric_consumption_MJ": "sum",
                "fuel_MJ": "sum",
                "total_energy_MJ": "sum",
                "GHGs_WTW": "sum",  # do not use yet
                "CO2_WTP": "sum",  # do not use yet
                "CO2_PTW": "sum",  # do not use yet
                "CO2_WTW": "sum",  # do not use yet
                "N2O_WTP": "sum",  # do not use yet
                "N2O_PTW": "sum",  # do not use yet
                "N2O_WTW": "sum",  # do not use yet
            }
        )
        return df

    @kpi_type(KPITag.VEHICLES)
    def metric_ev_charging(self):
        """Metric provides an aggregate summary of electric vehicle (EV) charging such as energy, waiting time, charging time, cost of charging,
        and number of charging events by EV type, charging station type, and whether residential charging was available
        """
        query = """
            WITH Aggregation AS (
                SELECT
                    charging_fleet_type,
                    charging_station_type,
                    has_residential_charging,
                    SUM((energy_out_wh - energy_in_wh) * scaling_factor) AS total_energy_charged_wh,
                    SUM((time_start - time_in) * scaling_factor) AS total_waiting_time_s,
                    SUM((time_out - time_start) * scaling_factor) AS total_charging_time_s,
                    SUM(CASE WHEN charged_money > 0 THEN charged_money * scaling_factor ELSE 0 END) as total_charged_dollars,
                    SUM(CASE WHEN charged_money > 0 THEN (energy_out_wh - energy_in_wh) * scaling_factor ELSE 0 END) as total_energy_charged_wh_for_cost,
                    COUNT(station_id) * scaling_factor AS number_of_charging_events
                FROM
                    EV_Charging
                WHERE
                    time_start < time_out
                    AND energy_in_wh < energy_out_wh
                GROUP BY 1,2,3
            )
            SELECT
                charging_fleet_type,
                charging_station_type,
                has_residential_charging,
                number_of_charging_events,
                total_energy_charged_wh,
                total_waiting_time_s,
                total_charging_time_s,
                total_charged_dollars,
                (total_energy_charged_wh / NULLIF(number_of_charging_events, 0)) / 1000.0 AS average_energy_charged_kwh,
                (total_waiting_time_s / NULLIF(number_of_charging_events, 0)) / 60.0 AS average_waiting_time_min,
                (total_charging_time_s / NULLIF(number_of_charging_events, 0)) / 60.0 AS average_charging_time_min,
                (total_charged_dollars * 1000.0 / NULLIF(total_energy_charged_wh_for_cost, 0)) AS averaged_paid_dollars_per_kWh,
                (total_energy_charged_wh / NULLIF(total_charging_time_s, 0)) * 3600.0 AS rate_w
            FROM
                Aggregation;
        """

        return self._slow_fast(query, "ev_charge_summary")

    @kpi_type(KPITag.VEHICLES)
    def metric_ev_consumption(self):
        """Metric provides electric vehicle (EV) consumption while in operation such as distance, energy used, and average Wh per mile by trip mode"""
        query = """SELECT
                m.mode_description as mode,
                t.type as "type",
                scaling_factor * sum(t.travel_distance/1609.3) AS distance_mile,
                scaling_factor * sum(t.initial_energy_level - t.final_energy_level) AS total_energy_Wh,
                sum(t.initial_energy_level - t.final_energy_level) / sum(t.travel_distance/1609.3) as Wh_per_mile
            FROM
                trip t
                JOIN vehicle x ON x.vehicle_id = t.vehicle
                JOIN Vehicle_Type v ON x.type = v.type_id
                JOIN fuel_type f ON v.fuel_type = f.type_id
                JOIN ev_features ev ON v.ev_features_id = ev.ev_features_id
                JOIN mode m ON t.mode = m.mode_id
            WHERE
                t.mode in (0,17,18,19,20)
                AND f.type = 'Elec'
            group by
                t.mode, t.type
            UNION
            SELECT
                m.mode_description as mode,
                t.type as "type",
                scaling_factor * sum(t.travel_distance/1609.3) AS distance_mile,
                scaling_factor * sum((ev.veh_ess_energy * t.init_battery / 100.0) - (ev.veh_ess_energy * t.final_battery / 100.0)) AS total_energy_Wh,
                sum((ev.veh_ess_energy * t.init_battery / 100.0) - (ev.veh_ess_energy * t.final_battery / 100.0)) / sum(t.travel_distance/1609.3) as Wh_per_mile
            FROM tnc_trip t
                JOIN vehicle x ON x.vehicle_id = t.vehicle
                JOIN Vehicle_Type v ON x.type = v.type_id
                JOIN fuel_type f ON v.fuel_type = f.type_id
                JOIN ev_features ev ON v.ev_features_id = ev.ev_features_id
                JOIN mode m ON t.mode = m.mode_id
            WHERE
                f.type = 'Elec'
            group by
                t.mode, t.type;
        """

        return self._slow_fast(query, "ev_consumption_summary")

    @kpi_type(KPITag.VEHICLES)
    def metric_fuel_consumption(self):
        """Metric provides energy use by fuel type, powertrain type, mode, automation level, and vintage level, along
        with total travel distance and number of trips recorded for the associated energy use"""
        demand_db = self.inputs.demand_db
        autoai_dir = demand_db.parent / "autoai"
        if not (autoai_dir / "emissions.csv").exists() and not (autoai_dir / "emissions.parquet").exists():
            logging.warning("No AutoAI emissions file to process")
            return None

        if (autoai_dir / "consumption_polaris.parquet").exists():
            df = pd.read_parquet(autoai_dir / "consumption_polaris.parquet")
        else:
            df = pd.read_csv(autoai_dir / "consumption_polaris.csv")
        logging.info(f"read {len(df)} trip consumption records from AutoAI")

        shape_before = df.shape
        df = df.drop_duplicates(subset=["trip_id"])
        if shape_before != df.shape:
            logging.warning(f"dropping duplicates from AutoAI emissions file: {shape_before} -> {df.shape}")

        # trip_id,vehicle_type,num_points,clazz,pwt,fuel_mass,electric_consumption
        if "travel_distance" not in df.columns or "mode" not in df.columns:
            with read_and_close(ScenarioCompression.maybe_extract(demand_db)) as conn:
                trip_df = pd.read_sql("SELECT path, travel_distance, mode FROM trip", conn)
                logging.info(f"read {len(trip_df)} trip records from database")
                df = df.merge(trip_df, left_on="trip_id", right_on="path", how="left")
                shape_before = df.shape
                df = df[df.path.notna()]
                if shape_before != df.shape:
                    logging.warning(f"dropping rows due to no path ID match in trips: {shape_before} -> {df.shape}")

        vehicle_types = ResultKPIs.vehicle_attributes(demand_db)
        df = df.merge(vehicle_types, left_on="vehicle_type", right_on="type_id", how="left")
        logging.info(f"merged to {len(df)} trip records after joining vehicle and trip data")

        df["num_trips"] = 1
        print(df["mode"].unique())
        mode_strings = {0: "SOV", 17: "MDT", 18: "HDT", 19: "BPlace", 20: "LDT"}
        key_cols = ["fuel_type", "powertrain_type", "mode", "automation_level", "vintage_level"]
        cols = ["fuel_mass", "electric_consumption", "travel_distance", "num_trips"]
        df[key_cols] = df[key_cols].astype("category")
        df = df.groupby(key_cols, observed=True, sort=False)[cols].sum().reset_index()
        df["mode"] = df["mode"].map(mode_strings)
        df[key_cols] = df[key_cols].astype(str)
        return df

    @classmethod
    def vehicle_attributes(cls, demand_db):
        sql = """
            SELECT vt.type_id, vc.class_type, pt.type as powertrain_type, ft.type as fuel_type,
                   vg.type as vintage_level, at.type as automation_level
            FROM vehicle_type vt
            JOIN vehicle_class vc ON vc.class_id = vt.vehicle_class
            JOIN powertrain_type pt ON pt.type_id = vt.powertrain_type
            JOIN fuel_type ft ON ft.type_id = vt.fuel_type
            JOIN vintage_type vg ON vg.type_id = vt.vintage_type
            JOIN automation_type at ON at.type_id = vt.automation_type
        """
        with read_and_close(ScenarioCompression.maybe_extract(demand_db)) as conn:
            return pd.read_sql(sql, conn)

    @kpi_type(KPITag.TRAFFIC)
    def metric_vmt_vht_by_link(self):
        """Metric provides the vehicle miles traveled (VMT), vehicle hours traveled (VHT), and average speed in AM, PM, and Off-Peak periods by link type"""
        if not self.inputs.result_h5.exists():
            logging.warning("No H5 file to process")
            return

        h5_results = H5_Results(ScenarioCompression.maybe_extract(self.inputs.result_h5))
        vmt_vht = h5_results.get_vmt_vht(self.population_scale_factor)

        # Add link type from the supply database for easier grouping later
        vmt_vht["link"] = vmt_vht.index // 2
        vmt_vht = vmt_vht.join(load_link_types(self.inputs.supply_db), on="link").drop(columns=["link"])

        return vmt_vht

    @kpi_type(KPITag.TRAFFIC)
    def metric_flow_density_fd(self):
        """Metric provides the fundamental diagram by link types in the simulation"""
        if not self.inputs.result_h5.exists():
            logging.warning("No H5 file to process")
            return

        h5_results = H5_Results(ScenarioCompression.maybe_extract(self.inputs.result_h5))
        df = h5_results.get_flow_density().reset_index()

        # Add link type column
        df["link"] = df.index // 2
        df = df.join(load_link_types(self.inputs.supply_db), on="link").drop(columns=["link"])

        df_dens = df.melt(
            id_vars=["uuid", "type"],
            value_name="density",
            var_name="time_step",
            value_vars=[x for x in df.columns if "density" in x],
        )
        df_dens.time_step = df_dens.time_step.str.replace("density_", "")

        df_flow = df.melt(
            id_vars=["uuid"],
            value_name="flow",
            var_name="time_step",
            value_vars=[x for x in df.columns if "flow" in x],
        )
        df_flow.time_step = df_flow.time_step.str.replace("flow_", "")

        df_merge = pd.merge(left=df_dens, right=df_flow, on=["uuid", "time_step"])
        # Drop NA to be removed after fixing h5
        df_merge = df_merge.replace(np.inf, np.nan).dropna()
        df_merge["density_bin"] = (df_merge.density / 0.1).astype(int) * 0.1
        df_fd = df_merge.groupby(["type", "density_bin"], observed=False).agg({"flow": "max"})
        df_fd = df_fd.reset_index()

        return df_fd

    @kpi_type(KPITag.ACTIVITIES)
    def metric_activity_distances(self):
        """Metric provides activity distances and travel times by activity type"""
        return self._slow_fast(
            sql_dir / "travel_time.template.sql", "ttime_By_ACT_Average", attach_db_type=DatabaseType.Supply
        )

    @kpi_type(KPITag.VEHICLES)
    def metric_vehicle_technology(self, **kwargs):
        """Metric provides the summary of vehicle technology owned by various POLARIS agents (such as households, freight operators, TNC, and transit)"""
        sql = """
            SELECT (CASE WHEN v.hhold > 0 THEN 1                          ELSE v.hhold END) AS agent_type,
                   (CASE WHEN v.hhold > 0 THEN h.has_residential_Charging ELSE -1      END) AS Has_Residential_Charging,
                   vc.class_type,
                   ct.type as connected,
                   at.type as automation_level,
                   pt.type as powertrain_type,
                   ft.type as fuel_type,
                   vtg.type as vintage_level,
                   vt.ev_features_id,
                   vt.operating_cost_per_mile,
                   scaling_factor * count(*) as veh_count
            from vehicle v
            LEFT JOIN vehicle_type vt      ON v.type = vt.type_id
            LEFT JOIN vehicle_class vc     ON vc.class_id = vt.vehicle_class
            LEFT JOIN connectivity_type ct ON ct.type_id = vt.connectivity_type
            LEFT JOIN automation_type at   ON at.type_id = vt.automation_type
            LEFT JOIN powertrain_type pt   ON pt.type_id = vt.powertrain_type
            LEFT JOIN fuel_type ft         ON ft.type_id = vt.fuel_type
            LEFT JOIN vintage_type vtg     ON vtg.type_id = vt.vintage_type
            LEFT JOIN household h          ON v.hhold = h.household
            GROUP BY 1,2,vt.type_id;
        """
        return self._slow_fast(sql, "vehicle_technology", **kwargs)

    def _slow_fast(self, slow_sql, table_name, db_type=DatabaseType.Demand, attach_db_type=None, skip_cache=False):
        """Utility method to read analytics data from table. Uses slow query to create it if table doesn't exist."""
        with commit_and_close(ScenarioCompression.maybe_extract(self._get_db(db_type))) as conn:
            if has_table(conn, table_name):
                if not skip_cache:
                    return pd.read_sql(sql=f"SELECT * FROM {table_name};", con=conn)
                conn.execute(f"DROP TABLE {table_name};")

            if attach_db_type is not None:
                attach_to_conn(conn, {"a": ScenarioCompression.maybe_extract(self._get_db(attach_db_type))})

            # If the given input is a path to a template file, or a create table statement, just run it
            if isinstance(slow_sql, Path):
                run_sql(render_wtf_file(slow_sql, self.population_scale_factor), conn)
            elif re.match("create table", slow_sql.lower()):
                run_sql(render_sql(slow_sql, self.population_scale_factor), conn)
            else:
                # Otherwise wrap it up into a create table to cache the result
                conn.execute(f"CREATE TABLE {table_name} AS {render_sql(slow_sql, self.population_scale_factor)}")
            return pd.read_sql(sql=f"SELECT * FROM {table_name};", con=conn)

    def _get_db(self, db_type: DatabaseType):
        """Utility to obtain the appropriate file by db_type

        :param db_type: Type of database to obtain database path
        """
        if db_type == DatabaseType.Demand:
            return self.inputs.demand_db
        if db_type == DatabaseType.Supply:
            return self.inputs.supply_db
        if db_type == DatabaseType.Results:
            return self.inputs.result_db
        if db_type == DatabaseType.Freight:
            return self.inputs.freight_db

    @kpi_type(KPITag.TNC)
    def metric_tnc_request_stats(self):
        """Metric provides a summary of all TNC requests made during simulation such as time to assign, pickup time,
        dropoff time, travel time, travel distance group by TNC operators, service modes such as TAXI and First-Mile-Last-Mile (FMLM), and assignment status
        """
        return self._slow_fast(sql_dir / "tnc.template.sql", "tnc_request_stats")

    @kpi_type(KPITag.TNC)
    def metric_tnc_trip_stats(self):
        """Metric provides a summary of all TNC vehicle trips made during simulation such as vehicle miles traveled (VMT), vehicle hours traveled (VHT)
        and grouped by TNC operator, various legs of operation (pickup, dropoff, charging), and whether vehicle was occupied or unoccupied
        """
        return self._slow_fast(sql_dir / "tnc.template.sql", "tnc_trip_stats")

    @kpi_type(KPITag.TNC)
    def metric_tnc_stats(self):
        """Metric provides the aggregate TNC operator level stats such as trips served, revenue, charging trips by operator"""
        return self._slow_fast(sql_dir / "on_result" / "tnc.template.sql", "tnc_stats", DatabaseType.Results)

    @kpi_type(KPITag.TNC)
    def metric_avo_by_tnc_operator(self):
        """Metric provides the average vehicle occupancy (AVO) achieved by each TNC oeprator when serving the demand in simulation"""
        return self._slow_fast(sql_dir / "tnc.template.sql", "avo_by_tnc_operator")

    @kpi_type(KPITag.TRAFFIC)
    def metric_road_pricing(self):
        """Metric provides the tolls collected from various vehicle sources (such as personally-owned, TNC, freight)"""
        return self._slow_fast(sql_dir / "wtf_baseline_analysis.template.sql", "toll_revenue")

    @kpi_type(KPITag.TRANSIT)
    def metric_transit_boardings(self):
        """Metric provides the boardings and alightings by each transit agency and GTFS mode (such as bus, rail, metro, etc.)"""
        sql_slow = """
            SELECT
                ta.agency as agency,
                transit_mode_fn as "mode",
                scaling_factor*sum(tvl.value_boardings) as boardings,
                scaling_factor*sum(tvl.value_alightings) as alightings
            FROM
                "Transit_Vehicle_links" tvl,
                transit_vehicle tv,
                a.transit_trips tt,
                a.transit_patterns tp,
                a.transit_routes tr,
                a.transit_agencies ta
            where
                tvl.value_transit_vehicle_trip = tv.transit_vehicle_trip and
                tvl.value_transit_vehicle_trip = tt.trip_id and
                tp.pattern_id = tt.pattern_id and
                tr.route_id = tp.route_id AND
                tr.agency_id = ta.agency_id
            group by
                ta.agency,
                tv.mode
            order by
                ta.agency,
                tv.mode desc
            ;
        """
        return self._slow_fast(sql_slow, "boardings_by_agency_mode", attach_db_type=DatabaseType.Supply)

    @kpi_type(KPITag.TRANSIT)
    def metric_transit_experience(self):
        """Metric provides the aggregate transit experience as processed from multimodal paths in the simulation to provide travel time, transfers, walk time, bike time, cost, etc."""
        paths = H5_Results(self.inputs.result_h5).get_mm_paths()
        paths["wait_time"] = paths.actual_bus_wait_time + paths.actual_rail_wait_time + paths.actual_comm_rail_wait_time
        paths["ivtt"] = paths.actual_bus_ivtt + paths.actual_rail_ivtt + paths.actual_comm_rail_ivtt
        df = paths.groupby("mode").agg(
            {
                "timestep": "count",
                "actual_duration": "mean",
                "actual_wait_count": "mean",
                "actual_tnc_wait_count": "mean",
                "wait_time": "mean",
                "actual_tnc_wait_time": "mean",
                "ivtt": "mean",
                "actual_walk_time": "mean",
                "actual_bike_time": "mean",
                "actual_car_time": "mean",
                "actual_monetary_cost": "mean",
            }
        )
        renames = {k: k.replace("actual_", "") for k in df.columns if k.startswith("actual_")}
        df = df.rename(columns={"timestep": "count"} | renames)
        return df.reset_index()

    def network_gaps_by_x(self, x):
        """Utility function used by metrics to aggregate network gaps by x

        :param x: aggregation criteria such as 'link_type' or 'hour'
        """
        dfs = []
        h5_results = H5_Results(ScenarioCompression.maybe_extract(self.inputs.result_h5))
        link_attrs = read_table("link", ScenarioCompression.maybe_extract(self.inputs.supply_db))
        link_attrs = link_attrs[["link", "length", "type"]]
        link_attrs["total_dist"] = link_attrs["length"] / 1609.0
        link_attrs = link_attrs.rename(columns={"type": "link_type"})

        for t in h5_results.timesteps:
            df = h5_results.get_path_links_for_timestep(t)
            df = df[df["travel_time"] > 0]
            df["tt_diff"] = df.travel_time - df.routed_travel_time
            df["tt_diff_abs"] = abs(df.travel_time - df.routed_travel_time)
            df["hour"] = (df["entering_time"] / 3600).astype(int)
            df = df[["hour", "link_id", "routed_travel_time", "tt_diff", "tt_diff_abs"]]
            df = pd.merge(df, link_attrs, left_on="link_id", right_on="link")

            df = df[[x, "total_dist", "routed_travel_time", "tt_diff", "tt_diff_abs"]]
            df = df.groupby(x).sum().reset_index()
            dfs.append(df)

        df = pd.concat(dfs).groupby(x).sum().reset_index()
        df["abs_gap"] = df["tt_diff_abs"] / df["routed_travel_time"]
        df["gap"] = df["tt_diff"] / df["routed_travel_time"]
        df = df[[x, "total_dist", "abs_gap", "gap"]]
        return df.sort_values(by=x, axis=0)

    @kpi_type(KPITag.CONVERGENCE)
    def metric_network_gaps_by_link_type(self):
        """Metric provides the network gaps from routing aggregated by link type"""
        return self.network_gaps_by_x("link_type")

    @kpi_type(KPITag.CONVERGENCE)
    def metric_network_gaps_by_hour(self):
        """Metric provides the network gaps from routing aggregated by time of day (in hours)"""
        return self.network_gaps_by_x("hour")

    @kpi_type((KPITag.SKIMS, KPITag.HIGH_MEMORY))
    def metric_skim_stats(self):
        """Metric provides the skim statistics for highway and transit skims generated in the iteration such as min, max, and average travel time, cost, etc."""
        check_dependency("openmatrix")
        from polaris.skims.highway.highway_skim import HighwaySkim
        from polaris.skims.transit.transit_skim import TransitSkim

        hwy_skim = HighwaySkim.from_file(self.inputs.highway_skim)
        pt_skim_file = self.inputs.transit_skim
        if not pt_skim_file.exists():
            logging.debug(f"Skipping Transit skim metrics as file ({pt_skim_file}) not found")
            pt_skim = None
        else:
            pt_skim = TransitSkim.from_file(pt_skim_file)

        def f(skims, mode, interval, metric):
            mat = skims.get_skims(metric=metric, mode=mode, interval=interval)
            isfinite_mask = np.isfinite(mat)
            return {
                "interval": interval,
                "metric": metric,
                "mode": mode,
                "min": np.nanmin(mat[(mat > 0) & isfinite_mask], initial=0),
                "max": np.nanmax(mat[isfinite_mask], initial=10000),
                "avg": np.nanmean(mat[isfinite_mask]),
                # "std": mat[isfinite_mask].std(initial=10000),
            }

        df = pd.DataFrame([f(hwy_skim, "Auto", i, j) for i in hwy_skim.intervals for j in ["time", "distance"]])
        if pt_skim is None:
            return df

        df_transit = pd.DataFrame(
            [f(pt_skim, m, i, j) for i in pt_skim.intervals for j in ["time"] for m in ["Bus", "Rail"]]
        )
        return pd.concat([df, df_transit])

    @kpi_type(KPITag.VALIDATION)
    def metric_count_validation(self):
        """Metric provides the data comparing simulation link counts to those observed in data"""
        targets_dir = self._get_target_dir()
        target, periods = count_validation.load_targets(targets_dir / "link_volume_targets.csv")
        if target is None:
            return None
        simulated = count_validation.load_simulated(self.inputs.result_h5, self.population_scale_factor, periods)
        link_attrs = read_table("link", ScenarioCompression.maybe_extract(self.inputs.supply_db))
        df = link_attrs.set_index("link")[["type"]]
        return df.join(target).join(simulated).reset_index()

    def _get_target_dir(self):
        targets_dir = ConvergenceConfig.from_dir(self.inputs.demand_db.parent).calibration.target_csv_dir
        if not targets_dir.exists():
            logging.warning(f"No calibration targets found {targets_dir}")
            return None
        return targets_dir

    def _get_simulated_and_target_dict(self, target_type: str, use_planned=False, **kwargs):
        targets_dir = self._get_target_dir()

        if target_type == "activity_generation":
            simulated = activity_generation.load_simulated(self.inputs.demand_db, use_planned)
            target = activity_generation.load_target(targets_dir / "activity_generation_targets.csv")
        elif target_type == "mode_choice":
            simulated = mode_choice.load_simulated(self.inputs, self.population_scale_factor, use_planned)
            target = mode_choice.load_targets(targets_dir / "mode_choice_targets.csv", remove_transit=False)
        elif target_type == "destination_choice":
            data_type = kwargs.get("data_type", "distance")
            simulated = destination_choice.load_simulated(
                self.inputs.demand_db, self.inputs.supply_db, data_type=data_type
            )
            target = destination_choice.load_target(targets_dir / "destination_choice_targets.csv", data_type=data_type)
        elif target_type == "mode_choice_boardings":
            target_file = targets_dir / "mode_choice_boarding_targets.csv"
            if not target_file.exists():
                return None, None
            simulated = mode_choice.load_simulated_boardings(self.inputs, self.population_scale_factor)
            target = mode_choice.load_target_boardings(target_file)
        elif target_type == "timing":
            simulated = timing_choice.load_simulated(self.inputs, self.population_scale_factor, use_planned)
            target = timing_choice.load_target(targets_dir / "timing_choice_targets.csv")
        elif target_type == "speed_by_funcl":
            simulated = speed_by_funcl.load_simulated(self.inputs, self.population_scale_factor)
            target = speed_by_funcl.load_target(targets_dir / "speed_by_funcl_targets.csv")
        else:
            logging.error(f"Calibration targets not implemented for {target_type}")

        return simulated, target

    @kpi_type(KPITag.VALIDATION)
    def metric_rmse_vs_observed(self):
        """Metric provides the root mean squared errors for calibration procedures such as activity, mode, boardings, trip distance, and trip start time"""
        columns = ["RMSE_activity", "RMSE_mode", "RMSE_mode_boardings", "RMSE_destination", "RMSE_timing"]

        if self._get_target_dir() is None:
            return pd.DataFrame(data=[[-1, -1, -1, -1, -1]], columns=columns)

        simulated, target = self._get_simulated_and_target_dict("activity_generation")
        rmse_activity = calculate_normalized_rmse({k: r for k, (r, _) in simulated.items()}, target)

        simulated, target = self._get_simulated_and_target_dict("destination_choice")
        rmse_destination = calculate_normalized_rmse(simulated, target)

        simulated, target = self._get_simulated_and_target_dict("mode_choice")
        rmse_mode = calculate_normalized_rmse(denest_dict(simulated), denest_dict(target))

        simulated, target = self._get_simulated_and_target_dict("mode_choice_boardings")
        rmse_boardings = calculate_normalized_rmse(simulated, target)

        simulated, target = self._get_simulated_and_target_dict("timing")
        rmse_timing = calculate_normalized_rmse(denest_dict(simulated), denest_dict(target))

        return pd.DataFrame(
            data=[[rmse_activity, rmse_mode, rmse_boardings, rmse_destination, rmse_timing]], columns=columns
        )

    @kpi_type(KPITag.ACTIVITIES_PLANNED)
    def metric_planned_rmse_vs_observed(self):
        """Metric provides the root mean squared error for calibration procedures between planned and executed values of activity counts, mode shares, and trip start time choice"""
        columns = ["RMSE_activity", "RMSE_mode", "RMSE_timing"]

        if self._get_target_dir() is None:
            return pd.DataFrame(data=[[-1, -1, -1]], columns=columns)

        simulated, target = self._get_simulated_and_target_dict("activity_generation", use_planned=True)
        rmse_activity = calculate_normalized_rmse({k: r for k, (r, _) in simulated.items()}, target)

        simulated, target = self._get_simulated_and_target_dict("mode_choice", use_planned=True)
        rmse_mode = calculate_normalized_rmse(denest_dict(simulated), denest_dict(target))

        simulated, target = self._get_simulated_and_target_dict("timing", use_planned=True)
        rmse_timing = calculate_normalized_rmse(denest_dict(simulated), denest_dict(target))

        return pd.DataFrame(data=[[rmse_activity, rmse_mode, rmse_timing]], columns=columns)

    @kpi_type(KPITag.CALIBRATION)
    def metric_calibration_act_gen(self):
        """Metric provides calibration comparison between simulated activities and target activities by person type and activity type"""
        columns = ["pertype", "acttype", "target", "simulated", "per_count"]

        if self._get_target_dir() is None:
            return

        simulated, target = self._get_simulated_and_target_dict("activity_generation")

        keys = set.intersection(set(target.keys()), set(simulated.keys()))
        act_gen_df = pd.DataFrame([(key[0], key[1], target[key], *simulated[key]) for key in keys], columns=columns)
        act_gen_df.set_index(["pertype", "acttype"], inplace=True)

        return act_gen_df

    @kpi_type(KPITag.ACTIVITIES_PLANNED)
    def metric_calibration_act_gen_planned(self):
        """Metric provides calibration comparison between planned number of activities and target activities by person type and activity type - primarily used for debugging"""
        columns = ["pertype", "acttype", "simulated", "target", "per_count"]

        if self._get_target_dir() is None:
            return

        simulated, target = self._get_simulated_and_target_dict("activity_generation", use_planned=True)

        keys = set.intersection(set(target.keys()), set(simulated.keys()))
        act_gen_df = pd.DataFrame([(key[0], key[1], target[key], *simulated[key]) for key in keys], columns=columns)
        act_gen_df.set_index(["pertype", "acttype"], inplace=True)

        return act_gen_df

    @kpi_type(KPITag.CALIBRATION)
    def metric_calibration_mode_share(self):
        """Metric provides calibration comparison of executed mode shares by trip purpose in simulation and target for the region"""
        columns = ["type", "mode", "simulated", "target"]
        if self._get_target_dir() is None:
            return

        simulated, target = self._get_simulated_and_target_dict("mode_choice")

        mode_choice_df = pd.DataFrame(columns=columns)
        for key_type in set.intersection(set(target.keys()), set(simulated.keys())):
            for key_mode in set.intersection(set(target[key_type].keys()), set(simulated[key_type].keys())):
                mode_choice_df.loc[len(mode_choice_df.index)] = [
                    key_type,
                    key_mode,
                    simulated[key_type][key_mode],
                    target[key_type][key_mode],
                ]

        # Rebalance the shares so that they add to 1.0 for the run_id
        # It may not be 1 because maybe the target file may have split "TRANSIT" into "BUS" and "RAIL" but the
        # simulated as implemented here only has "TRANSIT"
        value_cols = ["simulated", "target"]
        mode_choice_df[value_cols] /= mode_choice_df.groupby("type")[value_cols].transform("sum")

        return mode_choice_df

    @kpi_type(KPITag.ACTIVITIES_PLANNED)
    def metric_calibration_mode_share_planned(self):
        """Metric provides calibration comparison of planned mode shares by trip purpose in simulation and target for the region"""
        columns = ["type", "mode", "simulated", "target"]
        if self._get_target_dir() is None:
            return

        simulated, target = self._get_simulated_and_target_dict("mode_choice", use_planned=True)

        mode_choice_df = pd.DataFrame(columns=columns)
        for key_type in set.intersection(set(target.keys()), set(simulated.keys())):
            for key_mode in set.intersection(set(target[key_type].keys()), set(simulated[key_type].keys())):
                mode_choice_df.loc[len(mode_choice_df.index)] = [
                    key_type,
                    key_mode,
                    simulated[key_type][key_mode],
                    target[key_type][key_mode],
                ]

        return mode_choice_df

    @kpi_type(KPITag.CALIBRATION)
    def metric_calibration_timing(self):
        """Metric provides calibration comparison of trip start times by activity purposein simulation and target for the region"""
        columns = ["act_type", "period", "target", "simulated"]
        if self._get_target_dir() is None:
            return

        simulated, target = self._get_simulated_and_target_dict("timing")

        timing_df = pd.DataFrame(columns=columns)
        for key_type in set.intersection(set(target.keys()), set(simulated.keys())):
            for key_period in set.intersection(set(target[key_type].keys()), set(simulated[key_type].keys())):
                timing_df.loc[len(timing_df.index)] = [
                    key_type,
                    key_period,
                    target[key_type][key_period],
                    simulated[key_type][key_period],
                ]

        return timing_df

    @kpi_type(KPITag.ACTIVITIES_PLANNED)
    def metric_calibration_timing_planned(self):
        """Metric provides calibration comparison of planned trip start times by activity purpose in simulation and target for the region - primarily used for debugging"""
        columns = ["act_type", "period", "target", "simulated"]
        if self._get_target_dir() is None:
            return

        simulated, target = self._get_simulated_and_target_dict("timing", use_planned=True)

        timing_df = pd.DataFrame(columns=columns)
        for key_type in set.intersection(set(target.keys()), set(simulated.keys())):
            for key_period in set.intersection(set(target[key_type].keys()), set(simulated[key_type].keys())):
                timing_df.loc[len(timing_df.index)] = [
                    key_type,
                    key_period,
                    target[key_type][key_period],
                    simulated[key_type][key_period],
                ]

        return timing_df

    @kpi_type(KPITag.CALIBRATION)
    def metric_calibration_destination(self):
        """Metric provides the calibration comparison of trip distances by activity type in simulation and that found in data, and also shows the validation travel
        times achieved in simulation compared to that found in data
        """
        columns = ["acttype", "data_type", "target", "simulated"]
        if self._get_target_dir() is None:
            return

        simulated, target = self._get_simulated_and_target_dict("destination_choice")
        simulated_time, target_time = self._get_simulated_and_target_dict(
            target_type="destination_choice", data_type="travel_time"
        )

        # Only use keys that are shared across all four dicts
        dicts = [simulated, target, simulated_time, target_time]
        keys = set.intersection(*(set(d.keys()) for d in dicts))

        def check(d, name):
            extra = set(d.keys()).difference(keys)
            if len(extra) > 0:
                logging.warning(f"Extra keys in {name} not found in others: {extra}")

        # warn for missing data
        [check(d, n) for d, n in zip(dicts, ["simulated", "target", "simulated_time", "target_time"])]

        return pd.DataFrame(
            [(key, "distance", target[key], simulated[key]) for key in keys]
            + [(key, "travel_time", target_time[key], simulated_time[key]) for key in keys],
            columns=columns,
        )

    @kpi_type(KPITag.CALIBRATION)
    def metric_calibration_boardings(self):
        """Metric provides the calibration comparison of boarding counts by transit agency and transit mode"""
        columns = ["agency", "mode", "target", "simulated"]
        if self._get_target_dir() is None:
            return

        simulated, target = self._get_simulated_and_target_dict("mode_choice_boardings")
        if simulated is None or target is None:
            return

        keys = set.intersection(set(target.keys()), set(simulated.keys()))
        return pd.DataFrame([(key[0], key[1], target[key], simulated[key]) for key in keys], columns=columns)

    @kpi_type(KPITag.VALIDATION)
    def metric_validation_speed(self):
        """Metric provides the validation of speeds simulated by link type and time period while comparing to data provided"""
        columns = ["link_type", "time_period", "target", "simulated"]

        if self._get_target_dir() is None:
            logging.warning("No calibration target directory")
            return

        simulated, target = self._get_simulated_and_target_dict("speed_by_funcl")
        if simulated is None or target is None:
            logging.warning("No target and simulation data")
            return

        keys = set.intersection(set(target.keys()), set(simulated.keys()))
        return pd.DataFrame([(key[0], key[1], target[key], simulated[key]) for key in keys], columns=columns)

    @kpi_type(KPITag.TRIPS)
    def metric_trip_length_distribution(self):
        """Metric provides an aggregate distribution of trip distances by mode and trip type"""
        sql = """SELECT t.mode, t.type, travel_distance
                   FROM Trip t
                  WHERE t.mode IN (0, 9, 17, 18, 19, 20)
                    AND t.has_artificial_trip <> 1 and t.start>=0
                    AND t.end<=110000
                    AND t.end > t.start
                    AND t.routed_travel_time > 0
                    AND t.travel_distance>0;"""

        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            df = pd.read_sql(sql, conn)

        dfs = []
        for m, t in df[["mode", "type"]].drop_duplicates().values:
            df_ = df[(df["mode"] == m) & (df["type"] == t)]
            max_dist = min(120, int(df_.travel_distance.max() / 1000))

            y, x = np.histogram(df_.travel_distance.to_numpy() / 1000, bins=range(0, max_dist))
            dfs.append(pd.DataFrame({"mode": m, "type": t, "distance": x[1:], "trips": y}))

        return pd.concat(dfs)

    @kpi_type(KPITag.TRIPS)
    def metric_trip_costs(self):
        """ "Metric provides the cost experienced when making trips in the simulation such as monetary (operating), toll, and time costs by mode and trip type"""
        sql = """
            SELECT t.mode, t.type,                                        -- agg column
                   scaling_factor * count(*) as num_trips,                -- for getting averages / trip
                   scaling_factor * sum(travel_distance) / 1609.3 as VMT, -- for getting averages / mile
                   scaling_factor * sum(t.monetary_cost) as monetary_cost,
                   scaling_factor * sum(t.toll) as toll_cost,
                   scaling_factor * sum(vt.operating_cost_per_mile * travel_distance) / 1609.3 as operating_cost,
                   -- removing the OVTT as it shouldn't be weighted by the mode specific VOTT
                   scaling_factor * sum(t.value_of_travel_time * (t.end - t.start - t.access_egress_ovtt)) / 3600 as time_cost
              FROM Trip t
         LEFT JOIN vehicle v ON t.vehicle = v.vehicle_id
         LEFT JOIN vehicle_type vt ON v.type = vt.type_id
             WHERE t.has_artificial_trip <> 1 and t.start>=0
               AND t.end<=110000
               AND t.end > t.start
               AND t.routed_travel_time > 0
               AND t.travel_distance>0
          GROUP BY 1,2;
        """
        return self._slow_fast(sql, "trip_costs", attach_db_type=DatabaseType.Demand)

    @kpi_type(KPITag.ACTIVITIES)
    def metric_activity_start_time_distributions(self):
        """Metric provides the activity start time distribution of vehicle trips in simulation"""
        sql = """SELECT start as tstart
                   FROM Trip t
                  WHERE t.mode IN (0, 9, 17, 18, 19, 20)
                    AND t.has_artificial_trip <> 1 and t.start>=0
                    AND t.end<=110000
                    AND t.end > t.start
                    AND t.routed_travel_time > 0"""

        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            df = pd.read_sql(sql, conn)

        # ~ 1000 trips per bin on average worked well for both Bloomington and Austin
        bins = int(max(30, np.floor(df.shape[0] / 1000)))
        y, x = np.histogram(df.tstart.to_numpy(), bins=bins)
        return pd.DataFrame({"trip_start": x[1:], "trips": y})

    @kpi_type((KPITag.ACTIVITIES_PLANNED, KPITag.HIGH_MEMORY))
    def metric_planned_activity_start_time_distributions(self):
        """ "Metric provides the planned activity start time distribution for all modes"""
        self.__get_activity_data()

        df = self.__activity_data[
            (self.__activity_data["mode"] != "NO_MOVE") | (self.__activity_data["type"] != "HOME")
        ]
        # ~ 1000 trips per bin on average worked well for both Bloomington and Austin
        bins = int(max(30, np.floor(df.shape[0] / 1000)))
        y, x = np.histogram(df.start_time.to_numpy(), bins=bins)
        return pd.DataFrame({"activity_start": x[1:], "activities": y})

    def __get_trip_data(self):
        if self.__trip_data.shape[0] > 0:
            return
        _ = ScenarioCompression.maybe_extract(self.inputs.supply_db)
        _ = ScenarioCompression.maybe_extract(self.inputs.demand_db)

    @kpi_type((KPITag.TRIPS, KPITag.VALIDATION))
    def metric_county_to_county_demand(self):
        """Metric provides a matrix of county to county demand aggregated using the County table in Supply"""
        # Use ~30 hours to catch any trips that roll over the day border
        sql = """SELECT COALESCE(lo.county, "NON_REPORTED") AS origin_county,
                        COALESCE(ld.county, "NON_REPORTED") AS destination_county,
                        mode AS mode_desc, count(*) AS trips FROM Trip t
                JOIN a.location lo ON t.origin = lo.location
                JOIN a.location ld ON t.destination = ld.location
                WHERE t.mode IN (0, 9, 17, 18, 19, 20)
                  AND t.has_artificial_trip <> 1 and t.start>=0
                  AND t.end<=110000
                  AND t.end > t.start
                  AND t.routed_travel_time > 0
                GROUP BY origin_county, destination_county, mode_desc"""

        return self._slow_fast(sql, "county_to_county_trips", attach_db_type=DatabaseType.Supply)

    def __get_activity_data(self):
        if self.__activity_data.shape[0] > 0:
            return
        _ = ScenarioCompression.maybe_extract(self.inputs.supply_db)
        _ = ScenarioCompression.maybe_extract(self.inputs.demand_db)

        am = ActivityMetrics(supply_file=self.inputs.supply_db, demand_file=self.inputs.demand_db)
        self.__activity_data = am.data

    @kpi_type(KPITag.POPULATION)
    def metric_average_vehicle_ownership(self):
        """Metric retrieves the average household vehicle ownership from the synthetic population in the output"""
        sql_slow = """SELECT avg(vehicles) as avg_hh_veh_from_hh, sum(vehicles) as tot_hh_veh_from_hh,
                        avg(case when num_vehicle_records is null then 0 else num_vehicle_records end) as avg_hh_veh_from_veh,
                        sum(case when num_vehicle_records is null then 0 else num_vehicle_records end) as tot_hh_veh_from_veh FROM
                        (Select * from Household h LEFT JOIN (SELECT hhold, count(*) as num_vehicle_records FROM Vehicle v GROUP by 1) v
                        ON h.household = v.hhold);
                    """
        return self._slow_fast(sql_slow, "average_vehicle_ownership", attach_db_type=DatabaseType.Demand)

    @kpi_type((KPITag.CONVERGENCE, KPITag.HIGH_MEMORY, KPITag.HIGH_CPU, KPITag.BROKEN))
    def metric_traffic_cumulative_gap(self):
        """BROKEN: Metric provides the cumulative gap"""
        self.__get_path_data()
        metrics = {
            "value_Switch_Cause": "By switch cause",
            "value_Number_of_Switches": "By number of switches",
            "has_artificial_trip": "By artificial trip",
            "mode_desc": "Traffic mode",
        }

        df = self.__path_data.rename(columns={"mend": "Trip end minute"})
        all_metrics = []
        for metric, label in metrics.items():
            if metric not in df.columns:
                logging.info(f"Metric: {metric} not available")
                continue
            data = df.groupby([metric, "Trip end minute"]).sum()[["absolute_gap"]].reset_index()

            pvt = data.pivot_table(index="Trip end minute", values="absolute_gap", columns=metric, fill_value=0)
            pvt = pvt.reset_index()
            output = pd.DataFrame({"Trip end minute": pvt["Trip end minute"]})
            for c in data[metric].unique():
                output[f"{c}"] = pvt[c].cumsum()
            output["metric"] = label
            all_metrics.append(output)
        return pd.concat(all_metrics)

    @kpi_type((KPITag.TRIPS))
    def metric_spatial_trips(self):
        """Metric provides trips by origin and destination across various aggregation for spatial mapping"""

        with commit_and_close(ScenarioCompression.maybe_extract(self.inputs.supply_db)) as conn:
            location_df = pd.read_sql("SELECT location, zone FROM location;", conn)

        with commit_and_close(ScenarioCompression.maybe_extract(self.inputs.demand_db)) as conn:
            sql = """
            SELECT
                person, start, end, origin, destination, mode, type,
                travel_distance, access_egress_ovtt, monetary_cost, toll
            FROM Trip
            WHERE (mode IN (0,9) AND has_artificial_trip <> 1)  -- skip stuck auto trips
                OR (mode NOT IN (0,9))                           -- non-auto modes
                AND start < end;
            """
            trip_df = pd.read_sql(sql, conn)
            sql = "SELECT person, school_location_id as school_loc, work_location_id as work_loc, household FROM person"
            person_df = pd.read_sql(sql, conn)
            hh_df = pd.read_sql("SELECT household, location FROM household;", conn)

        trip_df = trip_df.merge(
            location_df.rename(columns={"location": "origin", "zone": "origin_zone"}), on="origin", how="left"
        )
        trip_df = trip_df.merge(
            location_df.rename(columns={"location": "destination", "zone": "destination_zone"}),
            on="destination",
            how="left",
        )

        trip_df["person"] = trip_df.person.astype("Int64").fillna(-1)
        person_df = person_df.merge(hh_df.rename(columns={"location": "hh_location"}), on="household", how="left")
        trip_df = trip_df.merge(
            person_df[["person", "school_loc", "work_loc", "hh_location"]],
            on="person",
            how="left",
        )

        loc_cols = ["hh_location", "school_loc", "work_loc"]
        trip_df[loc_cols] = trip_df[loc_cols].astype("Int64").fillna(-1)

        has_person = trip_df.person != -1
        is_home_based = (trip_df.origin == trip_df.hh_location) | (trip_df.destination == trip_df.hh_location)
        is_work_based = (trip_df.origin == trip_df.work_loc) | (trip_df.destination == trip_df.work_loc)
        is_school_based = (trip_df.origin == trip_df.school_loc) | (trip_df.destination == trip_df.school_loc)

        trip_df["home_based"] = False
        trip_df["work_based"] = False
        trip_df.loc[has_person & is_home_based, "home_based"] = True
        trip_df.loc[has_person & (is_work_based | is_school_based), "work_based"] = True
        trip_df["purpose"] = "NOTHH"
        trip_df.loc[(trip_df.person != -1) & ~trip_df.home_based, "purpose"] = "NHB"
        trip_df.loc[(trip_df.person != -1) & trip_df.home_based & ~trip_df.work_based, "purpose"] = "HBO"
        trip_df.loc[(trip_df.person != -1) & trip_df.home_based & trip_df.work_based, "purpose"] = "HBW"

        trip_df["duration"] = trip_df.end - trip_df.start
        trip_df["start_hour"] = np.floor(trip_df.start / 3600)
        trip_df["end_hour"] = np.floor(trip_df.end / 3600)

        trip_df["start_period"] = trip_df.start_hour.map(timing_choice.hour_to_period_lu)
        trip_df["end_period"] = trip_df.end_hour.map(timing_choice.hour_to_period_lu)

        trip_df["trips"] = 1

        keep_cols = ["trips", "travel_distance", "duration", "access_egress_ovtt", "monetary_cost", "toll"]
        trip_start_df = trip_df.groupby(
            [
                "origin_zone",
                "mode",
                "type",
                "purpose",
                "start_period",
            ]
        )[keep_cols].sum()
        trip_start_df = trip_start_df / self.population_scale_factor
        trip_start_df = trip_start_df.reset_index()
        trip_start_df = trip_start_df.rename(
            columns={
                "origin_zone": "zone",
                "start_period": "period",
            }
        )
        trip_start_df["trip_side"] = "origin"

        # The next part can possibly be removed because we alost always look at only the origin side
        trip_end_df = trip_df.groupby(
            [
                "destination_zone",
                "mode",
                "type",
                "purpose",
                "end_period",
            ]
        )[keep_cols].sum()
        trip_end_df = trip_end_df / self.population_scale_factor
        trip_end_df = trip_end_df.reset_index()
        trip_end_df = trip_end_df.rename(
            columns={
                "destination_zone": "zone",
                "end_period": "period",
            }
        )
        trip_end_df["trip_side"] = "destination"

        return pd.concat([trip_start_df, trip_end_df], ignore_index=True)

    @kpi_type((KPITag.TRIPS, KPITag.PARKING))
    def metric_sov_parking_access_time(self):
        """Metric provides the parking access time simulated for personally-owned auto-based trips"""
        access_time_sql = """
            SELECT
                access_egress_ovtt > 0 as is_walking,
                min(access_egress_ovtt) / 60 as min_access_time_min,
                avg(access_egress_ovtt) / 60 as avg_access_time_min,
                max(access_egress_ovtt) / 60 as max_access_time_min,
                count(*) * scaling_factor  as count
                FROM Trip WHERE mode = 0
                GROUP BY 1;"""

        return self._slow_fast(access_time_sql, "sov_parking_access_time")

    @kpi_type((KPITag.PARKING))
    def metric_parking_share(self):
        """Metric provides the share of parking simulated between garage and on-street parking locations"""
        parking_share_sql = """
        SELECT garage_choices * 1.0 / (onstreet_choices + garage_choices) as garage_share,
                            onstreet_choices * 1.0 / (onstreet_choices + garage_choices) as onstreet_share
                    FROM (SELECT SUM(CASE WHEN p.type IN ('garage', 'airport') THEN 1 ELSE 0 END) AS garage_choices,
                            SUM(CASE WHEN p.type NOT IN ('garage', 'airport') THEN 1 ELSE 0 END) AS onstreet_choices
                            FROM Parking_Records pr JOIN a.Parking p ON pr.Parking_ID = p.parking
                            JOIN a.zone z ON p.zone = z.zone WHERE Parking_ID <> -1 AND z.area_type <= 3);"""
        return self._slow_fast(parking_share_sql, "parking_share", attach_db_type=DatabaseType.Supply)

    @kpi_type((KPITag.PARKING))
    def metric_escooter_utilization_at_garage(self):
        """Metric provides the e-scooter utilization when they are available at garages to use after parking a vehicle"""
        escooter_park_use_sql = """SELECT parking_ID, sum(Escooter_Borrowed) * scaling_factor as escooter_trips
        FROM Parking_Records pr
        LEFT JOIN Parking p
        ON p.parking = pr.parking_id
        WHERE num_escooters > 0 and p.type == 'garage'
        GROUP BY 1;"""

        return self._slow_fast(escooter_park_use_sql, "escooter_use_at_each_garage", attach_db_type=DatabaseType.Supply)

    @kpi_type((KPITag.PARKING))
    def metric_parking_utilization(self):
        """Metric provides the temporal utilization of parking for various parking types separated by area types"""

        occupancy_by_type_sql = """SELECT type, area_type, po.start/3600 as start_hr,
        count(*) * scaling_factor as count, avg(occupancy) as avg_occ
        FROM Parking_Occupancy po
        LEFT JOIN Parking p ON p.parking = po.parking_id
        LEFT JOIN Zone z ON p.zone = z.zone
        GROUP BY type, area_type, start_hr"""

        return self._slow_fast(
            occupancy_by_type_sql, "parking_occ_by_type", DatabaseType.Results, attach_db_type=DatabaseType.Supply
        )

    @kpi_type((KPITag.PARKING))
    def metric_garage_access_w_escooters(self):
        """Metric provides e-scooter utilization, demand, and access time observed at garages"""

        garage_sql = """SELECT parking FROM Parking WHERE type == 'garage' and num_escooters > 0;"""

        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.supply_db)) as conn:
            garages_with_escooters = pd.read_sql(garage_sql, conn)

        if garages_with_escooters.shape[0] == 0:
            return None

        access_times_sql = f"""SELECT Escooter_Borrowed,
        avg(distance_to_G) as access_dist_km,
        case when Escooter_Borrowed = 1 then avg(distance_to_G)/16 * 60 else avg(distance_to_G)/5 * 60 end
        as access_min, count(*) * scaling_factor as demand FROM Parking_Records pr
        LEFT JOIN Parking_Choice_Records pcr ON pr.choice_id = pcr.choice_id
        WHERE pr.parking_id in ({', '.join(garages_with_escooters.parking.astype(str))}) and pcr.chosen == 1
        GROUP BY pr.Escooter_Borrowed;"""

        return self._slow_fast(access_times_sql, "garage_access_w_escooters")

    @kpi_type((KPITag.PARKING))
    def metric_parking_stats(self):
        """Metric provides aggregate parking statistics such as revenue, demand, and number of e-scooter trips made by parking type and time of day"""

        p_stats_sql = """SELECT p.type as parking_type, (pr.Cost == 0.0) as free, pr.Time_In/3600 as start_hr,
                        sum(Cost) * scaling_factor as revenue, count(*) * scaling_factor as demand,
                        sum(Escooter_Borrowed) * scaling_factor as escooter_trips
                    FROM Parking_Records pr
                    LEFT JOIN Parking p
                    ON p.parking = pr.parking_id
                    WHERE Cost < 100000
                    GROUP BY 1,2,3;"""

        return self._slow_fast(p_stats_sql, "parking_stats", attach_db_type=DatabaseType.Supply)

    @kpi_type((KPITag.PARKING))
    def metric_parking_delay_stats(self):
        """Metric provides the aggregate delay statistics observed around parking infrastructure"""
        with read_and_close(ScenarioCompression.maybe_extract(self.inputs.supply_db)) as conn:
            parking_df = pd.read_sql(
                """SELECT * FROM (
                    SELECT
                        parking,
                        p.link,
                        p.link * 2 AS link_uid,
                        p.type AS parking_type,
                        z.area_type AS area_type
                    FROM Parking p
                    LEFT JOIN Zone z ON p.zone = z.zone
                    LEFT JOIN Link l ON p.link = l.link
                    WHERE l.lanes_ab > 0
                    UNION ALL
                    SELECT
                        parking,
                        p.link,
                        p.link * 2 + 1 AS link_uid,
                        p.type AS parking_type,
                        z.area_type AS area_type
                    FROM Parking p
                    LEFT JOIN Zone z ON p.zone = z.zone
                    LEFT JOIN Link l ON p.link = l.link
                    WHERE l.lanes_ba > 0);""",
                conn,
            )
        h5 = H5_Results(self.inputs.result_h5)
        vehicular_delays = (
            h5.get_link_delays(pivot_to_AB=False)
            .multiply(h5.get_link_volumes(population_scale_factor=self.population_scale_factor, pivot_to_AB=False))
            .rename(columns={"Daily": "total_veh_delay"})
        )
        df = parking_df.merge(vehicular_delays, left_on="link_uid", right_index=True, how="left").reset_index()
        df.total_veh_delay = df.total_veh_delay / 3600.0

        return df

    @kpi_type(KPITag.FREIGHT)
    def metric_freight_mode_share(self):
        """Metric provides the aggregate freight mode share by shipment mode"""
        if not self.inputs.freight_db.exists():
            return None
        sql = """
            SELECT ship.mode,
                   freight_mode_fn,
                   SUM(tf.annual_demand) AS annual_demand_sum,
                   SUM(tf.annual_demand) * 1.0 / SUM(SUM(tf.annual_demand)) OVER () AS share
            FROM Shipment AS ship
            LEFT JOIN Trade_Flow AS tf ON ship.trade_pair = tf.trade_pair
            GROUP BY 1;
        """
        return self._slow_fast(sql, "freight_mode_share", DatabaseType.Freight)

    @kpi_type(KPITag.FREIGHT)
    def metric_freight_shipping_cost(self):
        """Metric provides the total shipment costs by shipment mode"""
        if not self.inputs.freight_db.exists():
            return None
        sql = """
            SELECT mode, freight_mode_fn, SUM(CAST(total_cost AS REAL)) AS total_cost_sum
            FROM Shipment as ship
            GROUP BY 1
            ORDER BY 1;
        """
        return self._slow_fast(sql, "freight_shipping_cost", DatabaseType.Freight)

    @kpi_type(KPITag.FREIGHT)
    def metric_freight_mode_trade_type(self, **kwargs):
        """Metric provides the freight movements by trade type"""
        if not self.inputs.freight_db.exists():
            return None
        return self._slow_fast(
            sql_dir / "freight" / "freight.template.sql",
            "freight_mode_trade_type",
            DatabaseType.Freight,
            attach_db_type=DatabaseType.Demand,
            **kwargs,
        )

    @kpi_type(KPITag.FREIGHT)
    def metric_freight_trip(self):
        """Metric provides freight trip summary"""
        if not self.inputs.freight_db.exists():
            return None
        return self._slow_fast(
            sql_dir / "freight" / "freight.template.sql",
            "freight_trip",
            DatabaseType.Freight,
            attach_db_type=DatabaseType.Demand,
        )

    @kpi_type(KPITag.FREIGHT)
    def metric_freight_distance_distribution(self):
        """Metric provides freight distance distribution by freight mode, trip purpose, and trip type"""
        if not self.inputs.freight_db.exists():
            return None
        df = self.metric_freight_trip()
        df = df.drop_duplicates(subset=["trip_id"], keep="first")
        # make freight distance distribution
        dfs = []
        for m, t, p, fm in df[["mode", "type", "purpose", "freight_mode"]].drop_duplicates().values:
            df_ = df[(df["mode"] == m) & (df["type"] == t) & (df["purpose"] == p) & (df["freight_mode"] == fm)]
            max_dist = min(1000, int(df_.travel_distance.max() / 1000))

            y, x = np.histogram(df_.travel_distance.to_numpy() / 1000, bins=range(0, max_dist))
            dfs.append(
                pd.DataFrame({"mode": m, "type": t, "purpose": p, "freight_mode": fm, "distance": x[1:], "trips": y})
            )

        return pd.concat(dfs)

    def __get_path_data(self):
        if self.__path_data.shape[0] > 0:
            return
        _ = ScenarioCompression.maybe_extract(self.inputs.demand_db)

        pm = PathMetrics(demand_file=self.inputs.demand_db, h5_file=self.inputs.result_h5)
        self.__path_data = pm.data
