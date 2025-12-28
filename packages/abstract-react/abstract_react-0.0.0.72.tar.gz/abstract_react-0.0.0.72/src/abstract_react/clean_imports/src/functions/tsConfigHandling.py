from ..imports import *
# === TSCONFIG HANDLING ===
def get_spec_file_path(filename, directory=None):
    file_paths = find_files(filename, directory=directory)
    return get_single_from_list(file_paths)

def get_ts_config_path(directory=None):
    return get_spec_file_path('tsconfig', directory=directory)

def get_ts_config_data(directory=None):
    ts_config_path = get_ts_config_path(directory=directory)
    if ts_config_path:
        return safe_load_from_file(ts_config_path)

def get_ts_config_root_dir(directory=None):
    ts_config_path = get_ts_config_path(directory=directory)
    if ts_config_path:
        return os.path.dirname(ts_config_path)

def get_ts_config_compilerOptions(data=None, directory=None):
    if not data:
        data = get_ts_config_data(directory=directory)
    data = data or {}
    return data.get('compilerOptions') or {}

def get_ts_config_paths(data=None, directory=None):
    data = get_ts_config_compilerOptions(data=data, directory=directory) or {}
    return data.get('paths') or {}
