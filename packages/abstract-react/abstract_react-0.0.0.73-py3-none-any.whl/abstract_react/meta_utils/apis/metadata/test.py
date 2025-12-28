import re,os
from wordsegment import load, segment
from abstract_utilities.file_utils.src.find_collect import *
from abstract_webtools import *
from pathlib import Path
from typing import Optional, List, Set






def get_find_cmd(
    *args,
    mindepth: Optional[int] = None,
    maxdepth: Optional[int] = None,
    depth: Optional[int] = None,
    file_type: Optional[str] = None,  # 'f' or 'd'
    name: Optional[str] = None,
    size: Optional[str] = None,
    mtime: Optional[str] = None,
    perm: Optional[str] = None,
    user: Optional[str] = None,
    **kwargs
) -> str:
    """
    Construct a Unix `find` command string that supports multiple directories.
    Accepts filtering via ScanConfig-compatible kwargs.
    """
    # Normalize inputs into canonical form
    kwargs = get_safe_canonical_kwargs(*args, **kwargs)
    cfg = kwargs.get('cfg') or define_defaults(**kwargs)

    # Get directory list (may come from args or kwargs)
    kwargs["directories"] = ensure_directories(*args, **kwargs)


    # Build base command for all directories
    dir_expr = " ".join(shlex.quote(d) for d in kwargs["directories"])
    cmd = [f"find {dir_expr}"]

    # --- depth filters ---
    if depth is not None:
        cmd += [f"-mindepth {depth}", f"-maxdepth {depth}"]
    else:
        if mindepth is not None:
            cmd.append(f"-mindepth {mindepth}")
        if maxdepth is not None:
            cmd.append(f"-maxdepth {maxdepth}")

    # --- file type ---
    if file_type in ("f", "d"):
        cmd.append(f"-type {file_type}")

    # --- basic attributes ---
    if name:
        cmd.append(f"-name {shlex.quote(name)}")
    if size:
        cmd.append(f"-size {shlex.quote(size)}")
    if mtime:
        cmd.append(f"-mtime {shlex.quote(mtime)}")
    if perm:
        cmd.append(f"-perm {shlex.quote(perm)}")
    if user:
        cmd.append(f"-user {shlex.quote(user)}")

    # --- cfg-based filters ---
    if cfg:
        # Allowed extensions
        if cfg.allowed_exts and cfg.allowed_exts != {"*"}:
            ext_expr = " -o ".join(
                [f"-name '*{e}'" for e in cfg.allowed_exts if e]
            )
            cmd.append(f"\\( {ext_expr} \\)")

        # Excluded extensions
        if cfg.exclude_exts:
            for e in cfg.exclude_exts:
                cmd.append(f"! -name '*{e}'")

        # Allowed directories
        if cfg.allowed_dirs and cfg.allowed_dirs != ["*"]:
            dir_expr = " -o ".join(
                [f"-path '*{d}*'" for d in cfg.allowed_dirs if d]
            )
            cmd.append(f"\\( {dir_expr} \\)")

        # Excluded directories
        if cfg.exclude_dirs:
            for d in cfg.exclude_dirs:
                cmd.append(f"! -path '*{d}*'")

        # Allowed patterns
        if cfg.allowed_patterns and cfg.allowed_patterns != ["*"]:
            pat_expr = " -o ".join(
                [f"-name '{p}'" for p in cfg.allowed_patterns if p]
            )
            cmd.append(f"\\( {pat_expr} \\)")

        # Excluded patterns
        if cfg.exclude_patterns:
            for p in cfg.exclude_patterns:
                cmd.append(f"! -name '{p}'")

        # Allowed types (semantic, not `-type`)
        if cfg.allowed_types and cfg.allowed_types != {"*"}:
            type_expr = " -o ".join(
                [f"-path '*{t}*'" for t in cfg.allowed_types if t]
            )
            cmd.append(f"\\( {type_expr} \\)")

        # Excluded types
        if cfg.exclude_types:
            for t in cfg.exclude_types:
                cmd.append(f"! -path '*{t}*'")

    return " ".join(cmd)



