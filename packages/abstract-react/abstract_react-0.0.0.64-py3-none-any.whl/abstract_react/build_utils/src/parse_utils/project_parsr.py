from abstract_utilities import *

_BASE_DIR = get_caller_dir()

def safe_split(string, char, i=None, default=False):
    """Safely split a string by a character and optionally return index i."""
    if string is None or char is None:
        return string

    string_str, char_str = str(string), str(char)
    if char_str not in string_str:
        return string

    parts = string_str.split(char_str)

    if i is None:
        return parts

    if is_number(i):
        i = int(i)
        if i < len(parts):
            return parts[i]
        if default:
            return string if default is True else default
        return
    return string if default is True else default


def safe_slice(obj, i=None, k=None, default=False):
    """Safely slice an object like a list or string with defaults."""
    if obj is None or isinstance(obj, bool):
        return obj if default is True else default if default else None

    obj_len = len(obj)

    # If no indices provided, return as is (or default)
    if i is None and k is None:
        return obj if default is True else default if default else None

    # Normalize negative indices
    if isinstance(i, int) and i < 0:
        i = obj_len + i
    if isinstance(k, int) and k < 0:
        k = obj_len + k

    # Bound indices
    if i is not None:
        i = max(0, min(i, obj_len))
    if k is not None:
        k = max(0, min(k, obj_len))

    try:
        return obj[i:k]
    except Exception:
        return obj if default is True else default if default else None
def safe_join(*paths):
    paths = list(paths)
    paths = [path for path in paths if path]
    return os.path.join(*paths)
def get_inside(text,char):
    parts = text.split(char)

    part = safe_slice(parts,1,-1) or []
    return char.join(part)
def get_insides(text,char):
    parts = safe_split(text,char)
    returns = []
    for i,part in enumerate(parts):
        if i !=0 and i%2 != float(0):
            returns.append(part)
    return returns

def get_content_lines(contents=None,filepath=None):
    if not contents and filepath and os.path.isfile(filepath):
        contents = read_from_file(filepath)
    if contents:
        line_spl=None
        if isinstance(contents,str): 
            line_spl = contents.split('\n')
        if isinstance(contents,list):
            line_spl = contents
        return line_spl
def get_index_content(contents=None,filepath=None):
    line_spl = get_content_lines(contents=contents,filepath=filepath)
    export_ls=[]
    exp_all = False
    filename='.'
    if filepath:
        dirname = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        filename,ext = os.path.splitext(basename)
    for line in line_spl:
        if line.startswith('export'):
            item = eatAll(line.split('(')[0].split('=')[0].split('function')[-1].split('const')[-1].split(' ')[-1],[' ','','\n','\t',';'])
            if 'default ' in line:
                export_ls.append("export {"+f"default as {item}"+"}"+f" from './{filename}';")
            elif exp_all == False:
                exp_all = True
                export_ls.append(f"export * from './{filename}';")
    index_cont = '\n'.join(export_ls)
    return index_cont
def create_script_dir(contents=None,file_path=None,script_dir=None):
    line_spl = get_content_lines(contents=contents,file_path=file_path)
    content_lines = line_spl[1:]
    contents = '\n'.join(content_lines)
    index_cont = get_index_content(contents=content_lines)
    if script_dir:
        dirname = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        filename,ext = os.path.splitext(basename)
        if script_dir == True:
            script_dir = os.path.join(dirname,filename)
        if not os.path.isdir(script_dir):
            create_dirs(script_dir)
        os.path.join(script_dir,basename)
    index_path = os.path.join(dirbase,'index.ts')
    base_path = os.path.join(dirbase,basename)
    write_to_file(contents=contents,file_path=base_path)
    write_to_file(contents=index_cont,file_path=index_path)

def raw_create_dirs(*paths):
    full_path = safe_join(*paths)
    partial_paths = full_path.split('/')
    paths = [path for path in partial_paths if path]
    for i,path in enumerate(paths):
        if i == 0:
            full_path = path
        else:
            full_path = safe_join(full_path,path)
        os.makedirs(full_path,exist_ok=True)
    return full_path
def create_dirs(directory,child=None):
    full_path = safe_join(directory,child)
    if not os.path.exists(full_path):
        full_path = raw_create_dirs(full_path)
    return full_path
def get_base_dir(directory = None):
    return directory or _BASE_DIR
def create_base_path(directory=None,child=None):
    directory = get_base_dir(directory = directory)
    return safe_join(directory,child)
def create_base_dir(directory=None,child=None):
    full_path = create_base_path(directory=directory,child=child)
    if not os.path.exists(full_path):
        base_path = create_dirs(full_path)
    return base_path

