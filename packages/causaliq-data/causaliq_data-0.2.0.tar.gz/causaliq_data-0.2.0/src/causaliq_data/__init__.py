"""
causaliq-data: Data handling for causal discovery and BN fitting.
"""

from causaliq_data.data import Data, DatasetType, VariableType
from causaliq_data.numpy import NumPy
from causaliq_data.oracle import Oracle
from causaliq_data.pandas import Pandas

__version__ = "0.2.0"
__author__ = "CausalIQ"
__email__ = "info@causaliq.com"

# Package metadata
__title__ = "causaliq-data"
__description__ = "Data handling for causal discovery and BN fitting"

__url__ = "https://github.com/causaliq/causaliq-data"
__license__ = "MIT"

# Version tuple for programmatic access
VERSION = tuple(map(int, __version__.split(".")))

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "VERSION",
    "Data",
    "DatasetType",
    "VariableType",
    "Pandas",
    "NumPy",
    "Oracle",
]
