from imports import *

domain="abstractendeavors.com"
info = getInfo(domain=domain)
info = get_pared_url_info(info)
input(process_metadata(info))
meta_info = get_meta_info(info)
input(meta_info)
