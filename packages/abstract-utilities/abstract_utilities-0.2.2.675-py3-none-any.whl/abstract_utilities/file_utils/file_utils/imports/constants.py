from .imports import *
from .module_imports import *
@dataclass
class ScanConfig:
    allowed_exts: Set[str]
    unallowed_exts: Set[str]
    exclude_types: Set[str]
    exclude_dirs: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
DEFAULT_ALLOWED_EXTS: Set[str] = {
    ".py", ".pyw",                             # python
    ".js", ".jsx", ".ts", ".tsx", ".mjs",      # JS/TS
    ".html", ".htm", ".xml",                   # markup
    ".css", ".scss", ".sass", ".less",         # styles
    ".json", ".yaml", ".yml", ".toml", ".ini",  # configs
    ".cfg", ".md", ".markdown", ".rst",        # docs
    ".sh", ".bash", ".env",                    # scripts/env
    ".txt"                                     # plain text
}

DEFAULT_EXCLUDE_TYPES: Set[str] = {
    "image", "video", "audio", "presentation",
    "spreadsheet", "archive", "executable"
}

# never want these—even if they sneak into ALLOWED
_unallowed = set(get_media_exts(DEFAULT_EXCLUDE_TYPES)) | {'.bak', '.shp', '.cpg', '.dbf', '.shx','.geojson',".pyc",'.shx','.geojson','.prj','.sbn','.sbx'}
DEFAULT_UNALLOWED_EXTS = {e for e in _unallowed if e not in DEFAULT_ALLOWED_EXTS}

DEFAULT_EXCLUDE_DIRS: Set[str] = {
    "node_modules", "old","__pycache__", "backups", "backup", "backs", "trash", "depriciated", "old", "__init__"
}

DEFAULT_EXCLUDE_PATTERNS: Set[str] = {
    "__init__*", "*.tmp", "*.log", "*.lock", "*.zip","*~"
}
REMOTE_RE = re.compile(r"^(?P<host>[^:\s]+@[^:\s]+):(?P<path>/.*)$")
AllowedPredicate = Optional[Callable[[str], bool]]
DEFAULT_EXCLUDE_FILE_PATTERNS=DEFAULT_EXCLUDE_PATTERNS
