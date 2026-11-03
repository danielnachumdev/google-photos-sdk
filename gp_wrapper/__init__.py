from importlib.metadata import version

from .utils.structures import *
from .utils.pbar import ProgressBar
from .objects import *

# Always matches the installed distribution (CD stamps pyproject version into the wheel).
__version__ = version("gp_wrapper")
