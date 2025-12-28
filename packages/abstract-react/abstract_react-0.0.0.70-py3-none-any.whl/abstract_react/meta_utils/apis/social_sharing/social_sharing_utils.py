from .social_params import create_post_url
def get_post_text(data):
    output_text = ''
    title = data.get('title','')
    output_text+=title
    pageTitle = data.get('pageTitle','')
    if pageTitle:
        if output_text:
            output_text+=':'
        output_text+=pageTitle
    description = data.get('description','')
    if description:
        if output_text:
            output_text+='\n\n'
        output_text+=description
    text = get_data_from_alias(data,'text') or ''
    if text:
        if output_text:
            output_text+='\n'
        output_text+=text
    return output_text
def get_url(data):
    url = data.get('url') or data.get('path') or data.get('link_address')
    return url
def get_data_from_alias(data,alias):
    params = get_alias_params(alias)
    alias_ls = params.get('alias')
    for key in alias_ls:
        value = data.get(key)
        if value:
            return value
