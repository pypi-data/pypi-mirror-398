from ..imports import *
from .diffUtils import *
# === BACKUP HANDLING ===
def create_backup(file_path: str) -> str:
    """Create backup of file before modification
    
    Returns: backup file path
    """
    backup_path = f"{file_path}.backup"
    
    # If backup already exists, add timestamp
    if os.path.exists(backup_path):
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{file_path}.backup.{timestamp}"
    
    # Copy file to backup
    import shutil
    shutil.copy2(file_path, backup_path)
    
    return backup_path

# === SAFE WRITE ===
def write_replacement(replacement: FileReplacement, 
                     create_backup_file: bool = True,
                     dry_run: bool = False) -> dict:
    """Write replacement to file with safety checks
    
    Args:
        replacement: FileReplacement object
        create_backup_file: Whether to create .backup file
        dry_run: If True, don't actually write
    
    Returns:
        {
            'written': bool,
            'backup_path': str or None,
            'changes': str (summary)
        }
    """
    result = {
        'written': False,
        'backup_path': None,
        'changes': show_import_changes(replacement)
    }
    
    if dry_run:
        result['changes'] += "\n\n[DRY RUN - No files modified]"
        return result
    
    # Create backup if requested
    if create_backup_file:
        backup_path = create_backup(replacement.file_path)
        result['backup_path'] = backup_path
    
    # Write new content
    with open(replacement.file_path, 'w', encoding='utf-8') as f:
        f.write(replacement.new_content)
    
    result['written'] = True
    
    return result
