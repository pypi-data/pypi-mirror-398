# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from dataclasses import dataclass

import numpy as np


@dataclass
class PathResults:
    travel_time: float
    departure: int
    links: np.ndarray
    link_directions: np.ndarray
    cumulative_time: np.ndarray
