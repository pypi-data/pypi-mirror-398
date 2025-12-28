INFO_KEYS = ["info","meta","metadata","meta_data","keywords","keywords_str","title",'path',"share_url","domain","thumbnail","thumbnail_link","thumbnail_alt","thumbnail_resized","thumbnail_url_resized",'languages',"description"]
BOOL_KEYS = ["app","player_url","feed_url","geo","languages"]

def get_dir_link(*args,**kargs):
    return args[0]
def is_string_in_range(string, size_range):
    if not isinstance(string, str):
        return False
    return size_range[0] <= len(string.strip()) <= size_range[1]
def get_max_or_limit(obj,limit=None):
    obj_length = len(obj)
    
    if limit:
        if obj_length>=limit:
            obj = obj[:limit]
    return obj
##def truncate_or_add(string,size_range,variants):
##    string_in_range = is_string_in_range(string, size_range)
##    if not string_in_range:
##        
def title_add(current_string="", size_range=None,domain=None,title_variants=None):
    if not size_range or (not domain and not title_variants and not current_string) or not isinstance(current_string, str):
        return current_string
    title_potentials = title_variants or title_variants_from_domain(domain)
    result = current_string.strip()
    str_space = ' | '
    target_min, target_max = size_range[0], size_range[1]
    if is_string_in_range(result, size_range):
        return result
    
    for potential in sorted(title_potentials, key=len, reverse=True):
        addition = f"{str_space}{potential}"
        candidate = result + addition
        if len(candidate) <= target_max:
            result = candidate
            break
    
    while len(result) < target_min and len(result) < target_max:
        for potential in sorted(title_potentials, key=len):
            addition = f"{str_space}{potential}"
            candidate = result + addition
            if len(candidate) <= target_max:
                result = candidate
            else:
                break
    result_spl= result.split('|')
    result_spl= get_max_or_limit(result_spl,limit=3)
    result = '|'.join(result_spl)
    return result
def truncate_or_add(string,size_range,title_variants=None):
    string_len = len(string)
    min_range = size_range.get('min')
    max_range = size_range.get('max')
    min_len_min = min_range[0]
    min_len_max = min_range[1]
    max_len_min = max_range[0]
    max_len_max = max_range[1]
    
    all_range = [min_len_min,max_len_max]
    in_all_range = is_string_in_range(string, all_range)
    if not in_all_range:
        if string_len < min_len_min:
            need_len = min_range#[min_len_min - string_len,min_len_max - string_len]
            string = title_add(current_string=string, size_range=min_range,title_variants=title_variants)
        else:
            string = truncate_text(string,max_len_max)#[string_len - max_len_min,string_len - max_len_max]
    return string
def pad_or_trim(typ, string, platform=None,domain=None,title_variants=None):
    if not isinstance(string, str):
        return ""
    string = string.strip()
    limits = META_VARS.get(typ, {"max": [0, float('inf')]})
    max_range = limits["max"]

    
    
    if platform == "twitter" and typ == "title":
        max_range = [60, 70]
    elif platform == "twitter" and typ == "description":
        max_range = [150, 200]
    elif platform == "og" and typ == "title":
        max_range = [60, 90]
        if len(string) > 100:
            return string[:88].strip()
    elif platform == "og" and typ == "description":
        max_range = [150, 200]
        if len(string) > 300:
            return string[:300].strip()
    
    if len(string) >= max_range[0]:
        return string[:max_range[1]].strip() if len(string) > max_range[1] else string
    padded = title_add(string, max_range,domain=domain,title_variants=title_variants)
    if len(padded) > max_range[1]:
        return padded[:max_range[1]].strip()
    return padded
def get_keywords(info):
    keywords = info.get('keywords', [])
    keywords_str = info.get('keywords_str', '')
    if keywords_str and not keywords:
        keywords = make_list(keywords_str.split(','))
    if keywords and not keywords_str:
        keywords_str = ','.join(keywords)
    if not keywords and not keywords_str:
        keywords = info.get("title_variants")
        keywords_str = ','.join(keywords)
    if len(keywords) < 10:
        keywords = list(set(info.get("title_variants") + make_list(keywords_str)+info.get("title_variants")))
        keywords = [keyword.replace(' ','_') for keyword in keywords if keyword]
        keywords_len = len(keywords)
        if keywords_len >10:
            keywords_len = 10
        keywords = keywords[:keywords_len]
        keywords_str = ','.join(keywords)
    return {"keywords":keywords,"keywords_str":keywords_str}    
