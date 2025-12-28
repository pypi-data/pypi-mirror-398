from abstract_utilities import *
from abstract_react import *
def split_caps(string):
    alphs_lower = 'abcdefghijklmnopqrstuvwxyz'
    alphs_upper = alphs_lower.upper()
    spl_chars = ''
    for char in string:
        if char in alphs_upper:
            char=f"_{char.lower()}"
        spl_chars+=char
    return spl_chars
def make_all_aliases(kinds,aliases):
    return_aliases = []
    
    for alias in aliases:
        return_aliases.append(alias)
        if '_' not in alias:
            alias = split_caps(alias)
        alias_spl = [al.lower() for al in alias.split('_') if al]
        alias_lower = ''.join(alias_spl)
        return_aliases.append(alias_lower)
        for i,alias_ap in enumerate(alias_spl):
            if i != 0:  
                alias_ap = capitalize(alias_ap)
            alias_spl[i] = alias_ap
        alias_upper = ''.join(alias_spl)
        return_aliases.append(alias_upper)
    return list(set([alias for alias in return_aliases if alias not in kinds]))
def are_equal(*nums):
    prev_num = None
    for num in nums:
        if prev_num == None:
            prev_num = num
        elif prev_num != num:
            return False
    return True
def get_full_args(string,fname):
    string_parts = {"fname":fname,"args":None,"returns":None}
    chars_js = {"(":1,")":0}
    string_spl = string.split('(')
    string_parts["fname"] = string_spl[0].split(' ')[-1]
    string_part = '('.join(string_spl[1:])
    for i,char in enumerate(string_part):
        if char in chars_js:
            chars_js[char]+=1
        values = chars_js.values()
        if are_equal(*values):
           
           string_parts["args"] = eatAll(string_part[:i],[')',' ','\n','\t','('])
           returns = string_part[i:].split('{')[0]
           
           string_parts["returns"] = eatAll(returns,['(',')',':',' ','\t','\n']) if [ret for ret in returns.split(' ') if ret] else None
           return string_parts
def create_alias_funcs(string,fname,aliases):
    full_args = get_full_args(string,fname)
    for i,alias in enumerate(aliases):
        args = full_args.get('args')
        input_args = ','.join([arg.split(':')[0] for arg in args.split(',') if ':' in arg])
        returns = full_args.get('returns')
        
        returns = f":{returns}" if returns else ""
        aliases[i] = f"\nexport function {alias}(\n\t{args}\n\t){returns} {{\n\t\treturn {fname}({input_args});\n\t}}\n"
    return aliases
def roll_types(kinds):
    types={}
    for key,value in kinds.items():
        if value not in types:
            types[value] = []
        if key not in types[value]:
            types[value].append(key)
    return types
def update_list_value(*lists):
    nu_list = []
    for li in lists:
        nu_list+=li
    return list(set(li))
    
def fnames_in_kinds(all_declared,file):
    contents_js = all_declared["scripts"][file]
    kinds = contents_js.get('kinds')
    fnames = all_declared.get('fnames')
    for fname,fname_values in fnames.items():
        variables = list(kinds.keys())
        if fname_values.get('file') == None and fname in variables:
            all_declared["fnames"][fname]['file'] = file
            all_declared["fnames"][fname]['aliases'] = make_all_aliases(kinds,fname_values.get('aliases'))
            contents_js["fnames"].append(fname)
    all_declared["scripts"][file] = contents_js   
    return all_declared
def get_all_func_names(json_path,all_declared=None):
    all_declared= all_declared or {"fnames":{},"scripts":{},"kinds":{},"types":{}}
    data = safe_read_from_json(json_path)
    dirname = os.path.dirname(json_path)
    dirs,sub_files = get_files_and_dirs(directory,allowed_exts='.ts')
    declared_fnames = all_declared.get('fnames')
    fnames = list(data.keys())
    for fname in fnames:
        if fname not in all_declared['fnames']:
            vals = make_list(data.get(fname) or fname)
            all_declared['fnames'][fname]={"file":None,"aliases":vals}
    for file in sub_files:
        contents = read_from_file(file)
        kinds = decl_kinds(contents)
        types = roll_types(kinds)
        all_declared["kinds"].update(kinds)
        all_declared["scripts"][file] = {"kinds":kinds,"types":{},"fnames":[]}
        for key,values in types.items():
            if key not in all_declared["types"]:
                all_declared["types"][key] = []
            all_declared["types"][key] = update_list_value(all_declared["types"][key],values)    
        all_declared = fnames_in_kinds(all_declared,file)
    return all_declared

directory = "/var/www/modules/packages/abstract-utilities/src"
dirs,json_paths = get_files_and_dirs(directory,allowed_patterns='alias_map')
all_declared={}
for json_path in json_paths:
    all_declared = get_all_func_names(json_path,all_declared=all_declared)
    all_declared_scripts = all_declared.get("scripts")
    all_declared_fnames = all_declared.get('fnames')
    
    for sub_file,values in all_declared_scripts.items():
        
        
        for fname in all_declared_fnames:
            contents = read_from_file(sub_file)
      
            fname_values = all_declared_fnames.get(fname)
            aliases = fname_values.get('aliases')
            
            all_aliases = []
            lines = contents.split('\n')
            aliases = list(set([alias for alias in fname_values.get('aliases') if alias not in decl_kinds(contents)]))
            for i,line in enumerate(lines):
                if line.startswith(f'export function {fname}'):
                    string = '\n'.join(lines[i:])
                
                    
                    alias_funcs = create_alias_funcs(string,fname,aliases)
                    all_aliases+=alias_funcs
            if all_aliases:
                all_aliases = [contents]+all_aliases
                contents = '\n'.join(all_aliases)
                
                write_to_file(contents=contents,file_path=sub_file)
                

