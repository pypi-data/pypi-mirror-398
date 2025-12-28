from ..imports import *
from .pathUtils import *
# === CONSOLIDATION ===
def consolidate_imports_with_comments(imports: List[ImportStatement], file_directory: str,
                                     ts_root_dir: str, path_aliases: Dict[str, PathAlias]) -> Dict[str, dict]:
    """Consolidate imports preserving comments"""
    consolidated = defaultdict(lambda: {'symbols': set(), 'comments': []})
    
    for import_stmt in imports:
        alias_path = convert_to_alias_path(import_stmt, file_directory, ts_root_dir, path_aliases)
        target_path = alias_path if alias_path else import_stmt.from_path
        
        for symbol in import_stmt.imports:
            consolidated[target_path]['symbols'].add(symbol)
        
        if import_stmt.trailing_comment:
            comment = import_stmt.trailing_comment.strip()
            if comment and not comment.startswith('//'):
                comment = '// ' + comment
            consolidated[target_path]['comments'].append(comment)
    
    return consolidated

def generate_import_statements_with_comments(consolidated: Dict[str, dict]) -> List[str]:
    """Generate import statements with comments"""
    import_lines = []
    
    for path in sorted(consolidated.keys()):
        data = consolidated[path]
        symbols = sorted(data['symbols'])
        comments = data['comments']
        
        if len(symbols) == 1:
            import_line = f"import {{ {symbols[0]} }} from '{path}';"
        else:
            symbols_str = ', '.join(symbols)
            import_line = f"import {{ {symbols_str} }} from '{path}';"
        
        if comments:
            unique_comments = list(dict.fromkeys(comments))
            if len(unique_comments) == 1:
                import_line += f" {unique_comments[0]}"
            else:
                for comment in unique_comments:
                    import_lines.append(comment)
                import_lines.append(import_line)
                continue
        
        import_lines.append(import_line)
    
    return import_lines
