from .imports import *
from .filter_params import *
from .file_filters import enumerate_source_files


def check_path_type(
    path: str,
    user: Optional[str] = None,
    host: Optional[str] = None,
    user_as_host: Optional[str] = None,
    use_shell: bool = False
) -> Literal["file", "directory", "missing", "unknown"]:
    """
    Determine whether a given path is a file, directory, or missing.
    Works locally or remotely (via SSH).

    Args:
        path: The path to check.
        user, host, user_as_host: SSH parameters if remote.
        use_shell: Force shell test instead of Python os.path.
    Returns:
        One of: 'file', 'directory', 'missing', or 'unknown'
    """

    # --- remote check if user/host is given ---
    if user_as_host or (user and host):
        remote_target = user_as_host or f"{user}@{host}"
        cmd = f"if [ -f '{path}' ]; then echo file; elif [ -d '{path}' ]; then echo directory; else echo missing; fi"
        try:
            result = subprocess.check_output(
                ["ssh", remote_target, cmd],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5
            ).strip()
            return result if result in ("file", "directory", "missing") else "unknown"
        except Exception:
            return "unknown"

    # --- local check ---
    if not use_shell:
        if os.path.isfile(path):
            return "file"
        elif os.path.isdir(path):
            return "directory"
        elif not os.path.exists(path):
            return "missing"
        return "unknown"
    else:
        # fallback using shell tests (useful for sandboxed contexts)
        cmd = f"if [ -f '{path}' ]; then echo file; elif [ -d '{path}' ]; then echo directory; else echo missing; fi"
        try:
            output = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.DEVNULL, text=True
            ).strip()
            return output if output in ("file", "directory", "missing") else "unknown"
        except Exception:
            return "unknown"




def get_find_cmd(
    directory: str,
    *,
    mindepth: Optional[int] = None,
    maxdepth: Optional[int] = None,
    depth: Optional[int] = None,
    file_type: Optional[str] = None,  # 'f' or 'd'
    name: Optional[str] = None,
    size: Optional[str] = None,
    mtime: Optional[str] = None,
    perm: Optional[str] = None,
    user: Optional[str] = None,
    **kwargs
) -> str:
    """Constructs a Unix `find` command string from keyword args."""
    cmd = [f"find {directory}"]

    if depth is not None:
        cmd += [f"-mindepth {depth}", f"-maxdepth {depth}"]
    else:
        if mindepth is not None:
            cmd.append(f"-mindepth {mindepth}")
        if maxdepth is not None:
            cmd.append(f"-maxdepth {maxdepth}")

    if file_type in ("f", "d"):
        cmd.append(f"-type {file_type}")
    if name:
        cmd.append(f"-name '{name}'")
    if size:
        cmd.append(f"-size {size}")
    if mtime:
        cmd.append(f"-mtime {mtime}")
    if perm:
        cmd.append(f"-perm {perm}")
    if user:
        cmd.append(f"-user {user}")

    return " ".join(cmd)


def collect_globs(
    directory: str,
    cfg: Optional["ScanConfig"] = None,
    *,
    exts: Optional[Set[str]] = None,
    patterns: Optional[List[str]] = None,
    mindepth: Optional[int] = None,
    maxdepth: Optional[int] = None,
    depth: Optional[int] = None,
    file_type: Optional[str] = None,
    user_at_host: Optional[str] = None,
    add: bool = False,
    **kwargs
) -> List[str]:
    """
    Collect file or directory paths using either:
      - local recursive logic (rglob)
      - or remote shell call (find via run_cmd)
    """
    cfg = cfg or define_defaults(add=add)
    directory = str(directory)
    exts = ensure_exts(exts)
    patterns = ensure_patterns(patterns)

    # Remote path via SSH
    if user_at_host:
        find_cmd = get_find_cmd(
            directory,
            mindepth=mindepth,
            maxdepth=maxdepth,
            depth=depth,
            file_type=file_type,
            **{k: v for k, v in kwargs.items() if v},
        )
        return run_cmd(find_cmd, user_at_host=user_at_host)

    # Local path (Python-native walk)
    root = Path(directory)
    results = []
    for p in root.rglob("*"):
        if file_type == "f" and not p.is_file():
            continue
        if file_type == "d" and not p.is_dir():
            continue
        if exts and p.suffix.lower() not in exts:
            continue
        if patterns and not any(p.match(pat) for pat in patterns):
            continue
        results.append(str(p.resolve()))

    return sorted(results)
