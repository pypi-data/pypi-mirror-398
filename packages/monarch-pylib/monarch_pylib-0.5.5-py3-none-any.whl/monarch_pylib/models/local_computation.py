# import numpy as np
# from numba import njit


# @njit
# def local_time(C: float, f: float) -> float:
#     """
#     Name:
#         Local execution time

#     Description:
#         Computes local execution time for a task on a vehicle

#     Meaning:
#         - C: required CPU cycles of task
#         - f: CPU frequency of vehicle
#     """
#     return C / f


# @njit
# def local_energy(C: float, f: float, kappa: float) -> float:
#     """
#     Name:
#         Local energy consumption

#     Description:
#         Computes local energy consumption for a task on a vehicle
#     """
#     return kappa * (f * f) * C
