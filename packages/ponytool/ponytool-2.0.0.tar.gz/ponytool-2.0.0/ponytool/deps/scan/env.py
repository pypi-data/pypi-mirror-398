import sys
from pathlib import Path

WARN_MSG = "Virtual environment is not active"

def get_active_python() -> Path:
    if sys.prefix == sys.base_prefix:
        raise RuntimeError(WARN_MSG)
    return Path(sys.executable)


def get_active_venv() -> Path:
    if sys.prefix == sys.base_prefix:
        raise RuntimeError(WARN_MSG)
    return Path(sys.prefix)