def get_title(info):
    title = info.get('title')
    if not title:
        path = info.get('path')
        paths = [pa for pa in path.split('/') if pa]
        title = paths[-1] if len(paths)>0 else ''
        if title == '':
            title = 'Home'
    return title 
def is_string_in_range(string, size_range):
    """Check if string length is within the given range."""
    if not isinstance(string, str):
        return False
    str_length = len(string.strip())
    return size_range[0] <= str_length <= size_range[1]

def get_pared_url_info(info):
    domain = info.get("domain", "")
    url_mgr = urlManager(domain)
    domain = url_mgr.parsed.get('domain')
    parsed_url = url_mgr.parsed
    domain_name = parsed_url.get('name')
    info.update(parsed_url)
    info["title_variants"] = title_variants_from_domain(domain)
    tokenized_domain = tokenize_domain(domain)
    info["tokenized_domain"] = tokenized_domain
    info["app_name"] = ' '.join(tokenized_domain)
    info["author"] = f"@{domain_name.lower()}"
    info["i_url"] = f"{domain_name}://"
    title = get_title(info)
    info["title"] = title
    info["title_variants"].append(title)
    description = info.get('description', '')
    info["description"] = pad_or_trim('description',string=description,title_variants=title_variants)
    keywords_info = get_keywords(info)
    info.update(keywords_info)
    return info

def pad_to_max(typ, string,domain=None,title_variants=None):
    """Pad string to reach or approach the max range."""
    if not isinstance(string, str):
        return ""
    
    string = string.strip()
    limits = META_VARS.get(typ)
    if not limits:
        return string

    max_range = limits["max"]
    
    # If already in or above max range, return as is
    if len(string) >= max_range[0]:
        return string
    
    # Pad to reach max range
    return title_add(string, max_range,domain=domain,title_variants=title_variants)

def process_metadata(data):
    """Process all metadata fields to target max ranges."""
    if not isinstance(data, dict):
        return data

    # Process title
    if 'title' in data:
        data['title'] = pad_or_trim('title', data['title'],domain=data['domain'],title_variants=data.get('title_variants'))
    
    # Process description
    if 'description' in data:
        data['description'] = pad_or_trim('description', data['description'],domain=data['domain'],title_variants=data.get('title_variants'))
    
    # Add other fields as needed
    return data


def process_metadata(data):
    """Process all metadata fields to target max ranges."""
    if not isinstance(data, dict):
        return data

    # Process title
    if 'title' in data:
        data['title'] = pad_or_trim('title', data['title'],domain=data['domain'],title_variants=data.get('title_variants'))
    
    # Process description
    if 'description' in data:
        data['description'] = pad_or_trim('description', data['description'],domain=data['domain'],title_variants=data.get('title_variants'))

    # Add other fields as needed
    return data

def getMetaInfo(info,app=False,player_url=False,feed_url=False,geo=False,languages=False,**kwargs):
    path=info.get('path')
    share_url = info.get("share_url", "")
    domain = info.get("domain", "")
    url_mgr = urlManager(domain)
    domain = url_mgr.parsed.get('domain')
    parsed_url = url_mgr.parsed
    domain_name = parsed_url.get('name')
    tokenized_domain = tokenize_domain(domain)
    app_name = ' '.join(tokenized_domain)
    author = f"@{domain_name.lower()}"
    i_url = f"{domain_name}://"
    info = process_metadata(info)
    title = info.get('title', '')
    description = info.get('description', '')
    href = info.get('href', '')
    keywords_str = info.get("keywords_str", "")
    thumbnail = info.get("thumbnail", "")
    thumbnail_link = info.get("thumbnail_link", get_dir_link(thumbnail))
    thumbnail_alt = info.get("thumbnail_alt", title)
    thumbnail_resized = info.get("thumbnail_resized")
    thumbnail_url_resized = info.get("thumbnail_url_resized")  # Renamed for consistency
    if app:
        info['app'] = info.get('app',{})
    if player_url:
        info['player_url'] = info.get('player_url',{})
    if feed_url:
        info['feed_url'] = info.get('feed_url',{})
    if geo:
        info['geo'] = info.get('geo',{})
    if languages:
        info['languages'] = info.get('languages',{})
    # Resize logic
    if thumbnail and not thumbnail_url_resized:  # Only resize if not already provided
        img = validate_image(thumbnail_link)
        if img:
            if img.size != (1200, 627):
                img = resize_image(img)
                thumbnail_dir = os.path.dirname(thumbnail)
                basename = os.path.basename(thumbnail)
                os.makedirs(thumbnail_dir, exist_ok=True)
                thumbnail_resized = f"{thumbnail_dir}/resized_{basename.rsplit('.', 1)[0]}.jpg"  # Always .jpg
                img.save(thumbnail_resized, "JPEG", quality=85)
                thumbnail_url_resized = get_dir_link(thumbnail_resized)
            else:
                thumbnail_resized = thumbnail
                thumbnail_url_resized = thumbnail_link
        else:
            # Fallback if validation fails
            thumbnail_resized = os.path.join(path,'/public/imgs/default_thumbnail.jpg')
            thumbnail_url_resized = get_dir_link(thumbnail_resized)

    # Update info with resized values
    info['thumbnail_resized'] = thumbnail_resized
    info['thumbnail_url_resized'] = thumbnail_url_resized

    mobile_url = share_url.replace("https://", "https://m.")
    oembed_url = f"{domain}/oembed?url={share_url}"
