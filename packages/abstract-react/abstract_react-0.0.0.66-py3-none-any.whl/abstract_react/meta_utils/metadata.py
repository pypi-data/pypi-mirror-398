import re

ATTR_RE = re.compile(r'([a-zA-Z0-9:_-]+)\s*=\s*([\'"`])([^\'"`]+)\2')

def meta_line_to_js(line: str) -> dict:
    """
    Convert <meta ...> or <link ...> into a JS-friendly dict.
    Works regardless of:
      - single, double, or backtick quotes
      - attribute order
      - extra spaces
      - self-closing tags
    """
    out = {}
    s = line.strip()

    # detect tag type (<meta, <link, <title>, etc.)
    m = re.match(r"<\s*([a-zA-Z0-9:_-]+)", s)
    if m:
        out["type"] = m.group(1).lower()

    # extract all key="value", key='value', key=`value`
    for key, quote, val in ATTR_RE.findall(s):
        out[key] = val

    return out

ATTR_RE = re.compile(r'([a-zA-Z0-9:_-]+)\s*=\s*([\'"`])([^\'"`]+)\2')
TAG_OPEN_RE = re.compile(r'<\s*([a-zA-Z0-9:_-]+)')
TAG_CONTENT_RE = re.compile(r'<\s*([a-zA-Z0-9:_-]+)[^>]*>(.*?)</\s*\1\s*>', re.DOTALL)

def parse_head_line(line: str) -> dict:
    """
    Convert <meta>, <link>, <title>, <script>, etc.
    into a clean JS-like dict.
    """

    line = line.strip()
    if not line.startswith("<"):
        return {}

    out = {}

    # ------------------------------------------------
    # 1. Check for contentful tags (title, script, style…)
    # ------------------------------------------------
    m = TAG_CONTENT_RE.search(line)
    if m:
        tag = m.group(1).lower()
        content = m.group(2).strip()
        out["type"] = tag
        out["content"] = content
        return out

    # ------------------------------------------------
    # 2. If not contentful, extract tag type
    # ------------------------------------------------
    m = TAG_OPEN_RE.match(line)
    if m:
        out["type"] = m.group(1).lower()

    # ------------------------------------------------
    # 3. Extract attributes (meta/link/img/etc.)
    # ------------------------------------------------
    for key, quote, val in ATTR_RE.findall(line):
        out[key] = val

    return out


def convert_head_block(text: str):
    items = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("<") and not line.startswith("<!--"):
            parsed = parse_head_line(line)
            if parsed:
                items.append(parsed)
    return items
