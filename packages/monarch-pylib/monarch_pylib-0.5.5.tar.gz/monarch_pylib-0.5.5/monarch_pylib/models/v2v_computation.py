# import numpy as np
# from numpy.typing import NDArray


# def v2v_compile_time(
#     v_k: NDArray[np.float_],
#     u_k_target: NDArray[np.float_],
#     W_k: NDArray[np.float_],
#     f_target: float,
# ) -> float:
#     """
#     Computes V2V compile time.
#     Formula (9):
#         t_compile = Σ_k  v_k * (1 - u_k_target) * (W_k / f_target)
#     """
#     total = 0.0
#     for i in range(v_k.size):
#         total += v_k[i] * (1 - u_k_target[i]) * (W_k[i] / f_target)
#     return total


# def v2v_process_time(C: float, f_target: float) -> float:
#     """
#     Computes V2V processing time.
#     Formula (10):
#         t_process = C / f_target
#     """
#     return C / f_target


# def v2v_total_time(
#     v_k: NDArray[np.float_],
#     u_k_target: NDArray[np.float_],
#     W_k: NDArray[np.float_],
#     C: float,
#     f_target: float,
# ) -> float:
#     """
#     Computes total V2V execution time.
#     Formula (11):
#         t_total = t_compile + t_process
#     """
#     t_compile = v2v_compile_time(v_k, u_k_target, W_k, f_target)
#     t_process = v2v_process_time(C, f_target)
#     return t_compile + t_process


# def v2v_energy(
#     v_k: NDArray[np.float_],
#     u_k_target: NDArray[np.float_],
#     W_k: NDArray[np.float_],
#     C: float,
#     f_target: float,
#     kappa: float,
# ) -> float:
#     """
#     Computes V2V energy consumption.
#     Formula (12):
#         e = Σ_k v_k * (1 - u_k_target) * kappa * f_target^2 * W_k
#             + kappa * f_target^2 * C
#     """
#     total = 0.0

#     # Part 1: energy for fetched services
#     for i in range(v_k.size):
#         total += v_k[i] * (1 - u_k_target[i]) * kappa * (f_target * f_target) * W_k[i]

#     # Part 2: energy for task itself
#     total += kappa * (f_target * f_target) * C

#     return total


# class V2VComputationModel:
#     """
#     V2V offloading model:
#         - compile time
#         - processing time
#         - total time
#         - energy consumption
#     """

#     def __init__(self, kappa: float) -> None:
#         self.kappa = kappa

#     def compile_time(
#         self,
#         v_k: NDArray[np.float_],
#         u_k_target: NDArray[np.float_],
#         W_k: NDArray[np.float_],
#         f_target: float,
#     ) -> float:
#         return float(v2v_compile_time(v_k, u_k_target, W_k, f_target))

#     def process_time(self, C: float, f_target: float) -> float:
#         return float(v2v_process_time(C, f_target))

#     def total_time(
#         self,
#         v_k: NDArray[np.float_],
#         u_k_target: NDArray[np.float_],
#         W_k: NDArray[np.float_],
#         C: float,
#         f_target: float,
#     ) -> float:
#         return float(v2v_total_time(v_k, u_k_target, W_k, C, f_target))

#     def energy(
#         self,
#         v_k: NDArray[np.float_],
#         u_k_target: NDArray[np.float_],
#         W_k: NDArray[np.float_],
#         C: float,
#         f_target: float,
#     ) -> float:
#         return float(v2v_energy(v_k, u_k_target, W_k, C, f_target, self.kappa))
