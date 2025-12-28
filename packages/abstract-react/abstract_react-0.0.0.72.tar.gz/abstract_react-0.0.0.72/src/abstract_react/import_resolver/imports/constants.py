from .init_imports import *
RE_IMPORT_LINE = re.compile(r'^\s*import\s+.*?from\s+[\'"].+?[\'"];?\s*$', re.M)
RE_SIDE_EFFECT = re.compile(r'^\s*import\s+[\'"].+?[\'"];?\s*$', re.M)
