from typing import Any

_loguru: Any = None

try:
    import loguru as _loguru
except ImportError:
    _loguru = None


def __getattr__(name):
    if _loguru is None:
        raise ImportError("Loguru is not installed. Please install loguru to use this feature: altbacken[loguru].")
    return getattr(_loguru, name)