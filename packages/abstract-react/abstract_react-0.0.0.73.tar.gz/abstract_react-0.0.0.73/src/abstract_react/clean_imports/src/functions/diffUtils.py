from ..imports import *
# === DIFF GENERATION ===
def generate_diff(original: str, new: str, context_lines: int = 3) -> str:
    """Generate unified diff between original and new content"""
    original_lines = original.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile='original',
        tofile='modified',
        lineterm='',
        n=context_lines
    )
    
    return ''.join(diff)

def show_import_changes(replacement: FileReplacement) -> str:
    """Generate human-readable summary of import changes"""
    output = []
    
    output.append("=" * 60)
    output.append("IMPORT REPLACEMENT SUMMARY")
    output.append("=" * 60)
    
    output.append(f"\nFile: {replacement.file_path}")
    
    output.append(f"\n--- REMOVED ({len(replacement.import_section_removed)} lines) ---")
    for line in replacement.import_section_removed:
        output.append(f"  - {line}")
    
    output.append(f"\n+++ ADDED ({len(replacement.import_section_added)} lines) +++")
    for line in replacement.import_section_added:
        output.append(f"  + {line}")
    
    reduction = len(replacement.import_section_removed) - len(replacement.import_section_added)
    if reduction > 0:
        output.append(f"\n✓ Reduced by {reduction} lines")
    elif reduction < 0:
        output.append(f"\n⚠ Increased by {abs(reduction)} lines")
    else:
        output.append(f"\n→ Same number of lines")
    
    output.append("=" * 60)
    
    return '\n'.join(output)
