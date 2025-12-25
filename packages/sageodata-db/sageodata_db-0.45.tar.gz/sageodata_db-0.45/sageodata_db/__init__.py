import importlib.metadata

__version__ = importlib.metadata.version(__name__)

from sageodata_db.utils import *
from sageodata_db.config import *
from sageodata_db.connection import *

import warnings

warnings.filterwarnings("ignore", module="pandas.io.sql", lineno=758)
