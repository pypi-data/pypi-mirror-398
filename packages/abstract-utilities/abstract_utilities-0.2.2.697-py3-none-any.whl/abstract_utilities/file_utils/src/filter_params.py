
from ..imports import *
import re
def combine_params(*values,typ=None):
    nu_values = None
    for value in values:
        if value is not None:
            typ = typ or type(value)
            if nu_values is None:
                nu_values = typ()
            
            if typ is set:
                nu_values = nu_values | typ(value)
            if typ is list:
                nu_values += typ(value)
    return nu_values
def get_safe_kwargs(canonical_map, **kwargs):
    # Lowercase all keys for safety
    canonical_map = canonical_map or CANONICAL_MAP
    norm_kwargs = {k.lower(): v for k, v in kwargs.items() if v is not None}

    # Inverse lookup: alias → canonical key
    alias_lookup = {
        alias: canon
        for canon, aliases in canonical_map.items()
        if aliases
        for alias in aliases
    }

    # Preserve correctly named keys
    safe_kwargs = {k: v for k, v in norm_kwargs.items() if k in canonical_map}

    for k, v in norm_kwargs.items():
        if k in alias_lookup:
            canonical_key = alias_lookup[k]
            prev = safe_kwargs.get(canonical_key)
            if prev is None:
                safe_kwargs[canonical_key] = v
            else:
                # merge intelligently if both exist
                if isinstance(prev, (set, list)) and isinstance(v, (set, list)):
                    safe_kwargs[canonical_key] = list(set(prev) | set(v))
                else:
                    safe_kwargs[canonical_key] = v  # overwrite for non-iterables

    # fill defaults if missing
    for canon in canonical_map:
        safe_kwargs.setdefault(canon, None)

    return safe_kwargs

def create_canonical_map(*args,canonical_map=None):
    keys = [arg for arg in args if arg]
    if not keys:
        return CANONICAL_MAP
    canonical_map = canonical_map or CANONICAL_MAP

    return {key:canonical_map.get(key) for key in keys}
def get_safe_canonical_kwargs(*args,canonical_map=None,**kwargs):
    canonical_map = canonical_map or create_canonical_map(*args)
    
    return get_safe_kwargs(canonical_map=canonical_map,**kwargs)    
def get_dir_filter_kwargs(**kwargs):
    canonical_map = create_canonical_map("directories")
    return get_safe_kwargs(canonical_map=canonical_map,**kwargs)
def get_file_filter_kwargs(**kwargs):
    """
    Normalize arbitrary keyword arguments for file scanning configuration.
    
    Examples:
      - 'excluded_ext' or 'unallowed_exts' → 'exclude_exts'
      - 'include_dirs' or 'allow_dir' → 'allowed_dirs'
      - 'excludePattern' or 'excluded_patterns' → 'exclude_patterns'
      - 'allowed_type' or 'include_types' → 'allowed_types'
    """
    # Canonical keys and aliases
    canonical_keys =["allowed_exts","exclude_exts","allowed_types","exclude_types","allowed_dirs","exclude_dirs","allowed_patterns","exclude_patterns"]
   
    return get_safe_canonical_kwargs(*canonical_keys,**kwargs)
# -------------------------
# Utility functions
# -------------------------

def _normalize_listlike(value, typ=list, sep=','):
    """Normalize comma-separated or iterable values into the desired type."""
    if value in [True, None, False]:
        return value
    if isinstance(value, str):
        value = [v.strip() for v in value.split(sep) if v.strip()]
    return typ(value)

def ensure_exts(exts):
    if exts in [True, None, False]:
        return exts
    out = []
    for ext in _normalize_listlike(exts, list):
        if not ext.startswith('.'):
            ext = f".{ext}"
        out.append(ext)
    return set(out)

def ensure_patterns(patterns):
    """Normalize pattern list and ensure they are valid globs."""
    if patterns in [True, None, False]:
        return patterns
    patterns = _normalize_listlike(patterns, list)
    out = []
    for pattern in patterns:
        if not pattern:
            continue
        if '*' not in pattern and '?' not in pattern:
            # Implicitly make it a prefix match
            if pattern.startswith('.') or pattern.startswith('~'):
                pattern = f"*{pattern}"
            else:
                pattern = f"{pattern}*"
        out.append(pattern)
    return out


def _get_default_modular(value, default, add=False, typ=set):
    """Merge user and default values intelligently."""
    if value == None:
        value = add
    if value in [True]:
        return default
    if value is False:
        return value
    if add:
        return combine_params(value,default,typ=None)

    return typ(value)

# -------------------------
# Default derivation logic
# -------------------------
def _get_default_modular(value, default, add=None, typ=set):
    """Merge user and default values intelligently."""
    add = add or False
    if value == None:
        value = add
    if value in [True]:
        return default
    if value is False:
        return value
    if add:
        return combine_params(value,default,typ=None)
    return typ(value)
def derive_all_defaults(**kwargs):
    kwargs = get_safe_canonical_kwargs(**kwargs)
    add = kwargs.get("add",False)
    nu_defaults = {}
    for key,values in DEFAULT_CANONICAL_MAP.items():
        default = values.get("default")
        typ = values.get("type")
        key_value = kwargs.get(key)
        if key in DEFAULT_ALLOWED_EXCLUDE_MAP:

            if key.endswith('exts'):
                input_value = ensure_exts(key_value)
            if key.endswith('patterns'):
                input_value = ensure_patterns(key_value)
            else:
                input_value = _normalize_listlike(key_value, typ)
            nu_defaults[key] = _get_default_modular(input_value, default, add, typ)
        else:
            value = default if key_value is None else key_value
            if typ == list:
                value = make_list(value)
            elif typ == bool:
                value = bool(value)
            nu_defaults[key] = value
   
    return nu_defaults
# -------------------------
# Default derivation logic
# -------------------------
def derive_file_defaults(**kwargs):
    kwargs = derive_all_defaults(**kwargs)
    add = kwargs.get("add",False)
    nu_defaults = {}
    for key,values in DEFAULT_ALLOWED_EXCLUDE_MAP.items():
        default = values.get("default")
        typ = values.get("type")
        key_value = kwargs.get(key)
        if key.endswith('exts'):
            input_value = ensure_exts(key_value)
        if key.endswith('patterns'):
            input_value = ensure_patterns(key_value)
        else:
            input_value = _normalize_listlike(key_value, typ)
        nu_defaults[key] = _get_default_modular(input_value, default, add, typ)
    return nu_defaults

def define_defaults(**kwargs):
    defaults = derive_file_defaults(**kwargs)
    return ScanConfig(**defaults)