def collect_globs(
    *args,
    mindepth: Optional[int] = None,
    maxdepth: Optional[int] = None,
    depth: Optional[int] = None,
    file_type: Optional[str] = None,   # "f", "d", or None
    allowed: Optional[Callable[[str], bool]] = None,
    **kwargs
) -> List[str] | dict:
    """
    Collect file or directory paths recursively.

    - If file_type is None → returns {"f": [...], "d": [...]}
    - If file_type is "f" or "d" → returns a list of that type
    - Supports SSH mode via `user_at_host`
    """
    user_pass_host_key = get_user_pass_host_key(**kwargs)
    kwargs["directories"] = ensure_directories(*args, **kwargs)
    kwargs= get_safe_canonical_kwargs(**kwargs)
    kwargs["cfg"] = kwargs.get('cfg') or define_defaults(**kwargs)
    
    type_strs = {"f":"files","d":"dirs"}
    file_type = get_proper_type_str(file_type)
    file_types = make_list(file_type)
    if file_type == None:
        file_types = ["f","d"]
    return_results = {}
    return_result=[]
    for file_type in file_types:
        type_str = type_strs.get(file_type)
        # Remote path (SSH)
        find_cmd = get_find_cmd(
                directories=kwargs.get("directories"),
                cfg=kwargs.get('cfg'),
                mindepth=mindepth,
                maxdepth=maxdepth,
                depth=depth,
                file_type=file_type,
                **user_pass_host_key,
            )
        input(find_cmd)
        result = run_pruned_func(run_cmd,find_cmd,
            **user_pass_host_key,
            
            )
        return_result = [res for res in result.split('\n') if res]
        return_results[type_str]=return_result
    if len(file_types) == 1:
        return return_result
    return return_results
def get_files_and_dirs(
    *args,
    recursive: bool = True,
    include_files: bool = True,
    **kwargs
    ):
    if recursive == False:
        kwargs['maxdepth']=1
    if include_files == False:
        kwargs['file_type']='d'
    result = collect_globs(*args,**kwargs)
    if include_files == False:
        return result,[]
    if isinstance(result,list):
        return result
    dirs = result.get("dirs")
    files = result.get("files")
    return dirs,files
def collect_filepaths(
    *args,
    **kwargs
    ) -> List[str]:
    kwargs['file_type']='f'
    return collect_globs(*args,**kwargs)

def tokenize_domain(domain: str):
    domain = domain.lower().strip()
    root = re.sub(r"\.[a-z]{2,5}$", "", domain)

    load()  # loads tokenizer model once
    tokens = segment(root)  # <-- real statistical word tokenization

    return tokens
def get_abbr(domain=None,tokens=None):
    if domain or tokens:
        abbr = ""
        tokens = tokens or tokenize_domain(domain)
        for token in tokens:
            abbr+=token[0].upper()
        return abbr
def get_capitalize(domain=None,tokens=None):
    if domain or tokens:
        abbr = ""
        tokens = tokens or tokenize_domain(domain)
        for i,token in enumerate(tokens):
           tokens[i] =  capitalize(token)
        return tokens
def domain_title_potentials(domain):
    domain_name, ext = os.path.splitext(domain)
    title_potentials = [domain]

    tokens = tokenize_domain(domain)
    domain_name = ''.join(tokens)
    title_potentials.append(domain_name)

    capitalized = get_capitalize(domain=domain, tokens=tokens)
    cap_str = ' '.join(capitalized)
    title_potentials.append(cap_str)

    if len(capitalized) > 1:
        small_capitalized = capitalized[1:]
        small_cap_str = ' '.join(small_capitalized)
        title_potentials.append(small_cap_str)
        small_cap_str_name = ''.join(small_capitalized)
        title_potentials.append(small_cap_str_name)

    if len(capitalized) > 2:
        super_small_capitalized = capitalized[2:]
        super_small_cap_str = ' '.join(super_small_capitalized)
        title_potentials.append(super_small_cap_str)
        super_small_cap_str_name = ''.join(super_small_capitalized)
        title_potentials.append(super_small_cap_str_name)
    abbr = get_abbr(domain=domain, tokens=tokens)
    title_potentials.append(abbr)
    abbr_ext = f"{abbr}{ext}"
    title_potentials.append(abbr_ext)
    # --- CLEAN & SORT ---
    title_potentials = [x for x in title_potentials if x]           # drop empty
    title_potentials = list(dict.fromkeys(title_potentials))        # dedupe
    title_potentials = sorted(title_potentials, key=len, reverse=True)
    return title_potentials
class DomainManager(metaclass=SingletonMeta):
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.domains={}
    def process_domain(self,domain):
        if domain not in self.domains:
            if not domain.startswith('http'):
                domain = f"https://{domain}"
            parsed_dict = parse_url(domain)
            
            parsed_dict["title_potentials"] = domain_title_potentials(domain)
            allowed = parsed_dict.get('netloc',{}).get('domain',os.path.splitext(domain)[0])
            
            dirs= get_files_and_dirs('/server/var/www/sites',file_type='d',user_at_host='solcatcher')
            input(dirs)
dom_mgr= DomainManager()       
input(dom_mgr.process_domain('ireadsolidity.com'))
