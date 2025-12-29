# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.mdimport logging
import logging
from pathlib import Path

import pandas as pd
from polaris.utils.database.db_utils import commit_and_close, run_sql
from polaris.utils.list_utils import first_and_only
from polaris.utils.logging_utils import function_logging
from polaris.runs.scenario_compression import ScenarioCompression


class EnergyMetrics:
    """Loads all data from Autonomie energy, assigns energy
    back to trip table in demand, and creates tables ready for KPI use.
    """

    def __init__(self, demand_file: Path, autonomie_energy_folder: Path):
        """
        :param demand_file: Path to the demand file for which energy was computed
        :param autonomie_energy_folder: Path to folder where Autonomie energy results exist for given demand
        """

        self.__demand_file = demand_file
        self.__autonomie_result_csv = first_and_only(autonomie_energy_folder.glob("Result*.csv"))
        self.add_energy_to_demand()

    def add_energy_to_demand(self):
        logging.info("Adding energy results in csv into the demand database")
        df = pd.read_csv(self.__autonomie_result_csv)
        with commit_and_close(ScenarioCompression.maybe_extract(self.__demand_file)) as conn:
            df.to_sql("energy_results", con=conn, chunksize=500, if_exists="replace", index=False)

    @function_logging("  -> energy_use_by_mode")
    def energy_use_by_mode(self):
        sql = """
        DROP TABLE if exists energy_use_by_mode;

        CREATE TABLE energy_use_by_mode AS
            select a.mode as mode,  a.cacc as cacc, a.veh_type as veh_type, a.veh_class as veh_class, a.veh_powertrain as veh_powertrain, a.fuel_type as fuel_type, count(distinct a.trip_id) as trip_count, count(distinct a.veh_id) as veh_count, sum(a.length_miles) as length_miles, sum(a.fuel_kg) as fuel_kg, sum(a.GHG_ptw_g) as GHG_ptw_g,
                sum(a.GHG_wtp_g) as GHG_wtp_g, sum(a.elec_kWhr) as elec_kWhr, sum(a.fuel_kWhr) as fuel_kWhr, sum(a.length_miles) / (sum(a.elec_kWhr) + sum(a.fuel_kWhr)) * 33.7 as MPGge,
                sum(a.length_miles) / (sum(a.elec_kWhr) + sum(a.fuel_kWhr)) * 37.1 as MPGde, (sum(a.elec_kWhr) + sum(a.fuel_kWhr)) / sum(a.length_miles) as energy_kWhr_mi,
                sum(a.routed_travel_time) as travel_time_sec
            from (select t.mode as mode,
                        at.cacc as cacc,
                        case when r."Vehicle Class" = 'Class2' or r."Vehicle Class" = 'Class3' or r."Vehicle Class" = 'Class4' or r."Vehicle Class" = 'Class5' or r."Vehicle Class" = 'Class6'
                        or r."Vehicle Class" = 'TRUCK6' or r."Vehicle Class" = 'TRUCK8' or r."Vehicle Class" = 'Class8' then 'MD/HD' else 'LD' end as veh_type,
                        r."Trip Number" as trip_id,
                        r."Vehicle ID" as veh_id,
                        r."Vehicle Class" as veh_class,
                        r."Vehicle Powertrain" as veh_powertrain,
                        ft.type as fuel_type,
                        sum(r."Driving Distance [m]")/1609.3 as length_miles,
                        sum(t.routed_travel_time) as routed_travel_time,
                        sum(r."Fuel Consumption [kg]") as fuel_kg,
                        sum(r."PTW GHGs [g]") as GHG_ptw_g,
                        sum(r."WTP GHGs [g]") as GHG_wtp_g,
                        sum(case when v.powertrain_type = 2 or v.powertrain_type = 3 or v.powertrain_type = 6 then r."Electrical Consumption [J]"/3600/1000 else 0 end) as elec_kWhr,
                        sum(r."Fuel Energy [kWh]") as fuel_kWhr
                from energy_results as r,
                        (select mode, path, routed_travel_time from tnc_trip union select mode, path, routed_travel_time from trip) as t,
                        vehicle_type as v,
                        automation_type as at,
                        fuel_type as ft
                where
                        t.path is not null
                        and t.path <> -1
                        and r."Trip Number" = t.path
                        and r."Vehicle Type" = v.type_id
                        and v.automation_type = at.type_id
                        and v.fuel_type = ft.type_id
    group by 1,2,3,4,5,6,7,8) as a
    group by 1,2,3,4,5,6;
        """
        with commit_and_close(ScenarioCompression.maybe_extract(self.__demand_file)) as conn:
            run_sql(sql, db=conn)

    @function_logging("  -> energy_use_by_automation")
    def energy_use_by_automation(self):
        sql = """
        DROP TABLE if exists energy_use_by_automation;

        CREATE TABLE energy_use_by_automation AS
            select a.acc as acc, a.cacc as cacc, a.veh_type as veh_type, count(distinct a.trip_id) as trip_count, count(distinct a.veh_id) as veh_count, sum(a.length_miles) as length_miles, sum(a.fuel_kg) as fuel_kg, sum(a.GHG_ptw_g) as GHG_ptw_g,
                sum(a.GHG_wtp_g) as GHG_wtp_g, sum(a.elec_kWhr) as elec_kWhr, sum(a.fuel_kWhr) as fuel_kWhr, sum(a.length_miles) / (sum(a.elec_kWhr) + sum(a.fuel_kWhr)) * 33.7 as MPGge,
                sum(a.length_miles) / (sum(a.elec_kWhr) + sum(a.fuel_kWhr)) * 37.1 as MPGde, sum(a.routed_travel_time) as travel_time_sec
                from(select
                    at.acc as acc,
                    at.cacc as cacc,
                    case when r."Vehicle Class" = 'Class2' or r."Vehicle Class" = 'Class3' or r."Vehicle Class" = 'Class4' or r."Vehicle Class" = 'Class5' or r."Vehicle Class" = 'Class6'
                    or r."Vehicle Class" = 'TRUCK6' or r."Vehicle Class" = 'TRUCK8' or r."Vehicle Class" = 'Class8' then 'MD/HD'
                            else 'LD' end as veh_type,
                r."Trip Number" as trip_id,
                r."Vehicle ID" as veh_id,
                    sum(r."Driving Distance [m]")/1609.3 as length_miles,
                    sum(t.routed_travel_time) as routed_travel_time,
                    sum(r."Fuel Consumption [kg]") as fuel_kg,
                    sum(r."PTW GHGs [g]") as GHG_ptw_g,
                    sum(r."WTP GHGs [g]") as GHG_wtp_g,
                    sum(case when v.powertrain_type = 2 or v.powertrain_type = 3 or v.powertrain_type = 6 then r."Electrical Consumption [J]"/3600/1000 else 0 end) as elec_kWhr,
                    sum(r."Fuel Energy [kWh]") as fuel_kWhr
                from energy_results as r,
                    (select path, mode, routed_travel_time from tnc_trip union select path, mode, routed_travel_time from trip) as t,
                    vehicle_type as v,
                    automation_type as at
                where
                    t.path is not null
                    and t.path <> -1
                    and r."Trip Number" = t.path
                    and r."Vehicle Type" = v.type_id
                    and v.automation_type = at.type_id
    group by 1,2,3,4) as a
    group by 1,2,3;
        """
        with commit_and_close(ScenarioCompression.maybe_extract(self.__demand_file)) as conn:
            run_sql(sql, db=conn)

    @function_logging("  -> energy_use_by_veh_type")
    def energy_use_by_veh_type(self):
        sql = """
        DROP TABLE if exists energy_use_by_veh_type;

        CREATE TABLE energy_use_by_veh_type AS
            select
                veh_type,
                sum(trip_count) as trip_count,
                sum(length_miles) as length_miles,
                sum(fuel_kg) as fuel_kg,
                sum(GHG_ptw_g) as GHG_ptw_g,
                sum(GHG_wtp_g) as GHG_wtp_g,
                sum(fuel_kWhr) as fuel_kWhr,
                sum(elec_kWhr) as elec_kWhr,
                sum(trip_count) * 100 / 1e6 as trip_count_mill,
                sum(length_miles) * 100 / 1e6 as VMT_mi_mill,
                sum(length_miles) / (sum(elec_kWhr) + sum(fuel_kWhr)) * 33.7 as MPGge,
                sum(length_miles) / (sum(elec_kWhr) + sum(fuel_kWhr)) * 37.1 as MPGde,
                sum(fuel_kg) * 100 / 1e6 as fuel_Gg,
                sum(fuel_kWhr) * 100 / 1e6 as fuel_GWh,
                sum(elec_kWhr) * 100 / 1e6 as elec_GWh,
                sum(GHG_ptw_g) * 100 / 1e9 as GHG_ptw_Gg,
                sum(GHG_ptw_g) / sum(length_miles) as GHG_ptw_ave_gmi,
                (sum(GHG_ptw_g)+ sum(GHG_wtp_g)) * 100 / 1e9 as GHG_wtw_Gg,
                (sum(GHG_ptw_g)+ sum(GHG_wtp_g)) / sum(length_miles) as GHG_wtw_ave_gmi
            from energy_use_by_mode
            group by veh_type;
        """
        with commit_and_close(ScenarioCompression.maybe_extract(self.__demand_file)) as conn:
            run_sql(sql, db=conn)

    @function_logging("  -> energy_use_total")
    def energy_use_total(self):
        sql = """
        DROP TABLE if exists energy_use_total;

        CREATE TABLE energy_use_total AS
            select
                sum(trip_count) as trip_count,
                sum(length_miles) as length_miles,
                sum(fuel_kg) as fuel_kg,
                sum(GHG_ptw_g) as GHG_ptw_g,
                sum(GHG_wtp_g) as GHG_wtp_g,
                sum(fuel_kWhr) as fuel_kWhr,
                sum(elec_kWhr) as elec_kWhr,
                sum(trip_count_mill) as trip_count_mill,
                sum(VMT_mi_mill) as VMT_mi_mill,
                sum(length_miles) / (sum(elec_kWhr) + sum(fuel_kWhr)) * 33.7 as MPGge,
                sum(length_miles) / (sum(elec_kWhr) + sum(fuel_kWhr)) * 37.1 as MPGde,
                sum(fuel_Gg) as fuel_Gg,
                sum(elec_GWh) as elec_GWh,
                sum(GHG_ptw_Gg) as GHG_ptw_Gg,
                sum(GHG_ptw_g) / sum(length_miles) as GHG_ptw_ave_gmi,
                sum(GHG_wtw_Gg) as GHG_wtw_Gg,
                (sum(GHG_ptw_g)+ sum(GHG_wtp_g)) / sum(length_miles) as GHG_wtw_ave_gmi
            from energy_use_by_veh_type;
        """
        with commit_and_close(ScenarioCompression.maybe_extract(self.__demand_file)) as conn:
            run_sql(sql, db=conn)

    @function_logging("  -> energy_use_freight_only")
    def energy_use_freight_only(self):
        sql = """
        -- Freight & E-commerce Metrics: VMT & Energy Use
        DROP TABLE IF EXISTS energy_use_freight_only;

        CREATE TABLE energy_use_freight_only AS
        select
                t.mode,
                case
                    when t.purpose = 1
                    then "E-Commerce" else "Other" end as purpose,
                case when r."Vehicle Class" = "Class2" or r."Vehicle Class" = "Class3" or r."Vehicle Class" = "Class4" or r."Vehicle Class" = "Class5" or r."Vehicle Class" = "Class6"
                    or r."Vehicle Class" = "TRUCK6" or r."Vehicle Class" = "TRUCK8" or r."Vehicle Class" = 'Class8' then "MD/HD"
                    else "LD" end as veh_type,
                count(distinct r."Trip Number") * 100 / 1e6 as trip_count_mill,
                sum(r."Driving Distance [m]")/1609.3 * 100 / 1e6 as VMT_mi_mill,
                sum(r."Fuel Consumption [kg]") * 100 / 1e6 as fuel_Gg,
                sum(r."Fuel Energy [kWh]") * 100 / 1e6 as fuel_GWh,
                sum(case when v.powertrain_type = 2 or v.powertrain_type = 3 or v.powertrain_type = 6 then r."Electrical Consumption [J]"/3600/1000 else 0 end) * 100 / 1e6 as elec_GWh,
                sum(r."PTW GHGs [g]") * 100 / 1e9 as GHG_ptw_Gg,
                (sum(r."WTP GHGs [g]") + sum(r."PTW GHGs [g]"))  * 100 / 1e9 as GHG_wtw_Gg,
                case
                    when v.powertrain_type = 2 or v.powertrain_type = 3 or v.powertrain_type = 6
                    then sum(r."Driving Distance [m]"/1609.3) / sum(r."Electrical Consumption [J]"/3600/1000 + r."Fuel Energy [kWh]") * 33.7
                    else sum(r."Driving Distance [m]"/1609.3) / sum(r."Fuel Energy [kWh]") * 33.7
                    end as MPGge,
                case
                    when v.powertrain_type = 2 or v.powertrain_type = 3 or v.powertrain_type = 6
                    then sum(r."Driving Distance [m]"/1609.3) / sum(r."Electrical Consumption [J]"/3600/1000 + r."Fuel Energy [kWh]") * 37.1
                    else sum(r."Driving Distance [m]"/1609.3) / sum(r."Fuel Energy [kWh]") * 37.1
                    end as MPGde
            from
                energy_results as r,
                tnc_trip as t,
                vehicle_type as v
            where
                t.path is not null
                and t.path <> -1
                and r."Trip Number" = t.path
                and r."Vehicle Type" = v.type_id
            union
            select
                t.mode,
                case
                    when t.purpose = 1
                    then "E-Commerce" else "Other" end as purpose,
                case when r."Vehicle Class" = "Class2" or r."Vehicle Class" = "Class3" or r."Vehicle Class" = "Class4" or r."Vehicle Class" = "Class5" or r."Vehicle Class" = "Class6"
                    or r."Vehicle Class" = "TRUCK6" or r."Vehicle Class" = "TRUCK8" or r."Vehicle Class" = 'Class8' then "MD/HD"
                    else "LD" end as veh_type,
                count(distinct r."Trip Number") * 100 / 1e6 as trip_count_mill,
                sum(r."Driving Distance [m]")/1609.3 * 100 / 1e6 as VMT_mi_mill,
                sum(r."Fuel Consumption [kg]") * 100 / 1e6 as fuel_Gg,
                sum(r."Fuel Energy [kWh]") * 100 / 1e6 as fuel_GWh,
                sum(case when v.powertrain_type = 2 or v.powertrain_type = 3 or v.powertrain_type = 6 then r."Electrical Consumption [J]"/3600/1000 else 0 end) * 100 / 1e6 as elec_GWh,
                sum(r."PTW GHGs [g]") * 100 / 1e9 as GHG_ptw_Gg,
                (sum(r."WTP GHGs [g]") + sum(r."PTW GHGs [g]"))  * 100 / 1e9 as GHG_wtw_Gg,
                case
                    when v.powertrain_type = 2 or v.powertrain_type = 3 or v.powertrain_type = 6
                    then sum(r."Driving Distance [m]"/1609.3) / sum(r."Electrical Consumption [J]"/3600/1000 + r."Fuel Energy [kWh]") * 33.7
                    else sum(r."Driving Distance [m]"/1609.3) / sum(r."Fuel Energy [kWh]") * 33.7
                    end as MPGge,
                case
                    when v.powertrain_type = 2 or v.powertrain_type = 3 or v.powertrain_type = 6
                    then sum(r."Driving Distance [m]"/1609.3) / sum(r."Electrical Consumption [J]"/3600/1000 + r."Fuel Energy [kWh]") * 37.1
                    else sum(r."Driving Distance [m]"/1609.3) / sum(r."Fuel Energy [kWh]") * 37.1
                    end as MPGde
            from
                energy_results as r,
                trip as t,
                vehicle_type as v
            where
                t.path is not null
                and t.path <> -1
                and r."Trip Number" = t.path
                and r."Vehicle Type" = v.type_id
            group by t.mode, veh_type, t.purpose;
        """
        with commit_and_close(ScenarioCompression.maybe_extract(self.__demand_file)) as conn:
            run_sql(sql, db=conn)