def get_meta_info(info,app=False,player_url=False,feed_url=False,geo=False,languages=False,**kwargs):
    path=info.get('path')
    share_url = info.get("share_url", "")
    domain = info.get("domain", "")
    url_mgr = urlManager(domain)
    domain = url_mgr.parsed.get('domain')
    parsed_url = url_mgr.parsed
    domain_name = parsed_url.get('name')
    tokenized_domain = tokenize_domain(domain)
    app_name = ' '.join(tokenized_domain)
    author = f"@{domain_name.lower()}"
    i_url = f"{domain_name}://"
    info = process_metadata(info)
    title = info.get('title', '')
    description = info.get('description', '')
    href = info.get('href', '')
    keywords_str = info.get("keywords_str", "")
    thumbnail = info.get("thumbnail", "")
    thumbnail_link = info.get("thumbnail_link", get_dir_link(thumbnail))
    thumbnail_alt = info.get("thumbnail_alt", title)
    thumbnail_resized = info.get("thumbnail_resized")
    thumbnail_url_resized = info.get("thumbnail_url_resized")  # Renamed for consistency
    if app not in [None,False]:
        info['app'] = info.get('app',{})
    if player_url not in [None,False]:
        info['player_url'] = info.get('player_url',{})
    if feed_url not in [None,False]:
        info['feed_url'] = info.get('feed_url',{})
    if geo not in [None,False]:
        info['geo'] = info.get('geo',{})
    if languages not in [None,False]:
        info['languages'] = info.get('languages',{})
    # Resize logic
    if thumbnail and not thumbnail_url_resized:  # Only resize if not already provided
        img = validate_image(thumbnail_link)
        if img:
            if img.size != (1200, 627):
                img = resize_image(img)
                thumbnail_dir = os.path.dirname(thumbnail)
                basename = os.path.basename(thumbnail)
                os.makedirs(thumbnail_dir, exist_ok=True)
                thumbnail_resized = f"{thumbnail_dir}/resized_{basename.rsplit('.', 1)[0]}.jpg"  # Always .jpg
                img.save(thumbnail_resized, "JPEG", quality=85)
                thumbnail_url_resized = get_dir_link(thumbnail_resized)
            else:
                thumbnail_resized = thumbnail
                thumbnail_url_resized = thumbnail_link
        else:
            # Fallback if validation fails
            thumbnail_resized = os.path.join(path,'/public/imgs/default_thumbnail.jpg')
            thumbnail_url_resized = get_dir_link(thumbnail_resized)

    # Update info with resized values
    info['thumbnail_resized'] = thumbnail_resized
    info['thumbnail_url_resized'] = thumbnail_url_resized

    mobile_url = share_url.replace("https://", "https://m.")
    oembed_url = f"{domain}/oembed?url={share_url}"
    input(description)
    metadata = {
        "title": pad_or_trim("title", title,domain=domain),
        "description_html": pad_or_trim("description", description,domain=domain),
        "description": pad_or_trim("description", description,domain=domain),
        "keywords": pad_or_trim("keywords", keywords_str,domain=domain),
        "thumbnail": thumbnail,
        "thumbnail_link": thumbnail_link,
        "thumbnail_resized": thumbnail_resized,
        "thumbnail_url_resized": thumbnail_url_resized,
        "canonical": share_url,
        "mobile_url": mobile_url,
        "oembed_url": oembed_url,
        "og": {
            "type": "article.other",
            "title": pad_or_trim("title", title, "og",domain=domain),
            "description": pad_or_trim("description", description, "og",domain=domain),
            "url": share_url,
            "image": thumbnail_url_resized or thumbnail_link,  # Prioritize resized
            "image_alt": pad_or_trim("alt", thumbnail_alt, "og",domain=domain),
            "image_width": "1200",
            "image_height": "627",
            "image_type": "image/jpeg",
            "locale": "en_US",
            "fb_app_id": "427305388009806",
            "site_name": app_name,
            "updated_time": info.get("updated_time", datetime.utcnow().isoformat() + "Z"),
            "article": {
                "published_time": info.get("published_time", datetime.utcnow().isoformat() + "Z"),
                "modified_time": info.get("modified_time", datetime.utcnow().isoformat() + "Z"),
                "section": info.get("section", "Health"),
                "tag": keywords_str.split(",")
            }
        },
        "twitter": {
            "card": "summary_large_image",
            "title": pad_or_trim("title", title, "twitter",domain=domain),
            "description": pad_or_trim("description", description, "twitter",domain=domain),
            "site": author,
            "site:id": info.get("twitter_site_id", "123456789"),  # Replace with actual ID
            "creator": author,
            "creator:id": info.get("twitter_creator_id", "123456789"),  # Replace with actual ID
            "image": thumbnail_url_resized or thumbnail_link,  # Prioritize resized
            "image_alt": pad_or_trim("alt", thumbnail_alt, "twitter",domain=domain),
            "image_type": "image/jpeg",
            "domain": domain
        },
        "other": {
            "robots": "index, follow" if not info.get("noindex", False) else "noindex, nofollow",
            "googlebot": "index, follow",
            "bingbot": "noarchive",
            "yahooContent": "article",
            "msvalidate.01": info.get("bing_validation_id", ""),
            "yandex-verification": info.get("yandex_validation_id", ""),
            "author": info.get("author", app_name),
            "revisit-after": "7 days",
            "rating": info.get("rating", "General"),
            "application-name": app_name,
            "distribution": "global",
            "content_type": "text/html; charset=utf-8",
            "charset": "UTF-8",
            "viewport": "width=device-width, initial-scale=1, maximum-scale=2, shrink-to-fit=no",
            "referrer": "origin-when-crossorigin",
            "color_scheme": "light",
            "theme_color": "#FFFFFF",
            "manifest": "/data/manifest/"
        }
    }

    if "player_url" in info:
        metadata["twitter"].update({
            "card": "player",
            "player": info["player_url"],
            "player:width": info.get("player_width", "1200"),
            "player:height": info.get("player_height", "627"),
            "player:stream": info.get("player_stream", "")
        })
    
    if "app" in info:
        metadata["twitter"].update({
            "card": "app",
            "app:name:iphone": info["app"].get("iphone_name", app_name),
            "app:id:iphone": info["app"].get("iphone_id", ""),
            "app:url:iphone": info["app"].get("iphone_url", i_url),
            "app:name:ipad": info["app"].get("ipad_name", app_name),
            "app:id:ipad": info["app"].get("ipad_id", ""),
            "app:url:ipad": info["app"].get("ipad_url", i_url),
            "app:name:googleplay": info["app"].get("googleplay_name", app_name),
            "app:id:googleplay": info["app"].get("googleplay_id", ""),
            "app:url:googleplay": info["app"].get("googleplay_url", i_url)
        })

    if info.get("feed_url"):
        metadata["other"]["alternate"] = {
            "rel": "alternate",
            "type": "application/rss+xml",
            "href": info["feed_url"]
        }

    if "geo" in info:
        metadata["other"]["geo"] = {
            "position": info["geo"].get("position", ""),
            "placename": info["geo"].get("placename", "")
        }

    if "languages" in info:  # For multi-language support
        metadata["other"]["hreflang"] = [
            {"href": lang["url"], "lang": lang["code"]} for lang in info["languages"]
        ]
    
    return metadata
def get_kwargs_value(dict_obj=None,keys=None,default = None,**kwargs):
    dict_obj = dict_obj or {}
    keys = keys or []
    for key in keys:
        kwargs_value = kwargs.get(key)
        dict_obj_value = dict_obj.get(key)
        value = dict_obj_value or kwargs_value
        if value or default != None:
            dict_obj[key] = value or default
    return dict_obj
def getInfo(*args,**kwargs):
    info = {}
    for arg in args:
        if isinstance(arg,dict):
            info = arg
    info = get_kwargs_value(dict_obj=info,keys=INFO_KEYS,**kwargs)
    info = get_kwargs_value(dict_obj=info,keys=BOOL_KEYS,default={},**kwargs)    
    return info
