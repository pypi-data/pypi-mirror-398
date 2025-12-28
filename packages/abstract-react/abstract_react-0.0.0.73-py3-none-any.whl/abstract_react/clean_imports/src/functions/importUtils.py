from ..imports import *
# === IMPORT SYMBOL PARSING ===
def parse_import_symbols(import_text: str) -> List[str]:
    """Extract all imported symbols from import text"""
    # Remove 'import' keyword and normalize whitespace
    import_text = import_text.replace('import', '', 1)
    import_text = re.sub(r'\s+', ' ', import_text)  # Collapse all whitespace
    import_text = import_text.strip()
    
    # Split by 'from'
    if ' from ' not in import_text:
        return []
    
    import_part, _ = import_text.split(' from ', 1)
    import_part = import_part.strip()
    
    # Handle different import types
    if '{' in import_part and '}' in import_part:
        # Named imports: { A, B, C }
        inside_braces = import_part[import_part.find('{')+1:import_part.rfind('}')]
        inside_braces = inside_braces.strip().rstrip(',')
        
        # Split by comma and clean
        symbols = []
        for s in inside_braces.split(','):
            s = s.strip()
            if s:
                symbols.append(s)
        return symbols
        
    elif import_part.startswith('* as '):
        # Namespace import
        return [import_part.replace('* as ', '').strip()]
    
    else:
        # Default import
        return [import_part.strip()]

def extract_from_path(import_text: str) -> str:
    """Extract the 'from' path from import text"""
    if ' from ' not in import_text:
        return ''
    
    _, path_part = import_text.split(' from ', 1)
    
    # Remove semicolon, quotes, whitespace
    from_path = path_part.strip()
    from_path = from_path.rstrip(';').strip()
    from_path = from_path.strip('"\'')
    
    return from_path
# === FIXED MULTI-LINE IMPORT ACCUMULATOR ===
def get_complete_import_text(lines: List[str], start_idx: int) -> Tuple[int, str]:
    """Extract complete import statement starting at start_idx
    
    Returns: (end_idx, complete_import_text)
    """
    import_parts = []
    
    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        import_parts.append(line)
        
        # Check if this line completes the import (has semicolon)
        if ';' in line:
            complete_import = ' '.join(import_parts)
            return idx, complete_import
    
    # If we reach here, import wasn't closed properly
    # Return what we have
    return len(lines) - 1, ' '.join(import_parts)

def extract_imports_from_lines(lines: List[str]) -> List[Tuple[int, int, str]]:
    """Extract all import statements from raw text lines
    
    Returns: [(start_idx, end_idx, complete_import_text)]
    """
    imports = []
    idx = 0
    
    while idx < len(lines):
        line = lines[idx].strip()
        
        # Check if line starts an import
        if line.startswith('import'):
            end_idx, complete_import = get_complete_import_text(lines, idx)
            imports.append((idx, end_idx, complete_import))
            idx = end_idx + 1  # Skip to line after import ends
        else:
            idx += 1
    
    return imports
# === COMPLETE IMPORT EXTRACTION ===
def extract_all_imports_robust(file_path: str) -> List[ImportStatement]:
    """Extract all imports using simple line-based approach"""
    # Read raw lines (not using the complex parser initially)
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
    
    # Strip only trailing newlines, preserve indentation
    lines = [line.rstrip('\n\r') for line in raw_lines]
    
    # Extract imports
    import_blocks = extract_imports_from_lines(lines)
    
    imports = []
    for start_idx, end_idx, import_text in import_blocks:
        # Parse symbols
        symbols = parse_import_symbols(import_text)
        if not symbols:
            continue
        
        # Extract path
        from_path = extract_from_path(import_text)
        if not from_path:
            continue
        
        is_relative = from_path.startswith('.') or from_path.startswith('..')
        
        # Extract trailing comment
        trailing_comment = None
        if '//' in import_text:
            # Find comment after the semicolon (if any)
            parts = import_text.split(';', 1)
            if len(parts) > 1 and '//' in parts[1]:
                comment_part = parts[1].split('//', 1)[1]
                trailing_comment = '//' + comment_part.strip()
        
        imports.append(ImportStatement(
            raw_lines=lines[start_idx:end_idx+1],
            imports=symbols,
            from_path=from_path,
            is_relative=is_relative,
            start_line_index=start_idx,
            end_line_index=end_idx,
            trailing_comment=trailing_comment
        ))
    
    return imports
