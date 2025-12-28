from .productionImportResolver import *
"""
Production-Grade TypeScript Import Resolver
Handles projects in shambles: missing imports, wrong imports, barrel files, re-exports, etc.

Goal: Given ANY .ts file, determine EXACTLY what it needs to import and from where.
"""

# ============================================================================
# CLI Interface
# ============================================================================

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python production_resolver.py analyze <project_dir>")
        print("  python production_resolver.py fix <project_dir>")
        print("  python production_resolver.py diagnostics <file> <project_dir>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        project_dir = Path(sys.argv[2])
        resolver = ProductionImportResolver()
        resolver.analyze_project(project_dir)
        
        # Show summary for each file
        print("\n" + "="*80)
        print("IMPORT ANALYSIS")
        print("="*80)
        
        for file_path in list(resolver.file_analysis.keys())[:10]:
            print(f"\n📄 {Path(file_path).name}")
            imports = resolver.generate_import_statements(file_path)
            if imports:
                for imp in imports[:5]:
                    print(f"   {imp}")
                if len(imports) > 5:
                    print(f"   ... and {len(imports) - 5} more")
    
    elif command == "fix":
        
        project_dir = Path(sys.argv[2])
        resolver = ProductionImportResolver()
        resolver.analyze_project(project_dir)
        
        print("\n🔧 Fixing imports...")
        changed = 0
        
        for file_path in resolver.file_analysis.keys():
            imports = resolver.generate_import_statements(file_path)
            p = Path(file_path)
            
            if patch_file(p, imports):
                changed += 1
                print(f"   ✅ {p.name}")
        
        print(f"\n✨ Fixed {changed} files")
    
    elif command == "diagnostics":
        file_path = sys.argv[2]
        project_dir = Path(sys.argv[3])
        
        resolver = ProductionImportResolver()
        resolver.analyze_project(project_dir)
        
        diag = resolver.get_diagnostics(file_path)
        
        print(json.dumps(diag, indent=2))



