# attach_functions.py  — single helper you can import anywhere
# attach_dynamic.py
from __future__ import annotations
from .imports import *
def call_for_all_tabs(root = None,tab_control=True):
    root = root or get_caller_dir()
    get_for_all_tabs(root,tab_control=tab_control)

def get_clean_list(*args):
    objs = []
    for arg in args:
        objs+= make_list(arg)
    return list(set(objs))
def clean_imports(*args,**kwargs):
    for pkg,imps in kwargs.items():
        f"from {pkg} import make_list(imps)"
        
    alls = str(list(set("""os,re,subprocess,sys,re,traceback,pydot, enum, inspect, sys, traceback, threading,json,traceback,logging,requests""".replace('\n','').replace(' ','').replace('\t','').split(','))))[1:-1].replace('"','').replace("'",'')
    return 
def isTab(item):
    item_lower =  item.lower()
    for key in ['console','tab']:
        if item_lower.endswith(key):
            return True
def get_dir(root,item):
    if None in [root]:
        return None
    path = root
    if item != None:
        path = os.path.join(path,item)
    return path
def isDir(root,item=None):
    path = get_dir(root,item)
    if path:
        return os.path.isdir(path)
def check_dir_item(root,item=None):
    return item and isTab(item) and isDir(root,item)
def get_dirs(root = None):
    root = root or ABSROOT
    dirpaths = [get_dir(root,item) for item in os.listdir(root) if check_dir_item(root,item)]
    return dirpaths
def ifFunctionsInFile(root):
    items = [os.path.join(root, "functions"),os.path.join(root, "functions.py")]
    for item in items:
        if os.path.exists(item):
            return item
        

def get_for_all_tabs(root = None,tab_control=True):
    root = root or caller_path()
    if os.path.isfile(root):
        root = os.path.dirname(root)
    if tab_control:
        all_tabs = get_dirs(root = root)
    else:
        dirname = root
        if root and os.path.isfile(root):
            dirname = os.path.dirname(root)
        all_tabs = [dirname]
    for ROOT in all_tabs:
        FUNCS_DIR = ifFunctionsInFile(ROOT)
        if FUNCS_DIR == None:
            for ROOT in get_dirs(root = ROOT):
                apply_inits(ROOT)
        else: 
            apply_inits(ROOT)
            

def write_init_functions(import_lines,functions_dir):
    functions_init = "\n".join(import_lines) + ("\n" if import_lines else "")
    init_file_path = os.path.join(functions_dir, "__init__.py")
    write_to_file(contents=functions_init, file_path=init_file_path)
    return {"functions_init":functions_init,"init_file_path":init_file_path}
def extract_funcs(filepaths):
    funcs = []
    for line in read_from_file(path).splitlines():
        m = re.match(r"^def\s+([A-Za-z_]\w*)\s*\(self", line)
        if m:
            funcs.append(m.group(1))
    return funcs
def get_all_funcs(
    filepaths,
    all_funcs=None,
    import_lines=None
    ):
    import_lines = import_lines or []
    all_funcs = all_funcs or []
    for fp in filepaths:
        basename = os.path.basename(fp)
        module = os.path.splitext(basename)[0]
        funcs = extract_funcs(fp)
        if funcs:
            import_lines.append(f"from .{module} import ({', '.join(funcs)})")
            all_funcs.extend(funcs)
    uniq_funcs = sorted(set(all_funcs))
    func_tuple=", ".join(uniq_funcs) + ("," if len(uniq_funcs) == 1 else "")
    all_funcs_js = {"import_lines":import_lines,"all_funcs":all_funcs,"uniq_funcs":uniq_funcs,"func_tuple":func_tuple}
    return all_funcs_js
def get_init_funcs_str(func_tuple):
        init_funcs_str = textwrap.dedent(f"""\
            

            from .functions import ({func_tuple})

            def initFuncs(self):
                try:
                    for f in ({func_tuple}):
                        setattr(self, f.__name__, f)
                except Exception as e:
                    logger.info(f"{{e}}")
                return self
        """)
        return init_funcs_str
def get_function_file_paths(functions_dir):
    filepaths=[]
    if_fun_dir = isDir(functions_dir)
    if if_fun_dir != None:
        input(if_fun_dir)
        if if_fun_dir:
            CFG = define_defaults(allowed_exts='.py',
                unallowed_exts = True,
                exclude_types = True,
                exclude_dirs = True,
                exclude_patterns = True)
            input(CFG)
            _,filepaths = get_files_and_dirs(functions_dir,cfg=CFG)
        else:
            filepaths = [FUNCS_DIR]
    input(filepaths)
    return filepaths
def apply_inits(root=None,tab_control=True):
    root = root or get_caller_dir()
    FUNCS_DIR = ifFunctionsInFile(root)
    if_fun_dir = isDir(FUNCS_DIR)
    if if_fun_dir != None:  
        file_paths = get_function_file_paths(FUNCS_DIR)
 
        all_funcs_js = get_all_funcs(
            filepaths=file_paths
            )
        if if_fun_dir:
            init_func_js = write_init_functions(import_lines=all_funcs_js.get('import_lines'),functions_dir=FUNCS_DIR)
            all_funcs_js.update(init_func_js)
        func_tuple = all_funcs_js.get("func_tuple")
        init_funcs_str = get_init_funcs_str(func_tuple)
        init_funcs_file_path = os.path.join(root, "initFuncs.py")
        all_funcs_js["funcs_str"]=init_funcs_str
        all_funcs_js["funcs_file_path"]=init_funcs_file_path
        write_to_file(contents=init_funcs_str, file_path=init_funcs_file_path)
        return all_funcs_js

