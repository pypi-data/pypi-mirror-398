from ..imports import *
# === FILE SECTION EXTRACTION ===
def extract_file_sections(file_path: str, imports: List[ImportStatement]) -> Tuple[List[str], List[str], List[str]]:
    """Extract file into three sections: before imports, imports, after imports
    
    Returns: (before_lines, import_lines, after_lines)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        all_lines = [line.rstrip('\n\r') for line in f.readlines()]
    
    if not imports:
        return [], [], all_lines
    
    # Find the range of import lines
    first_import_idx = min(imp.start_line_index for imp in imports)
    last_import_idx = max(imp.end_line_index for imp in imports)
    
    # Mark all import line indices
    import_line_indices = set()
    for import_stmt in imports:
        for idx in range(import_stmt.start_line_index, import_stmt.end_line_index + 1):
            import_line_indices.add(idx)
    
    # Split into sections
    before_lines = []
    import_lines = []
    after_lines = []
    
    for idx, line in enumerate(all_lines):
        if idx < first_import_idx:
            before_lines.append(line)
        elif idx in import_line_indices:
            import_lines.append(line)
        elif idx > last_import_idx:
            after_lines.append(line)
    
    return before_lines, import_lines, after_lines

# === FILE REPLACEMENT ===
def replace_imports_in_file(file_path: str, 
                           new_imports: List[str], 
                           imports: List[ImportStatement],
                           preserve_header_comments: bool = True) -> FileReplacement:
    """Replace old imports with new consolidated imports
    
    Args:
        file_path: Path to file
        new_imports: New consolidated import statements
        imports: Original import statements (for tracking what was removed)
        preserve_header_comments: Keep comments before first import
    
    Returns:
        FileReplacement schema with all details
    """
    # Read original
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Extract sections
    before_lines, import_lines, after_lines = extract_file_sections(file_path, imports)
    
    # Build new content
    new_content_lines = []
    
    # Add header (lines before imports)
    if preserve_header_comments and before_lines:
        new_content_lines.extend(before_lines)
        # Add blank line if header doesn't end with one
        if before_lines and before_lines[-1].strip():
            new_content_lines.append('')
    
    # Add new consolidated imports
    new_content_lines.extend(new_imports)
    
    # Add blank line after imports if after_lines doesn't start with blank
    if after_lines and after_lines[0].strip():
        new_content_lines.append('')
    
    # Add rest of file
    new_content_lines.extend(after_lines)
    
    new_content = '\n'.join(new_content_lines)
    
    return FileReplacement(
        original_content=original_content,
        new_content=new_content,
        import_section_removed=import_lines,
        import_section_added=new_imports,
        file_path=file_path,
        backup_path=None
    )
