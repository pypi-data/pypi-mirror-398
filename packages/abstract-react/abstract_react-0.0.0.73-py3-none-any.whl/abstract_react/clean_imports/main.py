
from src import *

# === EXECUTION ===
def clean_ts_imports_main(directory,autoSave=False):
    dirs,files = get_files_and_dirs(directory,allowed_exts=['.ts'],add=True)
    for file in files:
        result = consolidate_and_replace_imports(
            file, 
            directory,
            write_to_file=False,  # Preview only
            show_diff=False,
            show_debug=True
        )
        print("\n" + result['write_result']['changes'])
        print("\n=== NEW CONSOLIDATED IMPORTS ===")
        for imp in result['new_imports']:
            print(imp)
        print("\n=== STATISTICS ===")
        stats = result['stats']
        print(f"Original imports: {stats['original_import_count']}")
        print(f"Consolidated to: {stats['consolidated_import_count']}")
        print(f"Total symbols: {stats['total_symbols']}")
        print(f"Line reduction: {stats['line_reduction']}")
        print("\n=== FILE PREVIEW (first 35 lines) ===")
        preview_lines = result['replacement'].new_content.split('\n')[:35]
        for i, line in enumerate(preview_lines, 1):
            print(f"{i:3}: {line}")
        # Ask user if they want to proceed
        print("\n" + "=" * 70)
        
        if autoSave != True:
            response = input("Write changes to file? This will create a backup. (yes/no): ")
        else:
            response='y'
        if response.lower() in ['yes', 'y']:
            result = consolidate_and_replace_imports(
                file,
                directory,
                write_to_file=True,
                create_backup_file=True,
                show_debug=False
            )
            
            print("\n✓ File updated successfully!")
            print(f"✓ Backup created at: {result['write_result']['backup_path']}")
            print(result['write_result']['changes'])
        else:
            print("\n✗ No changes made.")
        
        # Example: Batch process all TypeScript files
        # print("\n" + "=" * 70)
        # print("BATCH PROCESSING")
        # print("=" * 70)
        # batch_results = consolidate_imports_batch(
        #     directory,
        #     pattern='*.ts',
        #     write_to_files=False,  # Preview only
        #     create_backups=True
        # )
        # 
        # for br in batch_results:
        #     if br['success']:
        #         print(f"\n✓ {br['file_path']}")
        #         print(f"  Reduced by {br['result']['stats']['line_reduction']} lines")
        #     else:
        #         print(f"\n✗ {br['file_path']}")
        #         print(f"  Error: {br['error']}")

