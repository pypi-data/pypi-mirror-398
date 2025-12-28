from monarch_pylib.decorator.type import type_decorator


@type_decorator(
    dc_type=None,
    return_type=float,
)
def v2v_compile_time(v_k: list, u_k_target: list, W_k: list, f_target: float) -> float:
    """
    Name:
        V2V compile time

    Description:
        Computes the compile time for service dependencies when offloading to a cooperative car.

    Meaning:
        - v_k: required service flags for the task
        - u_k_target: services already stored in target vehicle cache
        - W_k: cycles needed to load each service
        - f_target: CPU frequency of the target vehicle
    """
    total = 0.0
    for i in range(len(v_k)):
        total += v_k[i] * (1 - u_k_target[i]) * (W_k[i] / f_target)
    return total


def v2v_process_time(C: float, f_target: float) -> float:
    """
    Name:
        V2V processing time

    Description:
        Computes the processing time for executing the task on a cooperative vehicle.

    Meaning:
        - C: required CPU cycles of the task
        - f_target: CPU frequency of the target vehicle
    """
    return C / f_target


def v2v_total_time(
    v_k: list, u_k_target: list, W_k: list, C: float, f_target: float
) -> float:
    """
    Name:
        Total V2V execution time

    Description:
        Computes total time for compiling required services + executing the task.

    Meaning:
        - v_k: required services
        - u_k_target: cache availability
        - W_k: load cost per service
        - C: task CPU cycles
        - f_target: CPU frequency
    """
    t_compile = v2v_compile_time(v_k, u_k_target, W_k, f_target)
    t_process = v2v_process_time(C, f_target)
    return t_compile + t_process


def v2v_energy(
    v_k: list,
    u_k_target: list,
    W_k: list,
    C: float,
    f_target: float,
    kappa: float,
) -> float:
    """
    Name:
        V2V energy consumption

    Description:
        Computes total energy consumed when executing a task on a cooperative vehicle.

    Meaning:
        - v_k: required services
        - u_k_target: service availability in cache
        - W_k: cycles to load each service
        - C: task CPU cycles
        - f_target: CPU frequency
        - kappa: energy coefficient
    """
    total = 0.0

    for i in range(len(v_k)):
        total += v_k[i] * (1 - u_k_target[i]) * kappa * (f_target * f_target) * W_k[i]

    total += kappa * (f_target * f_target) * C

    return total
