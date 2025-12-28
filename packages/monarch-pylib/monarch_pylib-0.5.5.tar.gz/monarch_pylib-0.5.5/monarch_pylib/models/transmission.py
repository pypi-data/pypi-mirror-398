from dataclasses import dataclass
from typing import Union, Callable, Any, Type, Sequence, Tuple
from monarch_pylib.decorator.type import type_decorator
from monarch_pylib.type.transmission_type import (
    CurrentPosition,
    Distance1DInput,
    Distance2DInput,
    Distance3DInput,
    PathLength,
    SpeedVehicle,
)


# def type_decorator(
#     dc_type, return_type
# ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
#     """
#     Minimal decorator factory that acts as a no-op wrapper for functions while
#     preserving metadata; accepts the same parameters used in the module.
#     """

#     def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             return func(*args, **kwargs)

#         return wrapper

#     return decorator


# # -----------------------------
# # (3) Channel gain (path loss + fading factors)
# # -----------------------------
# @dataclass
# class ChannelGainV2IInput:
#     tau_nm: ScalarLike
#     rho: ScalarLike
#     varpi_nm: ScalarLike
#     d_nm: ScalarLike
#     gamma: ScalarLike


# @type_decorator(
#     dc_type=ChannelGainV2IInput,
#     return_type=float,
# )
# def channel_gain_v2i(
#     tau_nm: ScalarLike,
#     rho: ScalarLike,
#     varpi_nm: ScalarLike,
#     d_nm: ScalarLike,
#     gamma: ScalarLike,
# ) -> float:
#     """
#     Name:
#         V2I channel gain

#     Description:
#         Computes the channel gain for a V2I link using fading factors and distance-based path loss.

#     Meaning:
#         - tau_nm: small-scale fading between vehicle n and RSU/MEC m
#         - rho: path loss reference factor
#         - varpi_nm: large-scale fading / shadowing factor
#         - d_nm: 3D distance between n and m
#         - gamma: path loss exponent
#     """
#     tau_ = _as_float_scalar(tau_nm, "tau_nm")
#     rho_ = _as_float_scalar(rho, "rho")
#     varpi_ = _as_float_scalar(varpi_nm, "varpi_nm")
#     d_ = _as_float_scalar(d_nm, "d_nm")
#     gamma_ = _as_float_scalar(gamma, "gamma")

#     if d_ <= 0.0:
#         raise ValueError("d_nm must be > 0 to compute path-loss based channel gain.")

#     return float(tau_ * rho_ * varpi_ * (d_ ** (-gamma_)))


# # -----------------------------
# # (2) Uplink rate (generic; use for V2I/V2V by passing proper G and V)
# # -----------------------------
# @dataclass
# class UplinkRateInput:
#     B: ScalarLike
#     V_m: ScalarLike
#     p_n: ScalarLike
#     G_nm: ScalarLike
#     noise_power: ScalarLike


# @type_decorator(
#     dc_type=UplinkRateInput,
#     return_type=float,
# )
# def uplink_rate(
#     B: ScalarLike,
#     V_m: ScalarLike,
#     p_n: ScalarLike,
#     G_nm: ScalarLike,
#     noise_power: ScalarLike,
# ) -> float:
#     """
#     Name:
#         Uplink rate

#     Description:
#         Computes the uplink transmission rate using Shannon capacity-like formula.

#     Meaning:
#         - B: bandwidth
#         - V_m: resource sharing factor (e.g., number of vehicles sharing)
#         - p_n: transmit power of vehicle n
#         - G_nm: channel gain between n and m
#         - noise_power: noise power (delta^2)
#     """
#     B_ = _as_float_scalar(B, "B")
#     V_ = _as_float_scalar(V_m, "V_m")
#     p_ = _as_float_scalar(p_n, "p_n")
#     G_ = _as_float_scalar(G_nm, "G_nm")
#     n2_ = _as_float_scalar(noise_power, "noise_power")

#     if V_ <= 0.0:
#         raise ValueError("V_m must be > 0.")
#     if n2_ <= 0.0:
#         raise ValueError("noise_power must be > 0.")

#     snr = (p_ * G_) / n2_

#     # Numerically stable: log2(1+snr) = log1p(snr)/log(2)
#     return float((B_ / V_) * (np.log1p(snr) / np.log(2.0)))


# # Semantic aliases (same math; clearer names)
# @dataclass
# class UplinkRateV2IInput(UplinkRateInput):
#     pass


