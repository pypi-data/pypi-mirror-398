from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class Distance3DInput:
    x_m: float
    y_m: float
    h_m: float
    x_n: float
    y_n: float
    h_n: float


@dataclass
class Distance2DInput:
    x_m: float
    y_m: float
    x_n: float
    y_n: float


@dataclass
class Distance1DInput:
    x_m: float
    x_n: float


@dataclass
class SpeedVehicle:
    path_len_m: float
    sim_time_s: float


@dataclass
class CurrentPosition:
    total_sim_time_s: float
    now_time_s: float
    path_xy: Sequence[Sequence[float]]


@dataclass
class PathLength:
    path_xy: Sequence[Sequence[float]]
