"""
MinFX.

This package provides core functionality for the minfx system.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("minfx")
except PackageNotFoundError:
    __version__ = "unknown"

__author__ = "Minfx Technologies, s.r.o."
__email__ = "contact@minfx.ai"

# Package level imports can be added here as the package grows
# Neptune v2 (legacy) is available as minfx.neptune_v2
# Neptune v3 (scale) is available as minfx.neptune_v3
