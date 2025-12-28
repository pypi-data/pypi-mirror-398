from .schemas import *

# ============================================================================
# Enhanced Symbol Registry
# ============================================================================

class ProductionSymbolRegistry:
    """
    Industrial-strength symbol registry.
    Handles re-exports, barrel files, ambiguous symbols.
    """
    
    def __init__(self):
        # Core mappings
        self._exports: Dict[str, Dict[str, ExportSpec]] = defaultdict(dict)
        self._symbol_to_sources: Dict[str, List[str]] = defaultdict(list)
        self._reexport_chains: Dict[Tuple[str, str], str] = {}  # (file, symbol) -> original_source
        
        # Barrel file tracking
        self._barrel_files: Set[str] = set()
        self._index_files: Dict[str, List[str]] = {}  # directory -> [files in that dir]
        
        # Default exports
        self._default_exports: Dict[str, ExportSpec] = {}
        
    def register_export(self, export: ExportSpec) -> None:
        """Register an export"""
        self._exports[export.source_file][export.name] = export
        self._symbol_to_sources[export.name].append(export.source_file)
        
        if export.kind == "default":
            self._default_exports[export.source_file] = export
    
    def register_reexport(self, file: str, symbol: str, from_file: str) -> None:
        """Register a re-export chain"""
        self._reexport_chains[(file, symbol)] = from_file
    
    def mark_barrel_file(self, file: str) -> None:
        """Mark a file as a barrel/index file"""
        self._barrel_files.add(file)
    
    def resolve_symbol_source(self, symbol: str, requesting_file: str) -> Optional[str]:
        """
        Resolve where to import a symbol from.
        
        Strategy:
        1. Check same directory first (prefer local imports)
        2. Check barrel files in parent directories
        3. Check all other sources
        4. Handle ambiguity by proximity
        """
        sources = self._symbol_to_sources.get(symbol, [])
        if not sources:
            return None
        
        if len(sources) == 1:
            return self._resolve_through_reexports(sources[0], symbol)
        
        # Multiple sources - disambiguate by proximity
        requesting_path = Path(requesting_file)
        requesting_dir = requesting_path.parent
        
        # Priority 1: Same directory
        for source in sources:
            if Path(source).parent == requesting_dir:
                return self._resolve_through_reexports(source, symbol)
        
        # Priority 2: Barrel file in parent directory
        for source in sources:
            if source in self._barrel_files:
                source_dir = Path(source).parent
                if requesting_dir.is_relative_to(source_dir):
                    return self._resolve_through_reexports(source, symbol)
        
        # Priority 3: Closest by path distance
        def path_distance(src: str) -> int:
            try:
                rel = Path(requesting_file).relative_to(Path(src).parent)
                return len(rel.parts)
            except ValueError:
                return 9999
        
        closest = min(sources, key=path_distance)
        return self._resolve_through_reexports(closest, symbol)
    
    def _resolve_through_reexports(self, file: str, symbol: str) -> str:
        """Follow re-export chain to find original source"""
        key = (file, symbol)
        if key in self._reexport_chains:
            return self._resolve_through_reexports(self._reexport_chains[key], symbol)
        return file
    
    def get_default_export(self, file: str) -> Optional[ExportSpec]:
        """Get default export for a file"""
        return self._default_exports.get(file)
    
    def is_barrel_file(self, file: str) -> bool:
        """Check if file is a barrel"""
        return file in self._barrel_files
