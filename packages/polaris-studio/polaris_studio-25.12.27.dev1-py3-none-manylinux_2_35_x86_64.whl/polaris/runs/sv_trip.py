# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import multiprocessing
from pathlib import Path
from typing import Optional

import numpy as np
from polaris.runs.polaris_inputs import PolarisInputs
from polaris.utils.logging_utils import function_logging


@function_logging("    Exporting SV Trips")
def export_sv_trip(
    inputs: PolarisInputs, num_threads: int, subset_id=None, trip_ids_to_run=None, output_dir: Optional[Path] = None
):
    from SVTrip.svtrip import SVTrip

    svtrip = SVTrip()

    svtrip.parameters.execution.n_workers = num_threads
    svtrip.parameters.execution.jobs_per_thread = 15

    if subset_id is not None:
        subset_id, num_subsets = subset_id
    else:
        subset_id, num_subsets = (1, 1)

    iteration_dir = inputs.demand_db.parent
    output_dir = output_dir or iteration_dir / f"sv_trip_outputs_{subset_id}_of_{num_subsets}"
    output_dir.mkdir()
    (output_dir / f"based_on_{iteration_dir.name}").touch()
    svtrip.parameters.output.export_folder = output_dir

    svtrip.load_trips_from_polaris(inputs.demand_db, inputs.supply_db)
    if num_subsets > 1:
        trip_ids_to_run = [i for i in svtrip.list_trip_ids() if (i % num_subsets) == (subset_id - 1)]
    if trip_ids_to_run is not None:
        svtrip.isolate_trips(trip_ids_to_run)

    np.random.seed(123)
    svtrip.run()
    (output_dir / "svtrip_finished").touch()
    svtrip.logger.critical("FINISHED")
