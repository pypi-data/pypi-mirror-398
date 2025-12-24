from ..imports import *
from typing import *
from dataclasses import dataclass, field
@dataclass
class ScanConfig:
    allowed_exts: Set[str]
    unallowed_exts: Set[str]
    exclude_types: Set[str]
    exclude_dirs: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
