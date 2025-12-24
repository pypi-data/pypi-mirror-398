from imports import *
from abstract_apis import *

domain="abstractendeavors.com/howdy"
info = getInfo(domain=domain,thumbnail='/home/flerb/Pictures/abstractendeavors/AE.png')
parsed_url_info = get_pared_url_info(info)
kwargs = get_kwargs_value(dict_obj={},keys=BOOL_KEYS,default={})  
info = get_meta_info(info,**kwargs)
meta_tags = generate_meta_tags(info,parsed_url_info.get('variants')[0])

input(meta_tags)
