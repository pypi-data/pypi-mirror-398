__author__ = "Titouan Le Gourrierec"
__email__ = "titouanlegourrierec@icloud.com"
__license__ = "MIT"
__description__ = "A Python package to simplify downloading and processing elevation data."


from importlib.metadata import PackageNotFoundError, version

from . import settings  # noqa F401
from .get_elev_raster import get_elev_raster
from .raster import Raster  # noqa F401

try :
    __version__ = version(__name__)
except PackageNotFoundError :
    __version__ = "unknown"

__all__ = ["get_elev_raster", "Raster", "settings"]
