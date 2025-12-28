from .productionTypescriptParser import *
# ============================================================================
# Production Import Resolver
# ============================================================================

class ProductionImportResolver:
    """
    Resolve imports for messy codebases.
    Handles ambiguity, missing symbols, barrel files, etc.
    """
    
    def __init__(self):
        self.registry = ProductionSymbolRegistry()
        self.parser = ProductionTypeScriptParser()
        self.file_analysis: Dict[str, Tuple] = {}
    
    def analyze_project(self, root_dir: Path, verbose: bool = True) -> None:
        """Analyze entire project"""
        if verbose:
            print(f"🔍 Analyzing project: {root_dir}")
        
        # Find all TypeScript files
        ts_files = list(root_dir.rglob("*.ts")) + list(root_dir.rglob("*.tsx"))
        ts_files = [f for f in ts_files if 'node_modules' not in f.parts]
        
        if verbose:
            print(f"   Found {len(ts_files)} files")
        
        # Phase 1: Parse all files
        if verbose:
            print(f"📖 Phase 1: Parsing files...")
        
        for i, file_path in enumerate(ts_files):
            if verbose and i % 50 == 0:
                print(f"   Parsed {i}/{len(ts_files)}...")
            
            exports, usage, declarations = self.parser.parse_file(file_path)
            self.file_analysis[str(file_path)] = (exports, usage, declarations)
            
            # Register exports
            for export in exports:
                self.registry.register_export(export)
                
                # Track re-export chains
                if export.is_reexport and export.reexport_from:
                    self.registry.register_reexport(
                        export.source_file,
                        export.name,
                        export.reexport_from
                    )
            
            # Mark barrel files
            if self.parser._is_barrel_file(file_path, exports):
                self.registry.mark_barrel_file(str(file_path))
        
        if verbose:
            print(f"✅ Analysis complete!")
            print(f"   Total exports: {len(self.registry._symbol_to_sources)}")
            print(f"   Barrel files: {len(self.registry._barrel_files)}")
    
    def resolve_imports_for_file(self, file_path: str) -> List[ImportNeed]:
        """Resolve what a file needs to import"""
        if file_path not in self.file_analysis:
            return []
        
        exports, usage, declarations = self.file_analysis[file_path]
        
        # Symbols that need imports
        needs_import = set(usage.keys()) - declarations
        
        # Resolve each symbol
        import_needs = []
        
        for symbol in needs_import:
            # Find source
            source = self.registry.resolve_symbol_source(symbol, file_path)
            
            if not source:
                # Symbol not found in project - skip (probably node_modules)
                continue
            
            if source == file_path:
                # Self-import - skip
                continue
            
            # Determine import type
            symbol_usage = usage[symbol]
            is_type_only = symbol_usage.contexts == {"type"}
            
            # Check if it's a default export
            default_export = self.registry.get_default_export(source)
            import_type = "default" if (default_export and default_export.name == symbol) else "named"
            
            import_needs.append(ImportNeed(
                symbol=symbol,
                from_file=source,
                import_type=import_type,
                is_type_only=is_type_only
            ))
        
        return import_needs
    
    def generate_import_statements(self, file_path: str) -> List[str]:
        """Generate actual import statement strings"""
        needs = self.resolve_imports_for_file(file_path)
        
        if not needs:
            return []
        
        # Group by source file
        by_source: Dict[str, List[ImportNeed]] = defaultdict(list)
        for need in needs:
            by_source[need.from_file].append(need)
        
        # Generate statements
        statements = []
        
        for source_file, needs_from_source in sorted(by_source.items()):
            rel_path = self._get_relative_path(file_path, source_file)
            
            # Separate into categories
            default_imports = [n for n in needs_from_source if n.import_type == "default"]
            named_values = [n for n in needs_from_source if n.import_type == "named" and not n.is_type_only]
            named_types = [n for n in needs_from_source if n.import_type == "named" and n.is_type_only]
            
            # Generate import lines
            if default_imports:
                # Default import
                default_name = default_imports[0].symbol
                if named_values or named_types:
                    # Mixed import
                    if named_values:
                        names = ", ".join(sorted(n.symbol for n in named_values))
                        statements.append(f'import {default_name}, {{ {namake_relative_importmes} }} from "{rel_path}";')
                    if named_types:
                        names = ", ".join(sorted(n.symbol for n in named_types))
                        statements.append(f'import {default_name} from "{rel_path}";')
                        statements.append(f'import type {{ {names} }} from "{rel_path}";')
                else:
                    statements.append(f'import {default_name} from "{rel_path}";')
            else:
                # Only named imports
                if named_values:
                    names = ", ".join(sorted(n.symbol for n in named_values))
                    statements.append(f'import {{ {names} }} from "{rel_path}";')
                
                if named_types:
                    names = ", ".join(sorted(n.symbol for n in named_types))
                    statements.append(f'import type {{ {names} }} from "{rel_path}";')
        
        return statements
    
    def _get_relative_path(self, from_file: str, to_file: str) -> str:
        """Calculate relative import path"""

        return make_relative_import(from_file, to_file)
    def get_diagnostics(self, file_path: str) -> dict:
        """Get detailed diagnostics for a file"""
        if file_path not in self.file_analysis:
            return {"error": "File not analyzed"}
        
        exports, usage, declarations = self.file_analysis[file_path]
        needs = self.resolve_imports_for_file(file_path)
        
        # Find unresolved symbols
        unresolved = []
        for symbol in usage.keys():
            if symbol not in declarations:
                source = self.registry.resolve_symbol_source(symbol, file_path)
                if not source:
                    unresolved.append(symbol)
        
        return {
            "file": file_path,
            "exports_count": len(exports),
            "exports": [e.name for e in exports],
            "symbols_used": len(usage),
            "local_declarations": len(declarations),
            "needs_imports": len(needs),
            "unresolved_symbols": unresolved,
            "is_barrel": self.registry.is_barrel_file(file_path)
        }
