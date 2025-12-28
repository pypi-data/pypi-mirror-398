from dataclasses import is_dataclass
from typing import get_type_hints
from functools import wraps


def type(dc_type, return_type):
    dc_fields = get_type_hints(dc_type)

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not args or not isinstance(args[0], dc_type):
                raise TypeError("first argument must be dataclass instance")

            spec = args[0]

            for name, tp in dc_fields.items():
                val = getattr(spec, name)
                if not isinstance(val, tp):
                    raise TypeError(f"{name} must be {tp}")

            out = fn(*args, **kwargs)

            if not isinstance(out, return_type):
                raise TypeError(f"return must be {return_type}")

            return out

        return wrapper

    if not is_dataclass(dc_type):
        raise TypeError("dc_type must be dataclass")

    return decorator
