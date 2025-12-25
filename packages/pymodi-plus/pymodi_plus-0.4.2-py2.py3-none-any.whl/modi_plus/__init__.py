"""Top-level package for pyMODI+."""
from modi_plus import about
from modi_plus.modi_plus import (
    MODIPlus,
)

__all__ = [
    "MODIPlus",
]

__version__ = about.__version__

print(f"Running PyMODI+ (v{__version__})")
