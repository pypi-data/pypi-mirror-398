from .imports import *
from .filter_params import *
from .file_utils import *
##from abstract_utilities import make_list,get_media_exts, is_media_type

def collect_filepaths(
    directory: List[str],
    cfg: ScanConfig=None,
    allowed_exts: Optional[Set[str]] = False,
    unallowed_exts: Optional[Set[str]] = False,
    exclude_types: Optional[Set[str]] = False,
    exclude_dirs: Optional[List[str]] = False,
    exclude_patterns: Optional[List[str]] = False,
    add=False,
    allowed: Optional[Callable[[str], bool]] = None,
    **kwargs
    ) -> List[str]:
    cfg = cfg or define_defaults(
                                allowed_exts=allowed_exts,
                                unallowed_exts=unallowed_exts,
                                exclude_types=exclude_types,
                                exclude_dirs=exclude_dirs,
                                exclude_patterns=exclude_patterns,
                                add = add
                                )
    allowed = allowed or make_allowed_predicate(cfg)
    directories = make_list(directory)
    roots = [r for r in directories if r]

    # your existing helpers (get_dirs, get_globs, etc.) stay the same
    original_dirs = get_allowed_dirs(roots, allowed=allowed)
    original_globs = get_globs(original_dirs)
    files = get_allowed_files(original_globs, allowed=allowed)

    for d in get_filtered_dirs(original_dirs, allowed=allowed):
        files += get_filtered_files(d, allowed=allowed, files=files)

    # de-dupe while preserving order
    seen, out = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _fast_walk(
    root: Path,
    exts: Iterable[str],
    skip_dirs: Iterable[str] = (),
    skip_patterns: Iterable[str] = (),
) -> List[Path]:
    exts = tuple(exts)
    skip_dirs = set(sd.lower() for sd in skip_dirs or ())
    skip_patterns = tuple(sp.lower() for sp in (skip_patterns or ()))

    out = []
    for p in root.rglob("*"):
        # skip directories by name hit
        if p.is_dir():
            name = p.name.lower()
            if name in skip_dirs:
                # rglob doesn't let us prune mid-iteration cleanly; we just won't collect under it
                continue
            # nothing to collect for dirs
            continue

        # file filters
        name = p.name.lower()
        if any(fnmatch.fnmatch(name, pat) for pat in skip_patterns):
            continue
        if p.suffix.lower() in exts:
            out.append(p)

    # de-dup and normalize
    return sorted({pp.resolve() for pp in out})


def enumerate_source_files(
    src_root: Path,
    cfg: Optional["ScanConfig"] = None,
    *,
    exts: Optional[Iterable[str]] = None,
    fast_skip_dirs: Optional[Iterable[str]] = None,
    fast_skip_patterns: Optional[Iterable[str]] = None,
) -> List[Path]:
    """
    Unified enumerator:
      - If `cfg` is provided: use collect_filepaths(...) with full rules.
      - Else: fast walk using rglob over `exts` (defaults to EXTS) with optional light excludes.
    """
    src_root = Path(src_root)

    if cfg is not None:
        files = collect_filepaths([str(src_root)], cfg=cfg)
        return sorted({Path(f).resolve() for f in files})

    # Fast mode
    return _fast_walk(
        src_root,
        exts or EXTS,
        skip_dirs=fast_skip_dirs or (),
        skip_patterns=fast_skip_patterns or (),
    )
