from abstract_utilities import capitalize
def get_react_type_string(value,nullsafe=True):

    types_js = {"string":str,"Array<any>":list,"integer":int,"BigNumber":float,"Record<any,any>":dict}
    for key,value_typ in types_js.items():
        if type(value) == value_typ:
            return f"{key} | null"
    
    return 'any'
def create_react_type(
    fields: dict[str, str | dict],
    name: str | None = None,
    indent: int = 0,
    optional_vars=True,
    nullsafe=True
) -> str:
    pad = "  " * indent
    lines = []

    if name:
        name = name[:1].upper() + name[1:]
        lines.append(f"{pad}export interface {name} {{")
    else:
        lines.append(f"{pad}{{")

    for key, value in fields.items():
        if '-' in key:
            key = f"'{key}'"
        ts_type = get_react_type_string(value,nullsafe=nullsafe)
        if isinstance(value, dict):
            nested = create_react_type(value, indent=indent + 1)
            lines.append(f"{pad}  {key}{'?' if optional_vars else ''}: {nested};")
        else:
            lines.append(f"{pad}  {key}{'?' if optional_vars else ''}: {ts_type};")

    lines.append(f"{pad}}}")

    return "\n".join(lines)
