from .ProductionSymbolRegistry import *
# ============================================================================
# Enhanced Parser with ALL TypeScript Patterns
# ============================================================================

class ProductionTypeScriptParser:
    """
    Parse ALL TypeScript import/export patterns.
    Handles edge cases, barrel files, re-exports, etc.
    """
    
    # Comprehensive regex patterns
    PATTERNS = {
        # Exports
        'export_named': re.compile(
            r'export\s+(?:const|let|var|function|class|enum)\s+([A-Za-z_$][\w$]*)',
            re.MULTILINE
        ),
        'export_type': re.compile(
            r'export\s+(?:type|interface)\s+([A-Za-z_$][\w$]*)',
            re.MULTILINE
        ),
        'export_default_named': re.compile(
            r'export\s+default\s+(?:class|function)\s+([A-Za-z_$][\w$]*)',
            re.MULTILINE
        ),
        'export_default_expr': re.compile(
            r'export\s+default\s+([A-Za-z_$][\w$]*)',
            re.MULTILINE
        ),
        'export_list': re.compile(
            r'export\s*\{\s*([^}]+)\s*\}(?:\s+from\s+["\']([^"\']+)["\'])?',
            re.MULTILINE
        ),
        'export_star': re.compile(
            r'export\s+\*\s+from\s+["\']([^"\']+)["\']',
            re.MULTILINE
        ),
        
        # Imports
        'import_named': re.compile(
            r'import\s+(?:type\s+)?\{\s*([^}]+)\s*\}\s+from\s+["\']([^"\']+)["\']',
            re.MULTILINE
        ),
        'import_default': re.compile(
            r'import\s+([A-Za-z_$][\w$]*)\s+from\s+["\']([^"\']+)["\']',
            re.MULTILINE
        ),
        'import_namespace': re.compile(
            r'import\s+\*\s+as\s+([A-Za-z_$][\w$]*)\s+from\s+["\']([^"\']+)["\']',
            re.MULTILINE
        ),
        'import_side_effect': re.compile(
            r'import\s+["\']([^"\']+)["\']',
            re.MULTILINE
        ),
        'import_mixed': re.compile(
            r'import\s+([A-Za-z_$][\w$]*)\s*,\s*\{\s*([^}]+)\s*\}\s+from\s+["\']([^"\']+)["\']',
            re.MULTILINE
        ),
        
        # Usage patterns
        'function_call': re.compile(
            r'\b([a-z_$][\w$]*)\s*\(',
            re.MULTILINE
        ),
        'class_instantiation': re.compile(
            r'new\s+([A-Z][\w$]*)',
            re.MULTILINE
        ),
        'type_annotation': re.compile(
            r':\s*([A-Z][\w$]*)',
            re.MULTILINE
        ),
        'jsx_component': re.compile(
            r'<([A-Z][\w$]*)',
            re.MULTILINE
        ),
        'generic_type': re.compile(
            r'<([A-Z][\w$]*)[,>]',
            re.MULTILINE
        ),
        
        # Declarations
        'const_declaration': re.compile(
            r'const\s+([A-Za-z_$][\w$]*)',
            re.MULTILINE
        ),
        'function_declaration': re.compile(
            r'function\s+([A-Za-z_$][\w$]*)',
            re.MULTILINE
        ),
        'class_declaration': re.compile(
            r'class\s+([A-Za-z_$][\w$]*)',
            re.MULTILINE
        ),
        'type_declaration': re.compile(
            r'(?:type|interface)\s+([A-Za-z_$][\w$]*)',
            re.MULTILINE
        ),
    }
    
    def parse_file(self, file_path: Path) -> Tuple[List[ExportSpec], Dict[str, SymbolUsage], Set[str]]:
        """
        Parse file completely.
        
        Returns:
            (exports, symbol_usage, local_declarations)
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
            return [], {}, set()
        
        # Clean content
        clean_content = self._remove_noise(content)
        
        # Extract everything
        exports = self._parse_exports(clean_content, str(file_path))
        usage = self._parse_usage(clean_content)
        declarations = self._parse_declarations(clean_content)
        
        # Detect barrel files
        is_barrel = self._is_barrel_file(file_path, exports)
        
        return exports, usage, declarations
    
    def _remove_noise(self, content: str) -> str:
        """Remove strings, comments, etc."""
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Remove single-line comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        
        # Remove strings (but preserve structure)
        content = re.sub(r'"[^"]*"', '""', content)
        content = re.sub(r"'[^']*'", "''", content)
        content = re.sub(r'`[^`]*`', '``', content)
        
        return content
    
    def _parse_exports(self, content: str, file_path: str) -> List[ExportSpec]:
        """Parse all export patterns"""
        exports = []
        
        # Named exports (values)
        for match in self.PATTERNS['export_named'].finditer(content):
            name = match.group(1)
            exports.append(ExportSpec(
                name=name,
                kind="value",
                source_file=file_path
            ))
        
        # Named exports (types)
        for match in self.PATTERNS['export_type'].finditer(content):
            name = match.group(1)
            exports.append(ExportSpec(
                name=name,
                kind="type",
                source_file=file_path
            ))
        
        # Default exports (named)
        for match in self.PATTERNS['export_default_named'].finditer(content):
            name = match.group(1)
            exports.append(ExportSpec(
                name=name,
                kind="default",
                source_file=file_path
            ))
        
        # Default exports (expression)
        for match in self.PATTERNS['export_default_expr'].finditer(content):
            name = match.group(1)
            # Skip if it's just 'export default class' (already caught above)
            if not re.match(r'(class|function)', name):
                exports.append(ExportSpec(
                    name=name,
                    kind="default",
                    source_file=file_path
                ))
        
        # Export lists
        for match in self.PATTERNS['export_list'].finditer(content):
            names_str = match.group(1)
            from_path = match.group(2)
            
            for name_part in names_str.split(','):
                # Handle: export { foo as bar }
                parts = name_part.strip().split(' as ')
                original_name = parts[0].strip()
                exported_name = parts[-1].strip()
                
                if from_path:
                    # Re-export
                    exports.append(ExportSpec(
                        name=exported_name,
                        kind="value",  # Don't know if type or value from re-export
                        source_file=file_path,
                        is_reexport=True,
                        reexport_from=self._resolve_import_path(file_path, from_path)
                    ))
                else:
                    # Local export
                    exports.append(ExportSpec(
                        name=exported_name,
                        kind="value",
                        source_file=file_path
                    ))
        
        # Export star (barrel files)
        for match in self.PATTERNS['export_star'].finditer(content):
            from_path = match.group(1)
            # Mark as re-export everything from this file
            exports.append(ExportSpec(
                name="*",
                kind="reexport",
                source_file=file_path,
                is_reexport=True,
                reexport_from=self._resolve_import_path(file_path, from_path)
            ))
        
        return exports
    
    def _parse_usage(self, content: str) -> Dict[str, SymbolUsage]:
        """Parse symbol usage with context"""
        usage = defaultdict(lambda: SymbolUsage(name=""))
        
        # Function calls
        for match in self.PATTERNS['function_call'].finditer(content):
            name = match.group(1)
            if name not in {'if', 'for', 'while', 'switch', 'catch'}:  # Skip keywords
                usage[name].name = name
                usage[name].contexts.add("call")
        
        # Class instantiation
        for match in self.PATTERNS['class_instantiation'].finditer(content):
            name = match.group(1)
            usage[name].name = name
            usage[name].contexts.add("instantiate")
        
        # Type annotations
        for match in self.PATTERNS['type_annotation'].finditer(content):
            name = match.group(1)
            usage[name].name = name
            usage[name].contexts.add("type")
        
        # JSX components
        for match in self.PATTERNS['jsx_component'].finditer(content):
            name = match.group(1)
            usage[name].name = name
            usage[name].contexts.add("jsx")
        
        # Generic types
        for match in self.PATTERNS['generic_type'].finditer(content):
            name = match.group(1)
            usage[name].name = name
            usage[name].contexts.add("type")
        
        return dict(usage)
    
    def _parse_declarations(self, content: str) -> Set[str]:
        """Parse local declarations"""
        declarations = set()
        
        for pattern_name in ['const_declaration', 'function_declaration', 
                             'class_declaration', 'type_declaration']:
            for match in self.PATTERNS[pattern_name].finditer(content):
                declarations.add(match.group(1))
        
        return declarations
    
    def _is_barrel_file(self, file_path: Path, exports: List[ExportSpec]) -> bool:
        """Detect if this is a barrel/index file"""
        # Check if filename is index.ts
        if file_path.stem == 'index':
            return True
        
        # Check if mostly re-exports
        if exports:
            reexport_count = sum(1 for e in exports if e.is_reexport)
            return reexport_count / len(exports) > 0.5
        
        return False
    
    def _resolve_import_path(self, from_file: str, import_path: str) -> str:
        """Resolve relative import to absolute path"""
        from_path = Path(from_file).parent
        
        if import_path.startswith('.'):
            # Relative import
            resolved = (from_path / import_path).resolve()
            
            # Try with extensions
            for ext in ['.ts', '.tsx', '.js', '.jsx']:
                if resolved.with_suffix(ext).exists():
                    return str(resolved.with_suffix(ext))
            
            # Try index file
            index_file = resolved / 'index.ts'
            if index_file.exists():
                return str(index_file)
            
            return str(resolved) + '.ts'  # Best guess
        else:
            # Node module - return as-is
            return import_path

