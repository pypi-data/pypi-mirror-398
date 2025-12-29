# ============================================================
# abstract_utilities/imports/imports.py
# Global imports hub — everything imported here will be
# automatically available to any module that does:
#     from ..imports import *
# ============================================================
# ---- Core standard library modules -------------------------
import os, sys, re, shlex, glob, platform, textwrap, subprocess, inspect, json, time
import tempfile, shutil, logging, pathlib, fnmatch, importlib, importlib.util, types
from pathlib import Path
from datetime import datetime
from types import ModuleType

# ---- Dataclasses and typing --------------------------------
from dataclasses import dataclass, field
from typing import (
    Any, Optional, List, Dict, Set, Tuple,
    Iterable, Callable, Literal, Union, TypeVar
)

# ---- Common 3rd-party dependencies --------------------------
import pandas as pd
import geopandas as gpd
import pytesseract
import pdfplumber
import PyPDF2
import ezodf
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# ---- Helpers ------------------------------------------------
import textwrap as tw
from pprint import pprint

# ============================================================
# AUTO-EXPORT ALL NON-PRIVATE NAMES
# ============================================================
__all__ = [name for name in globals() if not name.startswith("_")]
