"""
path_utils.py

This module provides a collection of utility functions related to file and directory path management. 
Its features include, but are not limited to:

Usage:
    import abstract_utilities.path_utils as path_utils

- Determining appropriate file path separators based on the operating system.
- Joining paths using the correct file path separator.
- Fetching the current working directory and user's home folder.
- Checking if a path corresponds to a file or directory and if they exist.
- Fetching file sizes and determining the size of directories.
- Creating multiple nested directories if they do not exist.
- Retrieving creation time of files.
- Converting sizes to GB with options for truncation.

This module is part of the `abstract_utilities` package.

Author: putkoff
Date: 05/31/2023
Version: 0.1.2
"""
import os,shlex
from .ssh_utils import run_cmd
from .string_clean import eatAll
from .list_utils import make_list
from .type_utils import get_media_exts, is_media_type,MIME_TYPES
from .safe_utils import safe_join
from .class_utils import get_caller_path,get_caller_dir
from .abstract_classes import SingletonMeta,run_pruned_func
from .string_utils import get_from_kwargs
def get_os_info():
    """
    Get Operating System Information

    This function retrieves information about the current operating system, including its name and bit size.

    Returns:
    - os_info (dict): A dictionary containing the operating system information.
                      Keys:
                      - "operating_system" (str): The name of the operating system (e.g., "Windows", "Linux", "Darwin").
                      - "bit_size" (str): The bit size of the operating system (e.g., "32bit", "64bit").

    Example:
    os_info = get_os_info()
    print("Operating System:", os_info["operating_system"])
    print("Bit Size:", os_info["bit_size"])
    """
    os_name = platform.system()
    bit_size = platform.architecture()[0]
    return {"operating_system": os_name, "bit_size": bit_size}
def get_dirs(path):
    """
    Get List of Immediate Subdirectories in a Path

    This function uses the os.walk method to traverse through a directory tree and returns a list of immediate subdirectories
    within the specified path.

    Parameters:
    - path (str): The path for which subdirectories need to be retrieved.

    Returns:
    - subdirectories (list): A list of immediate subdirectories within the specified path.

    Example:
    subdirs = get_dirs("/path/to/directory")
    print("Immediate Subdirectories:", subdirs)
    """
    from os import walk
    for (dirpath, dirnames, filenames) in walk(path):
        return dirnames
def sanitize_filename(name: str):
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
    name (str): Filename to sanitize.
    
    Returns:
    str: Sanitized filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "", name)
def get_directory(file_path: str) -> str:
    """
    Extracts and returns the directory path from a given file path.

    Args:
        file_path (str): A string representing the file path.

    Returns:
        str: The directory path extracted from the file path.
    """
    return file_path[:-len(get_base_name(file_path))]

def get_base_name(file_path: str) -> str:
    """
    Extracts and returns the base name of a file from a given file path.

    Args:
        file_path (str): A string representing the file path.

    Returns:
        str: The base name of the file.
    """
    return os.path.basename(file_path)
def split_text(string: str) -> tuple:
    """
    Splits a string into its base name and extension and returns them as a tuple.

    Args:
        string (str): A string to be split, typically representing a file name.

    Returns:
        tuple: A tuple containing the base name and extension of the input string.
    """
    return os.path.splitext(string)
def get_ext(file_path: str) -> str:
    """
    Retrieves and returns the extension of a file from a given file path.

    Args:
        file_path (str): A string representing the file path.

    Returns:
        str: The extension of the file (including the dot).
    """
    return split_text(get_base_name(file_path))[1]
def get_file_name(file_path: str) -> str:
    """
    Retrieves and returns the base name of a file from a given file path.

    Args:
        file_path (str): A string representing the file path.

    Returns:
        str: The base name of the file (without extension).
    """
    return split_text(get_base_name(file_path))[0]
def get_slash():
    """
    Returns the appropriate file path separator depending on the current operating system.
    """
    slash = '/'  # Assume a Unix-like system by default
    if slash not in get_current_path():
        slash = '\\'  # Use backslash for Windows systems
    return slash

def simple_path_join(path_A:str, path_B:str):
    """
    Join two paths using the appropriate file path separator.

    Args:
        path_A (str): The first path to join.
        path_B (str): The second path to join.
    
    Returns:
        str: The joined path.
    """
    return os.path.join(str(path_A), str(path_B))

def path_join(path_A, path_B=None):
    """
    Joins two paths or a list of paths using the appropriate file path separator.

    Args:
        path_A (str or list): The first path or list of paths to join.
        path_B (str, optional): The second path to join. Defaults to None.
    
    Returns:
        str: The joined path.
    """
    if path_B is not None:  # If path_B is provided, join path_A and path_B
        return simple_path_join(path_A, path_B)
    if isinstance(path_A, list):  # If path_A is a list, join all paths in the list
        path = path_A[0]
        for k in range(1, len(path_A)):
            path = simple_path_join(path, path_A[k])
        return path