# @type_decorator(
#     dc_type=UplinkRateV2IInput,
#     return_type=float,
# )
# def uplink_rate_v2i(
#     B: ScalarLike,
#     V_m: ScalarLike,
#     p_n: ScalarLike,
#     G_nm: ScalarLike,
#     noise_power: ScalarLike,
# ) -> float:
#     """
#     Name:
#         V2I uplink rate

#     Description:
#         Computes the uplink rate from vehicle n to RSU/MEC m (V2I).

#     Meaning:
#         - B: bandwidth
#         - V_m: resource sharing factor at RSU/MEC side
#         - p_n: transmit power of vehicle n
#         - G_nm: V2I channel gain
#         - noise_power: noise power (delta^2)
#     """
#     return uplink_rate(B=B, V_m=V_m, p_n=p_n, G_nm=G_nm, noise_power=noise_power)


# @dataclass
# class UplinkRateV2VInput(UplinkRateInput):
#     pass


# @type_decorator(
#     dc_type=UplinkRateV2VInput,
#     return_type=float,
# )
# def uplink_rate_v2v(
#     B: ScalarLike,
#     V_m: ScalarLike,
#     p_n: ScalarLike,
#     G_nm: ScalarLike,
#     noise_power: ScalarLike,
# ) -> float:
#     """
#     Name:
#         V2V uplink rate

#     Description:
#         Computes the uplink rate from vehicle n to a target cooperative vehicle (V2V).

#     Meaning:
#         - B: bandwidth
#         - V_m: resource sharing factor for V2V link (if applicable)
#         - p_n: transmit power of vehicle n
#         - G_nm: V2V channel gain (use the appropriate gain model)
#         - noise_power: noise power (delta^2)
#     """
#     return uplink_rate(B=B, V_m=V_m, p_n=p_n, G_nm=G_nm, noise_power=noise_power)


# # -----------------------------
# # (5) Transmission time
# # -----------------------------
# @dataclass
# class TransmissionTimeInput:
#     D_nij: ScalarLike
#     R_nx: ScalarLike


# @type_decorator(
#     dc_type=TransmissionTimeInput,
#     return_type=float,
# )
# def transmission_time(D_nij: ScalarLike, R_nx: ScalarLike) -> float:
#     """
#     Name:
#         Transmission time

#     Description:
#         Computes the time needed to transmit intermediate data between tasks over a link.

#     Meaning:
#         - D_nij: data size to transmit (bits/bytes; keep consistent across the project)
#         - R_nx: transmission rate of the link
#     """
#     D_ = _as_float_scalar(D_nij, "D_nij")
#     R_ = _as_float_scalar(R_nx, "R_nx")

#     if R_ <= 0.0:
#         raise ValueError("R_nx must be > 0.")

#     return float(D_ / R_)


# # -----------------------------
# # (6) Transmission energy
# # -----------------------------
# @dataclass
# class TransmissionEnergyInput:
#     p_n: ScalarLike
#     D_nij: ScalarLike
#     R_nx: ScalarLike


# @type_decorator(
#     dc_type=TransmissionEnergyInput,
#     return_type=float,
# )
# def transmission_energy(p_n: ScalarLike, D_nij: ScalarLike, R_nx: ScalarLike) -> float:
#     """
#     Name:
#         Transmission energy

#     Description:
#         Computes the transmission energy using E = p * t, where t = D / R.

#     Meaning:
#         - p_n: transmit power of vehicle n
#         - D_nij: data size to transmit
#         - R_nx: transmission rate of the link
#     """
#     p_ = _as_float_scalar(p_n, "p_n")
#     t = transmission_time(D_nij=D_nij, R_nx=R_nx)
#     return float(p_ * t)


@type_decorator(
    dc_type=Distance3DInput,
    return_type=float,
)
def distance_3d(
    x_m: float, y_m: float, h_m: float, x_n: float, y_n: float, h_n: float
) -> float:
    """
    Name:
        3D distance

    Description:
        Computes the 3D Euclidean distance between transmitter (n) and receiver (m).

    Meaning:
        - x_m, y_m, h_m: receiver coordinates (e.g., RSU/MEC or target vehicle)
        - x_n, y_n, h_n: transmitter coordinates (vehicle n)
    """
    dx = x_m - x_n
    dy = y_m - y_n
    dh = h_m - h_n

    return float((dx * dx + dy * dy + dh * dh) ** 0.5)


