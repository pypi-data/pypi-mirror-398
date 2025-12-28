from dataclasses import is_dataclass
from typing import get_type_hints, get_origin, get_args
from functools import wraps
import inspect
import numbers
import numpy as np


def _is_instance(val, tp) -> bool:
    """
    Minimal runtime type checker:
    - supports Union/Optional
    - supports basic list/tuple container checks (shallow)
    - treats float as (int/float/numpy floating) if you want numeric-friendly behavior
    """
    origin = get_origin(tp)
    args = get_args(tp)

    if (
        origin is None
        and hasattr(tp, "__args__")
        and str(tp).startswith("typing.Union")
    ):
        origin = getattr(tp, "__origin__", None)
        args = getattr(tp, "__args__", ())

    if origin is inspect._empty:
        return True

    if origin is None:
        if tp is float:
            return isinstance(val, (numbers.Real, np.floating)) and not isinstance(
                val, bool
            )
        if tp is int:
            return isinstance(val, (numbers.Integral, np.integer)) and not isinstance(
                val, bool
            )
        if tp is bool:
            return isinstance(val, bool)
        return isinstance(val, tp)

    if origin is list:
        if not isinstance(val, list):
            return False
        if not args:
            return True
        return all(_is_instance(x, args[0]) for x in val)

    if origin is tuple:
        if not isinstance(val, tuple):
            return False
        if not args:
            return True
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_is_instance(x, args[0]) for x in val)
        if len(val) != len(args):
            return False
        return all(_is_instance(x, tpx) for x, tpx in zip(val, args))

    if origin is type(None):
        return val is None

    if origin is getattr(__import__("typing"), "Union", None):
        return any(_is_instance(val, tpx) for tpx in args)

    try:
        return isinstance(val, origin)
    except TypeError:
        return True


def type_decorator(dc_type, return_type):
    if not is_dataclass(dc_type):
        raise TypeError("dc_type must be dataclass")

    dc_fields = get_type_hints(dc_type)

    def decorator(fn):
        sig = inspect.signature(fn)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            for name, tp in dc_fields.items():
                if name not in bound.arguments:
                    raise TypeError(f"missing required argument: {name}")
                val = bound.arguments[name]
                if not _is_instance(val, tp):
                    raise TypeError(f"{name} must be {tp}")

            out = fn(*args, **kwargs)

            if return_type is float:
                if not isinstance(out, (numbers.Real, np.floating)) or isinstance(
                    out, bool
                ):
                    raise TypeError("return must be float-like")
                return float(out)

            if not isinstance(out, return_type):
                raise TypeError(f"return must be {return_type}")

            return out

        return wrapper

    return decorator
