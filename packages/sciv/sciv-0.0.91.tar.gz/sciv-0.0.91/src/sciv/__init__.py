# -*- coding: UTF-8 -*-

import os
import sys

from . import file as fl
from . import model as ml
from . import plot as pl
from . import preprocessing as pp
from . import tool as tl
from . import util as ul

os.environ['OPENBLAS_NUM_THREADS'] = '1'
sys.setrecursionlimit(1000)

__version__ = f"{ul.project_name}: v{ul.project_version}"
__cache__ = ul.project_cache_path
