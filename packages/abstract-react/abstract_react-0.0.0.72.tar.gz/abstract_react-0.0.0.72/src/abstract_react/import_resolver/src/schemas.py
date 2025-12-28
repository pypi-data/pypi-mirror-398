from .functions import *
# ============================================================================
# Enhanced Schemas
# ============================================================================

@dataclass
class ExportSpec:
    """What a file exports and how"""
    name: str
    kind: str  # "value", "type", "interface", "class", "function", "default"
    source_file: str
    is_reexport: bool = False
    reexport_from: Optional[str] = None  # If re-exported, where from originally
    
    def __hash__(self):
        return hash((self.name, self.source_file))


@dataclass
class ImportNeed:
    """What a file needs to import"""
    symbol: str
    from_file: str
    import_type: str  # "named", "default", "namespace", "side-effect"
    is_type_only: bool = False


@dataclass
class SymbolUsage:
    """How a symbol is used in a file"""
    name: str
    contexts: Set[str] = field(default_factory=set)  # "call", "type", "instantiate", "reference"
    line_numbers: List[int] = field(default_factory=list)
