from ..imports import *
from .tsConfigHandling import *
# === PATH ALIAS PROCESSING ===
def check_has_wildcard(path_config: str) -> bool:
    """Check if path configuration uses wildcard"""
    return path_config.endswith('/*')

def build_path_alias_registry(directory=None) -> Dict[str, PathAlias]:
    """Build registry of path aliases from tsconfig"""
    paths = get_ts_config_paths(directory=directory)
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    
    registry = {}
    for alias, path_configs in paths.items():
        if not path_configs:
            continue
        
        # Take first path config
        path_config = path_configs[0]
        
        # Check for wildcard BEFORE cleaning
        has_wildcard = check_has_wildcard(path_config) and check_has_wildcard(alias)
        
        # Remove trailing /* from both alias and path
        clean_alias = alias.rstrip('/*')
        clean_path = path_config.rstrip('/*')
        
        resolved = normalize_path(os.path.join(ts_root_dir, clean_path))
        
        registry[clean_alias] = PathAlias(
            alias=clean_alias,
            resolved_path=resolved,
            base_dir=ts_root_dir,
            has_wildcard=has_wildcard
        )
    
    return registry

# === PATH RESOLUTION ===
def get_import_path(relative_import, file_path=None, directory=None):
    """Resolve relative import to absolute path"""
    if not directory:
        if file_path:
            if os.path.isdir(file_path):
                directory = file_path
            elif os.path.isfile(file_path):
                directory = os.path.dirname(file_path)
    if not directory:
        return None
    
    parent_dir_count = count_chars(relative_import, '..')
    for _ in range(parent_dir_count):
        directory = os.path.dirname(directory)
    
    rel_path = relative_import.split('./')[-1]
    return os.path.join(directory, rel_path)

def normalize_path(path: str) -> str:
    """Normalize path for comparison"""
    return os.path.normpath(path).replace('\\', '/')

def resolve_absolute_import_path(import_path: str, file_directory: str, ts_root_dir: str) -> str:
    """Resolve import path to absolute filesystem path"""
    if import_path.startswith('.'):
        # Relative import
        return normalize_path(get_import_path(import_path, directory=file_directory))
    else:
        # Assume relative to ts root
        return normalize_path(os.path.join(ts_root_dir, import_path))
# === PATH CONVERSION ===
def resolve_absolute_import_path(import_path: str, file_directory: str, ts_root_dir: str) -> str:
    """Resolve import path to absolute filesystem path"""
    if import_path.startswith('.'):
        # Relative import - resolve from file directory
        abs_path = os.path.abspath(os.path.join(file_directory, import_path))
        return normalize_path(abs_path)
    else:
        # Assume relative to ts root
        return normalize_path(os.path.join(ts_root_dir, import_path))

def find_matching_alias(absolute_path: str, path_aliases: Dict[str, PathAlias]) -> Optional[Tuple[str, str, bool]]:
    """Find best matching path alias"""
    best_match = None
    best_match_len = 0
    
    for alias_key, path_alias in path_aliases.items():
        resolved = path_alias.resolved_path
        
        if absolute_path.startswith(resolved):
            match_len = len(resolved)
            remainder = absolute_path[match_len:].lstrip('/')
            
            # Validate wildcard support
            if remainder and not path_alias.has_wildcard:
                continue
            
            if match_len > best_match_len:
                best_match_len = match_len
                best_match = (alias_key, remainder, path_alias.has_wildcard)
    
    return best_match

def convert_to_alias_path(import_stmt: ImportStatement, file_directory: str, 
                          ts_root_dir: str, path_aliases: Dict[str, PathAlias]) -> Optional[str]:
    """Convert import path to alias path if possible"""
    abs_path = resolve_absolute_import_path(import_stmt.from_path, file_directory, ts_root_dir)
    match = find_matching_alias(abs_path, path_aliases)
    
    if match:
        alias_key, remainder, has_wildcard = match
        if remainder and has_wildcard:
            return f"{alias_key}/{remainder}"
        elif not remainder:
            return alias_key
    
    return None
