import os
from .title_variants import title_variants_from_domain

def is_string_in_range(s, size_range):
    if not isinstance(s, str):
        return False
    return size_range[0] <= len(s.strip()) <= size_range[1]

def get_max_or_limit(obj, limit=None):
    if limit and len(obj) >= limit:
        return obj[:limit]
    return obj

def title_add(current_string="", size_range=None):
    if not size_range or not isinstance(current_string, str):
        return current_string

    result = current_string.strip()
    min_len, max_len = size_range

    if is_string_in_range(result, size_range):
        return result

    potentials = title_variants_from_domain(result)
    sep = " | "

    for pot in potentials:
        candidate = result + sep + pot
        if len(candidate) <= max_len:
            result = candidate
            break

    while len(result) < min_len and len(result) < max_len:
        for pot in reversed(potentials):
            candidate = result + sep + pot
            if len(candidate) <= max_len:
                result = candidate
            else:
                break

    parts = result.split("|")
    parts = get_max_or_limit(parts, limit=3)
    return "|".join(parts).strip()

def pad_or_trim(typ, string, platform=None, META_VARS=None):
    if META_VARS is None:
        META_VARS = {
            "title": {"max": [0, 100]},
            "description": {"max": [0, 300]},
            "alt": {"max": [0, 200]}
        }

    if not isinstance(string, str):
        return ""

    string = string.strip()
    limits = META_VARS.get(typ, {"max": [0, float('inf')]})
    max_range = limits["max"]

    if platform == "twitter":
        if typ == "title": max_range = [60, 70]
        if typ == "description": max_range = [150, 200]

    elif platform == "og":
        if typ == "title":
            max_range = [60, 90]
            if len(string) > 100: return string[:88].strip()
        if typ == "description":
            max_range = [150, 200]
            if len(string) > 300: return string[:300].strip()

    if len(string) >= max_range[0]:
        return string[:max_range[1]].strip() if len(string) > max_range[1] else string

    padded = title_add(string, max_range)
    return padded[:max_range[1]].strip() if len(padded) > max_range[1] else padded