def if_not_last_child_join(path:str,child:str):
    """
    Adds a child path to the given path if it's not already present at the end.

    Args:
        path (str): The parent path.
        child (str): The child path to add.
    
    Returns:
        str: The updated path.
    """
    if path.endswith(child):
        return path
    return simple_path_join(path, child)

def get_current_path():
    """
    Returns the current working directory.
    
    Returns:
        str: The current working directory.
    """
    return os.getcwd()

def get_home_folder():
    """
    Returns the path to the home directory of the current user.
    
    Returns:
        str: The path to the home directory.
    """
    return os.path.expanduser("~")

def is_file(path: str) -> bool:
    """Checks if the provided path is a file.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is a file, False otherwise.
    """
    return os.path.isfile(path)

def update_global_variable(name: str, value) -> None:
    """Updates the global variable with the provided name and value.

    Args:
        name (str): The name of the global variable.
        value: The value to assign to the global variable.

    Returns:
        None
    """
    globals()[name] = value

def list_directory_contents(path: str) -> list:
    """Returns a list of directory contents or a list with a single file, if the path is a file.

    Args:
        path (str): The path of the directory or file.

    Returns:
        list: A list of directory contents or a list with a single file path.
    """
    if is_file(path):
        return [path]
    elif is_valid_path(path):
        return os.listdir(path)
    return [path]

def trunc(a: float, x: int) -> float:
    """
    Truncates a float number to a specific number of decimal places.

    Args:
        a (float): The number to truncate.
        x (int): The number of decimal places to retain.

    Returns:
        float: The truncated float number.
    """
    temp = str(a)
    for i in range(len(temp)):
        if temp[i] == '.':
            try:
                return float(temp[:i+x+1])
            except:
                return float(temp)
    return float(temp)

def mkGb(k) -> float:
    """
    Converts a value to Gigabytes (GB).

    Args:
        k (float): The value to convert to GB.

    Returns:
        float: The value converted to GB.
    """
    return float(float(k)*(10**9))

def mkGbTrunk(k) -> float:
    """
    Converts a value to Gigabytes (GB) and truncates the result to five decimal places.

    Args:
        k (float): The value to convert to GB.

    Returns:
        float: The value converted to GB and truncated to five decimal places.
    """
    return trunc(mkGb(k), 5)

def mkGbTrunFroPathTot(k) -> float:
    """
    Fetches the file size from a path, converts it to Gigabytes (GB) and truncates the result to five decimal places.

    Args:
        k (str): The file path.

    Returns:
        float: The file size converted to GB and truncated to five decimal places.
    """
    return trunc(mkGb(s.path.getsize(k)), 5)


def get_abs_name_of_this():
    """
    Returns the absolute name of the current module.

    Returns:
        Path: The absolute name of the current module.
    """
    return os.path.abspath(__name__)

def createFolds(ls: list) -> None:
    """
    Creates multiple directories.

    Args:
        ls (list): The list of directory paths to create.
    """
    for k in range(len(ls)):
        mkdirs(ls[k])
def makeAllDirs(path: str) -> str:
    def make_list(obj):
        if not isinstance(obj,list):
            obj = [obj]
        return obj
    
    slash = get_slash()
    path_parts = path.split(slash)
    path=''
    if path_parts:
        last_part = path_parts[-1]
        for i,part in enumerate(path_parts):
            if part == '':
                part = slash
            path = os.path.join(path,part)
            if not os.path.exists(path):
                if '.' in part and abs(len(path_parts)-1) == i:
                    return path
                os.makedirs(path)
            else:
                if os.path.isfile(path):
                    return path
    return path
            
        
def mkdirs(path: str) -> str:
    """
    Creates a directory and any necessary intermediate directories.

    Args:
        path (str): The directory path to create.

    Returns:
        str: The created directory path.
    """
    os.makedirs(path, exist_ok=True)
    return path
def make_dirs(*paths):
    path = path_join(*paths)
    if not os.path.isfile(path):
        mkdirs(path)
    return path
