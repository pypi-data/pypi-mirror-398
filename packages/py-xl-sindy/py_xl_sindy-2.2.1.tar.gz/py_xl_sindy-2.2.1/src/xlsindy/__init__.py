import importlib.metadata

__version__ = importlib.metadata.version("py-xl-sindy")

from . import symbolic_util
from . import dynamics_modeling
from . import euler_lagrange
from . import optimization
from . import render
from . import simulation
from . import result_formatting
from . import utils
from . import catalog
from . import catalog_base
from . import logger

__all__ = [
    "symbolic_util",
    "dynamics_modeling",
    "euler_lagrange",
    "optimization",
    "render",
    "simulation",
    "result_formatting",
    "utils",
    "catalog",
    "catalog_base",
    "logger",
]
