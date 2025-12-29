# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import copy
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from polaris import Polaris
from .add_missing import initialize_seed
from .correction import correct_across_tracts
from .validation import validate
from .verify_codes import verify_polaris_codes
from .verify_distribution_input import verify_veh_dist_input
from .verify_inputs import verify_inputs
from .verify_target_distribution import verify_target_distribution
from .verify_zones import verify_zone_input


class RedistributeVehicles:
    def __init__(
            self, model_dir, veh_file, target_file, zone_weights=None, fleet_mode=False  # noqa: C901
    ):
        """
        Update existing vehicle distribution files to new aggregate forecast targets
        :param model_dir:  The working directory where all files can be found
        :param veh_file:  existing vehicle distribution file with required field "TRACT", "POLARIS_ID", "VINTAGE" and "PROPORTION",
                          along with common fields from the control and vehicle_codes files
        :param target_file:  required aggregate distribution of vehicles types across control fields, with probability that sums to 1
        :param zone_weights:    Count of total vehicles by zone for the same zone system as in veh_file, if omitted makes all zones have equal weight in IPF
        :param fleet_mode:    Whether we are updating a fleet distribution (True) or a personal vehicle distribution (False)
        :return: None

        >>> model_dir = "C:/polaris_models/gpra/austin/built/veh_updates"
        >>> veh_file = Path("D:/path_to_source_vehicle_distribution_file/vehicle_distribution_updated_campo.txt")
        >>> target_file = Path("D:/path_to_target/target_2035_low.csv")
        >>> zone_weights = Path("D:/path_to_zone_weights/veh_by_zone.csv")
        >>> rv = RedistributeVehicles(model_dir=model_dir, veh_file=veh_file, target_file=target_file, zone_weights=zone_weights,fleet_mode=False)
        >>> rv.process(conv_threshold=0.001, max_iterations=50)
        >>> rv.save_results(Path("D:/path_to_results/veh_distr.csv"))
        """

        self.match_veh_type = 0
        self.match_zone = 0
        self.err = np.inf
        self.__results: pd.DataFrame
        self.fleet_mode = fleet_mode
        self.__tracking_columns = ["TRACT", "VEHICLE_CLASS", "FUEL", "POWERTRAIN", "VINTAGE", "PROPORTION"]
        # Polaris codes
        pol = Polaris.from_dir(model_dir)
        df = pol.demand.tables.get("Vehicle_Type").rename(columns={"type_id": "POLARIS_ID"})
        df = df.drop(columns=['ev_features_id', 'operating_cost_per_mile'])
        self.codes_df = df.rename(columns={x: str(x).upper().replace("_TYPE", "") for x in df.columns})

        # get the vehicle distribution
        self.veh_df = pd.read_csv(veh_file)
        if self.veh_df.columns.size == 1:
            self.veh_df = pd.read_csv(veh_file, delimiter="\t")
        self.veh_df = self.veh_df.rename(columns={x: str(x).upper() for x in self.veh_df.columns})
        self.veh_df = self.veh_df.rename(
            columns={"POLARIS_CODE": "POLARIS_ID", "PROB": "PROPORTION", "CLASS": "VEHICLE_CLASS"})

        # Targets
        self.target_df = pd.read_csv(target_file)
        if self.target_df.columns.size == 1:
            self.target_df = pd.read_csv(target_file, delimiter="\t")
        self.target_df = self.target_df.rename(columns={x: str(x).upper() for x in self.target_df.columns})

        self.pcode_idx = list(self.codes_df.columns[1:])

        self.controls = list(self.target_df.columns[:-1])
        t_names = {n: n.upper() for n in self.controls}
        self.controls = [x.upper() for x in self.controls]
        self.target_df.rename(columns=t_names, inplace=True)
        self.target_df.set_index(self.controls, inplace=True)

        # get the zone weights if requested or create default if not
        if self.fleet_mode:
            self.zone_df = None
        else:
            if zone_weights:
                self.zone_df = pd.read_csv(zone_weights)
                if self.zone_df.columns.size == 1:
                    self.zone_df = pd.read_csv(zone_weights, delimiter="\t")
                self.zone_df = self.zone_df.rename(columns={x: str(x).upper() for x in self.zone_df.columns})
            else:
                self.zone_df = self.veh_df.groupby("TRACT")[self.veh_df.columns[-1:]].count().reset_index()
                n = self.zone_df.columns[-1:][0]
                self.zone_df.rename(columns={n: "VEH_COUNT"}, inplace=True)
                self.zone_df["VEH_COUNT"] = 100.0

    def check_inputs(self):
        self.codes_df = verify_polaris_codes(self.codes_df)

        self.target_df = verify_target_distribution(self.target_df)

        self.veh_df = verify_veh_dist_input(self.veh_df, self.controls, self.fleet_mode)

        if not self.fleet_mode:
            self.zone_df = verify_zone_input(self.zone_df)

        verify_inputs(self.veh_df, self.target_df)

    def process(self, conv_threshold=0.001, max_iterations=50):
        # Add any vehicle type combinations with default small probabilities from the target that are missing for each zone
        self.check_inputs()

        default_values = {
            "VEHICLE_CLASS": "DEFAULT",
            "POWERTRAIN": "CONVENTIONAL",
            "FUEL": "GAS",
            "AUTOMATION": 0,
            "CONNECTIVITY": "NO",
            "VINTAGE": 0,
        }
        if not self.fleet_mode:
            self.veh_df = initialize_seed(self.veh_df, self.target_df, self.zone_df, self.codes_df, default_values)
            self.veh_df = correct_across_tracts(self.veh_df)

        # add the default uncontrolled values for doing lookup in the polaris codes map
        pcode_missing_values = {}
        self.pcode_idx_names = copy.deepcopy(self.controls)
        source_names = []
        tottime = perf_counter()

        for c in self.pcode_idx:
            if c not in self.controls:
                self.pcode_idx_names.append(c)
            # add defaults for each uncontrolled vehicle characteristics to the source dataframe
            if c not in self.veh_df.columns:
                if c not in default_values:
                    print("ERROR, unknown vehicle characteristic dimension name '" + c)
                else:
                    pcode_missing_values[c] = default_values[c]
            else:
                source_names.append(c)

        # convert vehicle distribution to actual counts for use in IPF
        df = self.veh_df.join(self.zone_df, "TRACT")
        df["VEH_TOT"] = df["PROPORTION"] * df["VEH_COUNT"]

        # ------------ Do IPF to targets --------------------------------------------
        counter = 0
        while self.err > conv_threshold and counter < max_iterations:
            ttime = perf_counter()
            # IPF on vehicle self.controls dimension
            g_veh = df[self.controls + ["VEH_TOT"]].groupby(self.controls)
            agg_type = g_veh.sum() / df["VEH_TOT"].sum()
            veh_update = self.target_df.join(agg_type, self.controls)
            veh_update.loc[veh_update.VEH_TOT > 0, "value"] = veh_update["value"] / veh_update.VEH_TOT
            df = self.update_across_veh_types(df, veh_update)

            if self.fleet_mode:
                # If fleet mode, we can just exit now
                veh_update.loc[veh_update.VEH_TOT > 0, "value"] = veh_update["value"] / veh_update.VEH_TOT
                self.err = abs(1.0 - veh_update["VEH_COUNT"].max())
                break

            # IPF on zone count dimension
            g_cnt = df[["TRACT", "VEH_TOT"]].groupby(["TRACT"]).sum()
            cnt_update = g_cnt.join(self.zone_df, "TRACT")
            cnt_update["VEH_COUNT"] = cnt_update.VEH_COUNT.astype(np.float64)
            cnt_update.loc[cnt_update.VEH_TOT > 0, "VEH_COUNT"] = cnt_update.VEH_COUNT / cnt_update.VEH_TOT
            df = self.update_across_zones(df, cnt_update)
            self.err = abs(1.0 - cnt_update["VEH_COUNT"].max())

            counter += 1
            print(f"Iteration {counter}: {round(perf_counter() - ttime, 1)}s , error {round(self.err, 5)}")

        df["PROPORTION"] = (df["VEH_TOT"] / df["VEH_COUNT"]).fillna(0)

        df.dropna(subset=self.__tracking_columns, inplace=True)
        df = df[df.PROPORTION > 0]
        self.__results = df.set_index(self.__tracking_columns)
        self.__check_tract_totals()

        print(f"Total processing time: {round(perf_counter() - tottime, 1)}s")

    def save_results(self, out_veh_file):
        model_dir = Path(out_veh_file).parent
        self.match_veh_type, self.match_zone = validate(
            self.__results, self.target_df, self.zone_df, model_dir, out_veh_file
        )

        df = self.__results.reset_index()[self.__tracking_columns + ["POLARIS_ID"]]

        df[df.PROPORTION > 0].sort_values("TRACT").to_csv(out_veh_file, index=False)

    def fix_across_tracts(self):
        self.__results = correct_across_tracts(self.__results.reset_index()).set_index(self.__tracking_columns)
        print("Proportions for missing tracts have been fixed")

    def __check_tract_totals(self):
        df = self.__results.reset_index()
        df2 = df.groupby(["TRACT"]).sum()[["PROPORTION"]]
        if round(df2.PROPORTION.max(), 4) > 1 or round(df2.PROPORTION.min(), 4) < 1:
            print("YOUR TRACT CONTROL TOTALS DO NOT ALL ADD TO 1.0 YOU MAY HAVE MISSING TRACTS ON YOUR CONTROL TOTALS")
            print("You can correct this issue by calling the method fix_across_tracts before saving results")

    def update_across_veh_types(self, df: pd.DataFrame, update_values):
        df2 = df.set_index(self.controls)
        df3 = df2.join(update_values, how="left", rsuffix="_v")
        df3["VEH_TOT"] *= df3["value"]
        df3.VEH_TOT.fillna(0)
        return df3.reset_index()[list(df.columns)]

    def update_across_zones(self, df: pd.DataFrame, update_values: pd.DataFrame) -> pd.DataFrame:
        cols = list(df.columns)
        fac = update_values[["VEH_COUNT"]].rename(columns={"VEH_COUNT": "mult_factor"})
        df = df.merge(fac, left_on="TRACT", right_index=True)
        df["VEH_TOT"] *= df.mult_factor
        return pd.DataFrame(df[cols])