def file_exists(file_path: str) -> bool:
    """
    Checks if a file exists at the specified path.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    return os.path.exists(file_path)

def dir_exists(path: str) -> bool:
    """
    Checks if a directory exists at the specified path.

    Args:
        path (str): The path to the directory.

    Returns:
        bool: True if the directory exists, False otherwise.
    """
    return os.path.isdir(path)
def file_size(path:str):
    if is_file(path):
        return os.path.getsize(path)
    return 0
def get_file_create_time(path):
    return os.path.getctime(path)
def get_size(path: str) -> int:
    """
    Calculates the size of a file or a directory.

    Args:
        path (str): The path of the file or directory.

    Returns:
        int: The size of the file or directory in bytes.
    """
    total_size = file_size(path)
    if dir_exists(path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for file in filenames:
                total_size += file_size(simple_path_join(dirpath, file))
    return total_size

def get_total_size(folder_path: str) -> int:
    """
    Calculates the total size of a directory and its subdirectories.

    Args:
        folder_path (str): The path of the directory.

    Returns:
        int: The total size of the directory and its subdirectories in bytes.
    """
    total_size = 0
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            total_size += get_size(item_path)
    return total_size

def get_files(directory):
    file_list = []
    for root,dirs,files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root,file))
    return file_list

def get_folders(directory):
    directory_list = []
    for root,dirs,files in os.walk(directory):
        for folder in dirs:
            directory_list.append(os.path.join(root,folder))
    return directory_list

def break_down_find_existing(path):
    slash = get_slash()
    test_path=''
    found_path=None
    for part in path.split(slash):
        test_path=os.path.join(test_path,part)
        if not os.path.exists(test_path):
            return found_path
        found_path = test_path
    return found_path

def get_directory_items(directory):
    if not os.path.isdir(directory):
        return []
    return os.listdir(directory)

def get_directory_files(directory):
    if not os.path.isdir(directory):
        return []
    return get_files(directory)

def get_all_item_paths(directory):
    directory_items = get_directory_items(directory)
    item_paths = [os.path.join(directory,item) for item in directory_items if item]
    return item_paths

def get_all_file_paths(directory):
    item_paths = get_directory_files(directory) 
    return item_paths

def get_directory(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory,exist_ok=True)
    return directory

def create_directory(directory,path):
    directory = os.path.join(directory,path)
    return get_directory(directory)


def initialize_file(directory,basename):
    directory = get_directory(directory)
    file_path = create_directory(directory,basename)
    return get_file_path(file_path)

def join_path(directory,basename):
    file_path = os.path.join(directory,basename)
    return file_path

def is_last_itter(i,*itters):
    itter_len = len(itters)
    if i+1 == itter_len:
        return True
    return False

def path_join(*paths, isfile=False):
    final_path = os.path.join(*paths)
    paths_len = len(paths)
    for i, path in enumerate(paths):
        if i == 0:
            final_path = path  # Note: Fixed bug; original code had `final_path = paths`
        else:
            final_path = os.path.join(final_path, path)
        if isfile and is_last_itter(i, paths_len):  # Note: `is_last_itter` is undefined; assuming it checks if last iteration
            break
        os.makedirs(final_path, exist_ok=True)      
    return final_path

def is_file(*paths):
    item_path = os.path.join(*paths)
    return os.path.isfile(item_path)

def is_dir(*paths):
    item_path = os.path.join(*paths)
    return os.path.isdir(item_path)

def is_path(*paths):
    item_path = os.path.join(*paths)
    return item_path if os.path.exists(item_path) else None

def get_all_directories(directory):
    dir_list = os.listdir(directory)
    directory_list = [item for item in dir_list if is_dir(directory,item)]
    return directory_list

def get_all_files(directory=None):
    directory = directory or os.getcwd()
    dir_list = os.listdir(directory)
    file_list = [item for item in dir_list if is_file(directory,item)]
    return file_list

def get_all_items(directory):
    dir_list = os.listdir(directory)
    file_list = [item for item in dir_list if is_path(directory,item)]
    return file_list


def get_dirlist(directory):
    path = get_directory(directory)
    if not path:
        return path
    dir_list=[]
    if is_dir(path):
        dir_list = os.listdir(path)
    elif is_file(path):
        dir_list = [os.path.basename(path)]
    return dir_list


def is_directory_in_paths(path,directory):
    return directory in path 

def remove_directory(directory,paths=None):
    paths = make_list_it(paths)
    shutil.rmtree(audio_dir)
    for path in paths:
        remove_path(path=path)
def remove_path(path=None):
    if path and os.path.exists(path):
        if os.path.isdir(path):
            remove_directory(path)
        else:
            os.remove(path)
def get_safe_dirname(path=None):
    if path:
        path_str = str(path)
        return os.path.dirname(path_str)
def get_safe_basename(path=None):
    if path:
        path_str = str(path)
        return os.path.basename(path_str)
def get_safe_splitext(path=None,basename=None):
    basename = basename or get_safe_basename(path=path)
    if basename:
        basename_str = str(basename)
        filename,ext = os.path.splitext(basename_str)
        return filename,ext
def get_safe_filename(path=None,basename=None):
    filename,_ = get_safe_splitext(path=path,basename=basename)
    return filename
def get_safe_ext(path=None,basename=None):
    _,ext = get_safe_splitext(path=path,basename=basename)
    return ext
def raw_create_dirs(*paths):
    """Recursively create all directories along the given path."""
    full_path = os.path.abspath(safe_join(*paths))
    sub_parts = [p for p in full_path.split(os.sep) if p]

    current_path = "/" if full_path.startswith(os.sep) else ""
    for part in sub_parts:
        current_path = safe_join(current_path, part)
        os.makedirs(current_path, exist_ok=True)
    return full_path


def create_dirs(directory, child=None):
    """Create directory and optional child path safely."""
    full_path = os.path.abspath(safe_join(directory, child))
    if not os.path.exists(full_path):
        raw_create_dirs(full_path)
    return full_path


def get_base_dir(directory=None):
    """Return given directory or _BASE_DIR fallback."""
    return directory or _BASE_DIR


def create_base_path(directory=None, child=None):
    """Join base dir with child."""
    directory = get_base_dir(directory)
    return safe_join(directory, child)


def create_base_dir(directory=None, child=None):
    """Ensure existence of base directory path."""
    full_path = create_base_path(directory, child)
    if not os.path.exists(full_path):
        raw_create_dirs(full_path)
    return full_path


def get_user_pass_host_key(**kwargs):
    args = ['password','user_at_host','host','key','user']
    kwargs['del_kwarg']=kwargs.get('del_kwarg',False)
    values,kwargs = get_from_kwargs(*args,**kwargs)
    return values

# --- Base remote checker -----------------------------------------------------
def _remote_test(path: str, test_flag: str, timeout: int = 5,*args, **kwargs) -> bool:
    """
    Run a remote shell test (e.g. -f, -d) via SSH.
    Returns True if test succeeds, False otherwise.
    """
    try:
        kwargs['cmd']=f"[ {test_flag} {shlex.quote(path)} ] && echo 1 || echo 0"
        kwargs['text']=True
        kwargs['timeout']=timeout
        kwargs['stderr']=subprocess.DEVNULL
        result = run_pruned_func(run_cmd,**kwargs)
        return result.strip() == "1"
    except Exception:
        return False


# --- Individual path checks --------------------------------------------------
def is_remote_file(path: str,*args, **kwargs) -> bool:
    """True if remote path is a file."""
    return _remote_test(path, "-f", **kwargs)


def is_remote_dir(path: str,*args, **kwargs) -> bool:
    """True if remote path is a directory."""
    return _remote_test(path, "-d", **kwargs)


def is_local_file(path: str) -> bool:
    """True if local path is a file."""
    return os.path.isfile(path)


def is_local_dir(path: str) -> bool:
    """True if local path is a directory."""
    return os.path.isdir(path)


# --- Unified interface -------------------------------------------------------

def is_file(path: str,*args,**kwargs) -> bool:
    """Determine if path is a file (works local or remote)."""
    if get_user_pass_host_key(**kwargs):
        return is_remote_file(path, **kwargs)
    return is_local_file(path)


def is_dir(path: str, *args,**kwargs) -> bool:
    """Determine if path is a directory (works local or remote)."""
    if get_user_pass_host_key(**kwargs):
        return is_remote_dir(path, **kwargs)
    return is_local_dir(path)

def is_exists(path: str, *args,**kwargs) -> bool:
    if is_file(path,**kwargs):
        return True
    if is_dir(path,**kwargs):
        return True
    return False
# --- Optional: keep your original all-in-one wrapper ------------------------
def check_path_type(
    path: str,
    *args,
    **kwargs
) -> str:
    """
    Return 'file', 'directory', 'missing', or 'unknown'.
    Uses isolated is_file/is_dir functions.
    """
    if get_user_pass_host_key(**kwargs):
        if is_remote_file(path,**kwargs):
            return "file"
        elif is_remote_dir(path,**kwargs):
            return "directory"
        else:
            return "missing"
    else:
        if os.path.isfile(path):
            return "file"
        elif os.path.isdir(path):
            return "directory"
        elif not os.path.exists(path):
            return "missing"
        return "unknown"

def get_file_parts(path):
    
    basename = get_safe_basename(path)
    filename, ext = get_safe_splitext(basename=basename)

    dirname = get_safe_dirname(path)
    dirbase = get_safe_basename(dirname)
    
    parent_dirname = get_safe_dirname(dirname)
    parent_dirbase = get_safe_basename(parent_dirname)
    
    super_dirname = get_safe_dirname(parent_dirname)
    super_dirbase = get_safe_basename(super_dirname)

    return {"dirname": dirname,
            "basename": basename,
            "filename": filename,
            "ext": ext,
            "dirbase":dirbase,
            "parent_dirname":parent_dirname,
            "parent_dirbase":parent_dirbase,
            "super_dirname":super_dirname,
            "super_dirbase":super_dirbase
            }
