from typing import Any

_np: Any = None

try:
    import numpy as _np
except ImportError:
    _np = None


def __getattr__(name):
    if _np is None:
        raise ImportError("Numpy is not installed. Please install numpy to use this feature: altbacken[numpy].")
    return getattr(_np, name)