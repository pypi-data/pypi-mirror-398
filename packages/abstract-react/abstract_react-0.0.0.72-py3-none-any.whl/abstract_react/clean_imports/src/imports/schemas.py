from .constants import *
from .init_imports import *
# === SCHEMAS (previous ones plus new) ===
@dataclass
class FileReplacement:
    """Schema for file replacement operation"""
    original_content: str
    new_content: str
    import_section_removed: List[str]  # Old import lines
    import_section_added: List[str]    # New import lines
    file_path: str
    backup_path: Optional[str]
@dataclass
class PathAlias:
    """Schema for tsconfig path mapping"""
    alias: str
    resolved_path: str
    base_dir: str
    has_wildcard: bool
    
@dataclass
class LineSegment:
    """Schema for line segment (content or comment)"""
    type: str  # 'content' or 'comments'
    text: str
    placement: int

@dataclass
class ParsedLine:
    """Schema for parsed TypeScript line"""
    segments: List[LineSegment]
    raw_content: str
    raw_comments: str
    line_index: int
    
@dataclass
class ImportStatement:
    """Schema for parsed import"""
    raw_lines: List[str]
    imports: List[str]
    from_path: str
    is_relative: bool
    start_line_index: int
    end_line_index: int
    trailing_comment: Optional[str]

@dataclass
class FileSection:
    """Schema for file sections"""
    type: str  # 'import', 'code', 'comment_block'
    lines: List[ParsedLine]
    start_index: int
    end_index: int

@dataclass
class ReconstructionQueue:
    """Queue for file reconstruction"""
    import_section: FileSection
    code_sections: List[FileSection]
    new_imports: List[str]
    file_path: str


@dataclass
class ImportRegistry:
    """Central registry for import processing"""
    imports: List[ImportStatement]
    path_aliases: Dict[str, PathAlias]
    file_directory: str
    ts_root_dir: str
