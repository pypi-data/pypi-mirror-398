# safe_import_utils.py
from ..imports import *
from .import_functions import *

def ensure_import_pkg_js(import_pkg_js,file_path=None):
    import_pkg_js = import_pkg_js or {"context":{}}
    if "context" not in import_pkg_js:
        import_pkg_js["context"]={}
    for key in ["nulines","file_path","all_data"]:
        if key not in import_pkg_js["context"]:
            import_pkg_js["context"][key]=[]
    if file_path and file_path != import_pkg_js["context"]["file_path"]:
        found=False
        nu_data = {"file_path":import_pkg_js["context"]["file_path"],"nulines":import_pkg_js["context"]["nulines"]}
        for i,data in enumerate(import_pkg_js["context"]["all_data"]):
            if data.get('file_path') == import_pkg_js["context"]["file_path"]:
                import_pkg_js["context"]["all_data"][i] = nu_data
                found = True
                break
        if found == False:
            import_pkg_js["context"]["all_data"].append(nu_data)
        import_pkg_js["context"]["nulines"]=[]
        import_pkg_js["context"]["file_path"]=file_path
    return import_pkg_js
def ensure_package_context(file: str):
    """
    Ensure that running this file directly still gives it the correct package.
    Sets sys.path and __package__ based on the __init__.py chain.
    """
    file = file or os.getcwd()
    here = Path(file).resolve()
    top_pkg_dir = find_top_pkg_dir(here)
    if not top_pkg_dir:
        raise RuntimeError(f"No package context above {here}. Add __init__.py files up the tree.")

    sysroot = top_pkg_dir.parent  # dir ABOVE the top package (e.g., .../src)
    if str(sysroot) not in sys.path:
        sys.path.insert(0, str(sysroot))

    # Compute this module's package (exclude the filename)
    parts = here.with_suffix("").relative_to(sysroot).parts
    pkg_name = ".".join(parts[:-1])  # e.g. abstract_ide.consoles.launcherWindowTab

    # When run as a script, __package__ is empty -> set it
    if (__name__ == "__main__") and (not globals().get("__package__")):
        globals()["__package__"] = pkg_name
# --- tiny utils ---
def find_top_package_dir(p: Path) -> Path | None:
    p = p.resolve()
    if p.is_file():
        p = p.parent
    top = None
    while (p / "__init__.py").exists():
        top = p
        if p.parent == p:
            break
        p = p.parent
    return top

def derive_package_for_file(file: str) -> tuple[str, Path]:
    """Return (pkg_name, sysroot) for the module file."""
    here = Path(file).resolve()
    top_pkg_dir = find_top_pkg_dir(here)
    if not top_pkg_dir:
        raise RuntimeError(f"No package context above {here}. Add __init__.py up the tree.")
    sysroot = top_pkg_dir.parent
    if str(sysroot) not in sys.path:
        sys.path.insert(0, str(sysroot))
    parts = here.with_suffix("").relative_to(sysroot).parts
    pkg_name = ".".join(parts[:-1])  # package of the module (drop the filename)
    return pkg_name, sysroot

def ensure_caller_package(caller_file: str, caller_globals: dict | None = None) -> str:
    """
    Ensure sysroot is on sys.path and return the caller's dotted package.
    Optionally set caller_globals['__package__'] when running as a script.
    """
    pkg, _ = derive_package_for_file(caller_file)
    if caller_globals and caller_globals.get("__name__") == "__main__" and not caller_globals.get("__package__"):
        caller_globals["__package__"] = pkg
    return pkg
def get_import_pkg(line):
    if is_line_group_import(line):
        return clean_line(line.split(FROM_TAG)[1].split(IMPORT_TAG)[0])
def get_imports_from_import_pkg(line):
    if is_line_group_import(line):
        return get_cleaned_import_list(line,commaClean=True)
def add_imports_to_import_pkg_js(import_pkg,imports,import_pkg_js=None):
    import_pkg_js = ensure_import_pkg_js(import_pkg_js)
    imports = clean_imports(imports)
    if import_pkg not in import_pkg_js:
        i = len(import_pkg_js["context"]["nulines"])
        import_pkg_js[import_pkg]={"imports":imports,"line":i}
        import_line = f"from {import_pkg} import "
        if import_pkg == "import":
            import_line = IMPORT_TAG
        import_pkg_js["context"]["nulines"].append(import_line)
    else:
        import_pkg_js[import_pkg]["imports"]+=imports
    return import_pkg_js
def update_import_pkg_js(line,import_pkg_js=None):
    import_pkg_js = ensure_import_pkg_js(import_pkg_js)
    if is_line_group_import(line):
        import_pkg = get_import_pkg(line)
        imports = get_imports_from_import_pkg(line)
        import_pkg_js = add_imports_to_import_pkg_js(import_pkg,imports,import_pkg_js=import_pkg_js)
    else:
        if len(import_pkg_js["context"]["nulines"]) >0 and line == '' and is_line_import(import_pkg_js["context"]["nulines"][-1]):
            pass
        else:
            import_pkg_js["context"]["nulines"].append(line)
    return import_pkg_js
# --- public API ---
def safe_import(
    name: str,
    *,
    member: str | None = None,
    package: str | None = None,
    file: str | None = None,
    caller_globals: dict | None = None,
):
    """
    Import `name` (relative or absolute).
    - If `name` is relative and `package` is missing, derive it from `file` (or caller).
    - If running the caller as a script, we can set its __package__ when caller_globals is provided.
    """
    if file is None:
        # best-effort: use the immediate caller's file
        frame = inspect.currentframe()
        assert frame is not None
        outer = frame.f_back
        caller_file = (outer.f_globals.get("__file__") if outer else None) or __file__
    else:
        caller_file = file

    if name.startswith(".") and not package:
        package = ensure_caller_package(caller_file, caller_globals=caller_globals)

    mod = importlib.import_module(name, package=package)
    return getattr(mod, member) if member else mod
