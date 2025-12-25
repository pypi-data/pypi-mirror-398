# -*- coding: utf-8
"""REMix energy system optimization framework"""

import importlib.metadata

__version__ = importlib.metadata.version("remix.framework")


import importlib.resources
import os
import sys
import warnings
from pathlib import Path

if sys.version_info[1] < 11:
    msg = "Support for Python versions below 3.10 will be dropped with REMix version 0.14.0."
    warnings.warn(FutureWarning(msg))

__gamscode__ = os.path.join(importlib.resources.files("remix.framework"), "model")
__testingpath__ = Path(__gamscode__).parent.parent.parent / "testing"
__remixhome__ = os.path.join(os.path.expanduser("~"), ".remix")
__versionhome__ = os.path.join(os.path.expanduser("~"), ".remix", __version__)

# put imports of api commands to remix.framework top level
from .api.instance import Instance as Instance
from .api.run import run_remix as run_remix
from .tools.gdx import GDXEval as GDXEval
from .tools.utilities import read_dat as read_dat
