from ...imports import *
def clean_var(var):
    var = str(var)
    return eatAll(var,['/',',','"',"'",'#','\t','\n'])
def capitalize_util(string):
    if not string:
        return string
    cap = string[0].upper()
    if len(string)>1:
        ital = string[1:].upper()
        cap = f"{cap}{ital}"
    return cap
def capitalize(string,replace_all=True):
    strings = string.replace('_',' ').replace('-',' ').replace(',',' ').split(' ')
    strings = [capitalize_util(string) for string in strings]
    strings = ''.join(strings)
    return strings
def clean_keyword(string,cleanIt=True,capitalizeIt=True,replace_all=True):
    if cleanIt:
        string = clean_var(string)
    if capitalizeIt:
        string = capitalize(string,replace_all=replace_all)
    return string
def generate_keywords_list(keywords,cleanIt=True,capitalizeIt=True,replace_all=True,hashtag=False):
    keywords = keywords or []
    if isinstance(keywords,tuple) or isinstance(keywords,set):
        keywords = list(keywords)
    if isinstance(keywords,str):
        keywords = keywords.replace('#',',').split(',')
    if isinstance(keywords,list):
        keywords = [clean_keyword(keyword,cleanIt=cleanIt,capitalizeIt=capitalizeIt,replace_all=replace_all) for keyword in keywords if keyword]
    return keywords
def convert_keywords_list_to_text(keywords,hash_symbol=True,cleanIt=True,capitalizeIt=True,replace_all=True,hashtag=False):
    keywords = generate_keywords_list(keywords,cleanIt=cleanIt,capitalizeIt=capitalizeIt,replace_all=replace_all,hashtag=hashtag)
    if isinstance(hash_symbol,bool):
        if hash_symbol:
            hash_symbol = ' #'
        else:
            hash_symbol = ','
    keywords = hash_symbol+hash_symbol.join(keywords)
    if keywords:
        keywords = eatAll(keywords,[' ',','])
    return keywords
def generate_hashtags(keywords,hash_symbol=True,cleanIt=True,capitalizeIt=True,replace_all=True) -> str:
    keywords = generate_keywords_list(
        keywords=keywords,
        cleanIt=cleanIt,
        capitalizeIt=capitalizeIt,
        replace_all=replace_all
        )

def encode_uri(string):
    if string == None:
        return None
    string = str(string)
    encoded_string = urllib.parse.quote(string)
    return encoded_string
def get_share_params(platform):
    params = SOCIAL_SHARE_PARAMS.get(platform)
    if params:
        return params
    platform_lower = platform.lower()
    first_key = None
    for key,values in SOCIAL_SHARE_PARAMS.items():
        alias = values.get("alias")
        if platform_lower in alias:
            return values
        if first_values == None:
            first_values=values
    return first_values
def get_precise_param(params,input_params):
    alias = params.get('alias')
    input_params_copy = input_params.copy()
    for key,value in input_params_copy.items():
        if key in alias:
            del input_params[key]
            return value,input_params
    return None,input_params
def create_output_text(input_params,hash_symbol):
    text_output = ''
    for key,value in input_params.items():
        if value:
            if key == 'text':
                text_output+=value
            elif key == 'via':
                if text_output:
                    text_output+='\n'
                if not value.startswith('@'):
                    value = f"@{value}"
                text_output+=value
            elif key == 'url':
                if text_output:
                    text_output+='\n'
                text_output+=value
            elif key == 'hashtags':
                if text_output:
                    text_output+='\n'
                value = get_max_hashtags(value,hash_symbol=hash_symbol)
                text_output+=value
    return text_output
def create_output_url(output_params,share_url):
    url = None
    for key,value in output_params.items():
        if value:
            value = encode_uri(value)
            if url == None:
                url = f"{share_url}?{key}={value}"
            else:
               url = f"{url}&{key}={value}"
    return url
def elipse_if_over(string,limit):
    string = str(string)
    if len(string)>limit:
        string = string[:limit-3]
        string = f"{string}..."
    return string
def get_exact_list(obj, items):
    return obj[:items] if len(obj) >= items else obj
def get_max_hashtags(hashtags:list,char_limit=None,hashtag_limit=None,hash_symbol=True):
    all_hashtags_text = convert_keywords_list_to_text(hashtags,hash_symbol=hash_symbol)
    hashtags = all_hashtags_text.split(' ')
    output_text = ''
    hashtag_count = 0
    char_limit = char_limit or len(str(hashtags))+1
    char_available = char_limit
    for hashtag in hashtags:
        hashtag_len = len(hashtag)
        if char_available>=hashtag_len:
            test_text=f"{output_text} {hashtag}"
            test_text = eatAll(test_text,[' '])
            if char_limit>=len(test_text):
                hashtag_count+=1
                output_text = test_text
                char_available = char_limit-len(output_text)
                if hashtag_limit and hashtag_count == hashtag_limit:
                    break
    return output_text
def conform_params_to_char_limits(input_params,characters,hash_symbol):
    max_chars = characters.get("limit")
    chars_available = max_chars
    url_len = 0
    url = input_params.get('url')
    if url:
        url_len = characters.get('url_len') or len(str(url))
    chars_available-= url_len
    via = input_params.get('via')
    if via:
        input_params['via'] = f"@{via}"
        chars_available-=1
    via_len = len(input_params['via'])
    chars_available-= via_len
    hashtags = input_params.get('hashtags')
    keywords_text = get_max_hashtags(hashtags,char_limit=chars_available,hashtag_limit=2)
    if keywords_text:
        chars_available-=1
    keywords_len = len(keywords_text)
    chars_available-= keywords_len
    text = input_params.get('text')
    text = elipse_if_over(text,chars_available)
    if text:
        chars_available-=1
    text_len = len(text)
    input_params['text'] = text
    chars_available-= text_len
    chars_available+=keywords_len
    keywords_text = get_max_hashtags(hashtags,chars_available,hash_symbol=hash_symbol)
    input_params['hashtags'] = keywords_text
    return input_params
def get_output_params(platform,text=None,url=None,via=None,hashtags=None):
    keywords = generate_keywords_list(hashtags)
    
    text = text or ''
    url = url or ''
    input_params = {"text":text,"via":via,"url":url,"hashtags":keywords}
    share_params = get_share_params(platform)
    params = share_params.get('params')
    characters = share_params.get('characters')
    hash_symbol = share_params.get('hash_symbol')
    output_params = {'text':''}
    input_params = conform_params_to_char_limits(input_params,characters,hash_symbol)
    for param,values in params.items():
        value,input_params = get_precise_param(values,input_params)
        output_params[param] = value
    text_output = create_output_text(input_params,hash_symbol)
    if output_params['text'] and text_output:
        output_params['text']+='\n'
    output_params['text']+=text_output
    return output_params
def create_post(platform,text=None,url=None,via=None,hashtags=None,output_params=None):
    output_params = output_params or get_output_params(platform,text=text,url=url,via=via,hashtags=hashtags)
    share_params = get_share_params(platform)
    hash_symbol = share_params.get('hash_symbol')
    output_text = create_output_text(output_params,hash_symbol)
    return output_text
def create_post_url(platform,text=None,url=None,via=None,hashtags=None,output_params=None):
    output_params = output_params or get_output_params(platform,text=text,url=url,via=via,hashtags=hashtags)
    share_params = get_share_params(platform)
    share_url = share_params.get('url')
    output_url = create_output_url(output_params,share_url)
    return output_url

