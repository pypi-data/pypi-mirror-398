# remote_fs.py
from __future__ import annotations
from typing import *
import subprocess, shlex, os, fnmatch, glob, posixpath, re
# ---- import your existing pieces ----
from ...type_utils import make_list  # whatever you already have
from ...time_utils import get_sleep
from ...ssh_utils import *
from ...env_utils import *
from ...string_clean import eatOuter
