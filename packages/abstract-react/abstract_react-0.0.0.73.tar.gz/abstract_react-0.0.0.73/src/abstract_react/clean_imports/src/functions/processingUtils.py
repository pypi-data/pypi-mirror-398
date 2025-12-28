from ..imports import *
from .tsConfigHandling import *
from .pathUtils import *
from .importUtils import *
from .consolidateUtils import *
from .fileUtils import *
from .readWriteUtils import *
# === ENHANCED MAIN WORKFLOW ===
def consolidate_and_replace_imports(file_path: str, 
                                    directory: str,
                                    write_to_file: bool = False,
                                    create_backup_file: bool = True,
                                    show_diff: bool = False,
                                    show_debug: bool = False) -> dict:
    """Complete workflow: consolidate imports and replace in file
    
    Args:
        file_path: Path to file to process
        directory: Project directory
        write_to_file: Actually write changes to file
        create_backup_file: Create .backup file before writing
        show_diff: Show unified diff
        show_debug: Show debug information
    
    Returns:
        Complete result dictionary with all details
    """
    # Setup environment
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    file_directory = os.path.dirname(file_path)
    path_aliases = build_path_alias_registry(directory=directory)
    
    # Extract imports
    imports = extract_all_imports_robust(file_path)
    input(imports)
    if show_debug:
        print("=== EXTRACTED IMPORTS ===")
        for i, imp in enumerate(imports):
            print(f"\n{i+1}. Lines {imp.start_line_index}-{imp.end_line_index}:")
            print(f"   From: {imp.from_path}")
            print(f"   Symbols ({len(imp.imports)}): {', '.join(imp.imports[:5])}")
            if len(imp.imports) > 5:
                print(f"            ... and {len(imp.imports) - 5} more")
    
    # Consolidate
    consolidated = consolidate_imports_with_comments(
        imports, file_directory, ts_root_dir, path_aliases
    )
    
    # Generate new imports
    new_imports = generate_import_statements_with_comments(consolidated)
    
    # Create replacement
    replacement = replace_imports_in_file(file_path, new_imports, imports)
    
    # Generate diff if requested
    diff = None
    if show_diff:
        diff = generate_diff(replacement.original_content, replacement.new_content)
    
    # Write if requested
    write_result = None
    if write_to_file:
        write_result = write_replacement(
            replacement, 
            create_backup_file=create_backup_file,
            dry_run=False
        )
    else:
        write_result = write_replacement(
            replacement,
            create_backup_file=False,
            dry_run=True
        )
    
    return {
        'replacement': replacement,
        'imports': imports,
        'consolidated': consolidated,
        'new_imports': new_imports,
        'diff': diff,
        'write_result': write_result,
        'stats': {
            'original_import_count': len(imports),
            'consolidated_import_count': len(new_imports),
            'total_symbols': sum(len(d['symbols']) for d in consolidated.values()),
            'lines_removed': len(replacement.import_section_removed),
            'lines_added': len(replacement.import_section_added),
            'line_reduction': len(replacement.import_section_removed) - len(replacement.import_section_added)
        }
    }

# === BATCH PROCESSING ===
def consolidate_imports_batch(directory: str, 
                              pattern: str = '*.ts',
                              write_to_files: bool = False,
                              create_backups: bool = True) -> List[dict]:
    """Process multiple files in batch
    
    Args:
        directory: Directory to search
        pattern: File pattern to match
        write_to_files: Actually write changes
        create_backups: Create backup files
    
    Returns:
        List of results for each file
    """
    file_paths = find_files(pattern, directory=directory)
    results = []
    
    for file_path in file_paths:
        try:
            result = consolidate_and_replace_imports(
                file_path,
                directory,
                write_to_file=write_to_files,
                create_backup_file=create_backups,
                show_debug=False
            )
            results.append({
                'file_path': file_path,
                'success': True,
                'result': result
            })
        except Exception as e:
            results.append({
                'file_path': file_path,
                'success': False,
                'error': str(e)
            })
    
    return results
