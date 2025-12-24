from .list_utils import make_list
def get_from_kwargs(*args,**kwargs):
    del_kwarg = kwargs.get('del_kwargs',False)
    values = {}
    for key in args:
        if key:
            key = str(key)
            if key in kwargs:
                values[key] = kwargs.get(key)
                if del_kwarg:
                    del kwargs[key]
    return values,kwargs

def replace_it(string,item,rep):
    if item in string:
        string = string.replace(item,rep)
    return string
def while_replace(string,item,rep):
    while True:
        string = replace_it(string,item,rep)
        if item not in string or item in rep:
            return string
def for_replace(string,item,replace):
    replace = make_list(replace)
    for rep in replace:
        string = while_replace(string,item,rep)
    return string
def replace_all(string,*args,**kwargs):
    for items in args:
        if items and isinstance(items,list):
            item = items[0]
            replace = items[1:] if len(items)>1 else items[-1]
            string = for_replace(string,item,replace)
    values,kwargs = get_from_kwargs('item','replace',**kwargs)
    if values:
        string = for_replace(string,**values)
    for item,replace in kwargs.items():
        string = for_replace(string,item,rep)
    return string
def get_lines(string,strip=True):
    lines = string.split('\n')
    if strip:
        lines = [line for line in lines if line]
    return lines
def get_alpha():
    return 'abcdefghijklmnopqrstuvwxyz'
def is_alpha(char,case_sensative=False):
    alphas = get_alpha()
    if not case_sensative:
        alphas+=alphas.upper()
    return char in alphas
