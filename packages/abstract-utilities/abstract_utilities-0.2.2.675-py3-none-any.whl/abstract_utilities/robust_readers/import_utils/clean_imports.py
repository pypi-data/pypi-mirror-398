from ...read_write_utils import read_from_file,write_to_file
from ...string_clean import eatAll,eatElse,clean_line
from ...class_utils import get_caller_path
from ...list_utils import make_list
import os
import_tag = 'import '
from_tag = 'from '
def get_text_or_read(text=None,file_path=None):
    text = text or ''
    imports_js = {}
    if not text and file_path and os.path.isfile(file_path):
        text=read_from_file(file_path)
    return text
def is_line_import(line):
    if line and (line.startswith(from_tag) or line.startswith(import_tag)):
        return True
    return False
def is_line_group_import(line):
    if line and (line.startswith(from_tag) and import_tag in line):
        return True
    return False
def get_import_pkg(line):
    if is_line_group_import(line):
        return clean_line(line.split(from_tag)[1].split(import_tag)[0])
def get_imports_from_import_pkg(line):
    if is_line_group_import(line):
        return get_cleaned_import_list(line,commaClean=True)

def add_imports_to_import_pkg_js(import_pkg,imports,import_pkg_js=None):
    import_pkg_js = import_pkg_js or {}
    imports = clean_imports(imports)
    if import_pkg not in import_pkg_js:
        i = len(import_pkg_js["nulines"])
        import_pkg_js[import_pkg]={"imports":imports,"line":i}
        import_line = f"from {import_pkg} import "
        if import_pkg == "import":
            import_line = import_tag
        import_pkg_js["nulines"].append(import_line)
    else:
        import_pkg_js[import_pkg]["imports"]+=imports
    return import_pkg_js
def update_import_pkg_js(line,import_pkg_js=None):
    import_pkg_js = import_pkg_js or {}
    if is_line_group_import(line):
        import_pkg = get_import_pkg(line)
        imports = get_imports_from_import_pkg(line)
        import_pkg_js = add_imports_to_import_pkg_js(import_pkg,imports,import_pkg_js=import_pkg_js)
    else:
        if len(import_pkg_js["nulines"]) >0 and line == '' and is_line_import(import_pkg_js["nulines"][-1]):
            pass
        else:
            import_pkg_js["nulines"].append(line)
    return import_pkg_js
def is_from_line_group(line):
    if line and line.startswith(from_tag) and import_tag in line and '(' in line:
        import_spl = line.split(import_tag)[-1]
        import_spl_clean = clean_line(line)
        if not import_spl_clean.endswith(')'):
            return True
    return False
def clean_imports(imports,commaClean=True):
    chars=["*"]
    if not commaClean:
        chars.append(',')
    if isinstance(imports,str):
        imports = imports.split(',')
    return [eatElse(imp,chars=chars) for imp in imports if imp]
def get_cleaned_import_list(line,commaClean=True):
    cleaned_import_list=[]
    if import_tag in line:
        imports = line.split(import_tag)[1]
        cleaned_import_list+=clean_imports(imports,commaClean=commaClean)
    return cleaned_import_list
def get_all_imports(text=None,file_path=None,import_pkg_js=None):
    text = get_text_or_read(text=text,file_path=file_path)
    lines = text.split('\n')
    cleaned_import_list=[]
    nu_lines = []
    is_from_group = False
    import_pkg_js = import_pkg_js or {}
    if "nulines" not in import_pkg_js:
        import_pkg_js["nulines"]=[]
    if "file_path" not in import_pkg_js:
        import_pkg_js["file_path"]=file_path
    if "all_data" not in import_pkg_js:
        import_pkg_js["all_data"]=[]
    if file_path and file_path != import_pkg_js["file_path"]:
        found=False
        nu_data = {"file_path":import_pkg_js["file_path"],"nulines":import_pkg_js["nulines"]}
        for i,data in enumerate(import_pkg_js["all_data"]):
            if data.get('file_path') == import_pkg_js["file_path"]:
                import_pkg_js["all_data"][i] = nu_data
                found = True
                break
        if found == False:
            import_pkg_js["all_data"].append(nu_data)
        import_pkg_js["nulines"]=[]
        import_pkg_js["file_path"]=file_path

    for line in lines:
        if line.startswith(import_tag) and ' from ' not in line:
            cleaned_import_list = get_cleaned_import_list(line)
            import_pkg_js = add_imports_to_import_pkg_js("import",cleaned_import_list,import_pkg_js=import_pkg_js)
        else:
            if is_from_group:
                import_pkg=is_from_group
                line = clean_line(line)
                if line.endswith(')'):
                   is_from_group=False
                   line=line[:-1]
                imports_from_import_pkg = clean_imports(line)
                import_pkg_js = add_imports_to_import_pkg_js(import_pkg,imports_from_import_pkg,import_pkg_js=import_pkg_js)
                
            else:
                import_pkg_js=update_import_pkg_js(line,import_pkg_js=import_pkg_js)
            if is_from_line_group(line) and is_from_group == False:
                is_from_group=get_import_pkg(line)
    return import_pkg_js
def clean_all_imports(text=None,file_path=None,import_pkg_js=None):
    if not import_pkg_js:
        import_pkg_js = get_all_imports(text=text,file_path=file_path)
    nu_lines = import_pkg_js["nulines"]
    for pkg,values in import_pkg_js.items():
        comments = []
        if pkg not in ["nulines","file_path","all_data"]: 
            line = values.get('line')
            imports = values.get('imports')
            for i,imp in enumerate(imports):
                if '#' in imp:
                    imp_spl = imp.split('#')
                    comments.append(imp_spl[-1])
                    imports[i] = clean_line(imp_spl[0])
            imports = list(set(imports))   
            if '*' in imports:
                imports="*"
            else:
                imports=','.join(imports)
                if comments:
                    comments=','.join(comments)
                    imports+=f" #{comments}"
            import_pkg_js[pkg]["imports"]=imports
            nu_lines[line] += imports
    import_pkg_js["nulines"]=nu_lines
    return import_pkg_js

def get_all_real_imps(file):
    contents = read_from_file(file)
    lines = contents.split('\n')
    for line in lines:
        if line.startswith('from '):
            from_line = line.split('from ')[-1]
            dot_fro = ""
            dirname = file
            for char in from_line:
                if  char != '.':
                    line = f"from {dot_fro}{eatAll(from_line,'.')}"
                    if line in all_imps:
                        line = ""
                    break
                if dot_fro == "":
                    dot_fro = ""
                dirname = os.path.dirname(dirname)
                dirbase = os.path.basename(dirname)
                dot_fro = f"{dirbase}.{dot_fro}"
        if line:
            all_imps.append(line)

    return '\n'.join(all_imps)
def save_cleaned_imports(text=None,file_path=None,write=False,import_pkg_js=None):
    import_pkg_js=get_all_imports(text=text,file_path=file_path,import_pkg_js=import_pkg_js)
    import_pkg_js = clean_all_imports(text=text,file_path=file_path,import_pkg_js=import_pkg_js)
    contents = '\n'.join(import_pkg_js["nulines"])
    if file_path and write:
        write_to_file(contents=contents,file_path=file_path)
    return contents
