"""
Neptune integration for MinFX.

This module temporarily re-exports the neptune package, allowing it to be accessed as:
    import minfx.neptune
"""

from neptune import *
import neptune as _neptune

# Re-export the neptune module's attributes
__all__ = getattr(_neptune, '__all__', [name for name in dir(_neptune) if not name.startswith('_')])

# Make the module behave like neptune when accessed
import sys
sys.modules[__name__].__dict__.update({
    name: getattr(_neptune, name) 
    for name in dir(_neptune) 
    if not name.startswith('_')
})

