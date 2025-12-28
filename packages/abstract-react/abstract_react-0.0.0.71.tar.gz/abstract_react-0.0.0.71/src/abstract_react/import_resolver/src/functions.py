from ..imports import *
def make_relative_import(from_file: str, target_file: str) -> str:
    from_dir = os.path.dirname(from_file)

    rel = os.path.relpath(target_file, from_dir)
    rel = rel.replace(os.sep, '/')

    # remove extension (ESM style)
    rel = os.path.splitext(rel)[0]

    if not rel.startswith('.'):
        rel = f'./{rel}'

    return rel


def auto_patch_project(src_root: Path):
    graph = build_graph_all(src_root)
    imports_by_file = generate_imports(graph, src_root)

    changed = 0
    for file, import_lines in imports_by_file.items():
        p = Path(file)
        if not p.exists():
            continue
        if p.suffix not in {".ts", ".tsx"}:
            continue

        did_change = patch_file(p, import_lines)
        if did_change:
            changed += 1



def is_local_import(line: str) -> bool:
    return (
        "from './" in line
        or 'from "../' in line
        or "from '/" in line
    )

def split_header_and_body(src: str):
    """
    Preserve:
      - shebang
      - comments
      - "use client" / "use server"
    """
    lines = src.splitlines()
    header = []
    body = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if (
            stripped.startswith("//")
            or stripped.startswith("/*")
            or stripped.startswith("*")
            or stripped.startswith("#!")
            or stripped in ('"use client";', "'use client';", '"use server";', "'use server';")
            or stripped == ""
        ):
            header.append(line)
            i += 1
            continue

        break

    body = lines[i:]
    return header, body
def remove_local_imports(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        if line.lstrip().startswith("import") and is_local_import(line):
            continue
        out.append(line)
    return out
def patch_file(file_path: Path, import_lines: list[str]):
    original = file_path.read_text(encoding="utf-8", errors="ignore")

    header, body = split_header_and_body(original)
    body = remove_local_imports(body)

    new_src = []

    if header:
        new_src.extend(header)
        if header[-1].strip():
            new_src.append("")

    if import_lines:
        new_src.extend(import_lines)
        new_src.append("")

    new_src.extend(body)

    result = "\n".join(new_src).rstrip() + "\n"

    if result != original:
        file_path.write_text(result, encoding="utf-8")
        return True

    return False
