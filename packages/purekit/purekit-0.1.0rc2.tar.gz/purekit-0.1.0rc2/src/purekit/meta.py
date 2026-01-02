__all__ = ("get_caller_module", "get_caller_name", "get_caller_varname")

import inspect


def get_caller_module(depth: int = 1) -> str:
    """Return the module name of the calling frame; depth=1 is the immediate caller."""
    if depth < 1:
        raise ValueError(f"invalid {depth=!r}; expected >= 1")

    frame = inspect.currentframe()
    try:
        caller = frame
        for _ in range(depth):
            caller = caller.f_back if caller is not None else None
        if caller is None:
            raise RuntimeError("expected to be executed within a function")
        return caller.f_globals.get("__name__", "<unknown>")
    finally:
        del frame


def get_caller_name(depth: int = 1) -> str:
    """Return the name of the calling function; depth=1 is the immediate caller."""
    if depth < 1:
        raise ValueError(f"invalid {depth=!r}; expected >= 1")

    frame = inspect.currentframe()
    try:
        caller = frame
        for _ in range(depth):
            caller = caller.f_back if caller is not None else None
        if caller is None:
            raise RuntimeError("expected to be executed within a function")
        return caller.f_code.co_name
    finally:
        del frame


def get_caller_varname(target: object, depth: int = 1) -> str:
    """Return the caller-local name bound to the given object."""
    if depth < 1:
        raise ValueError(f"invalid {depth=!r}; expected >= 1")

    frame = inspect.currentframe()
    try:
        caller = frame
        for _ in range(depth):
            caller = caller.f_back if caller is not None else None
        if caller is None:
            raise RuntimeError("expected to be executed within a function")

        for name, val in caller.f_locals.items():
            if val is target:
                return name

        raise ValueError("name not found")
    finally:
        del frame