@type_decorator(
    dc_type=Distance2DInput,
    return_type=float,
)
def distance_2d(x_m: float, y_m: float, x_n: float, y_n: float) -> float:
    """
    Name:
        2D distance

    Description:
        Computes the 2D Euclidean distance between transmitter (n) and receiver (m).

    Meaning:
        - x_m, y_m: receiver coordinates (e.g., RSU/MEC or target vehicle)
        - x_n, y_n: transmitter coordinates (vehicle n)
    """
    dx = x_m - x_n
    dy = y_m - y_n

    return float((dx * dx + dy * dy) ** 0.5)


@type_decorator(
    dc_type=Distance1DInput,
    return_type=float,
)
def distance_1d(x_m: float, x_n: float) -> float:
    """
    Name:
        1D distance

    Description:
        Computes the 1D distance between transmitter (n) and receiver (m).

    Meaning:
        - x_m: receiver coordinate (e.g., RSU/MEC or target vehicle)
        - x_n: transmitter coordinate (vehicle n)
    """
    dx = x_m - x_n

    return float(abs(dx))


@type_decorator(
    dc_type=SpeedVehicle,
    return_type=float,
)
def speed_vehicle(path_len_m: float, sim_time_s: float) -> float:
    """
    Name:
        Speed (from path length & simulation time)

    Description:
        Computes average speed based on traveled path length and simulation time.

    Meaning:
        - path_len_m: traveled path length (meters)
        - sim_time_s: simulation time elapsed (seconds)

    Formula:
        v = s / t
    """
    if sim_time_s <= 0.0:
        return 0.0

    return float(path_len_m / sim_time_s)


@type_decorator(
    dc_type=CurrentPosition,
    return_type=tuple,
)
def current_position(
    total_sim_time_s: float,
    now_time_s: float,
    path_xy: Sequence[Sequence[float]],
) -> Tuple[float, float]:
    """
    Name:
        Current position (x,y)

    Description:
        Returns current (x,y) on the polyline path based on simulation time,
        assuming uniform progress along the path.

    Meaning:
        - total_sim_time_s: total simulation duration (seconds)
        - now_time_s: current time (seconds)
        - path_xy: path points as [[x,y], ...]
    """
    if not path_xy:
        raise ValueError("path_xy is empty")
    if len(path_xy) == 1 or total_sim_time_s <= 0.0:
        return float(path_xy[0][0]), float(path_xy[0][1])

    p = now_time_s / total_sim_time_s
    if p <= 0.0:
        return float(path_xy[0][0]), float(path_xy[0][1])
    if p >= 1.0:
        return float(path_xy[-1][0]), float(path_xy[-1][1])

    seg_lens = []
    total_len = 0.0
    for i in range(len(path_xy) - 1):
        x1, y1 = float(path_xy[i][0]), float(path_xy[i][1])
        x2, y2 = float(path_xy[i + 1][0]), float(path_xy[i + 1][1])
        dx, dy = x2 - x1, y2 - y1
        L = (dx * dx + dy * dy) ** 0.5
        seg_lens.append(L)
        total_len += L

    if total_len <= 0.0:
        return float(path_xy[0][0]), float(path_xy[0][1])

    d = p * total_len

    acc = 0.0
    for i, L in enumerate(seg_lens):
        if d <= acc + L or i == len(seg_lens) - 1:
            x1, y1 = float(path_xy[i][0]), float(path_xy[i][1])
            x2, y2 = float(path_xy[i + 1][0]), float(path_xy[i + 1][1])
            if L <= 0.0:
                return x1, y1
            r = (d - acc) / L
            return float(x1 + r * (x2 - x1)), float(y1 + r * (y2 - y1))
        acc += L

    return float(path_xy[-1][0]), float(path_xy[-1][1])


@type_decorator(
    dc_type=PathLength,
    return_type=float,
)
def path_length_2d(path_xy: Sequence[Sequence[float]]) -> float:
    """
    Name:
        Path length (2D)

    Description:
        Computes total length of a 2D polyline path.

    Meaning:
        - path_xy: array of [x,y] points describing the path
    """
    if not path_xy or len(path_xy) < 2:
        return 0.0

    total = 0.0
    for i in range(len(path_xy) - 1):
        x1, y1 = float(path_xy[i][0]), float(path_xy[i][1])
        x2, y2 = float(path_xy[i + 1][0]), float(path_xy[i + 1][1])
        dx = x2 - x1
        dy = y2 - y1
        total += (dx * dx + dy * dy) ** 0.5

    return float(total)
