from ...imports import *
from ...images.image_utils import *
from abstract_utilities.type_utils import *
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
            need_len = [min_len_min - string_len,min_len_max - string_len]
            for title_variant in title_variants:
                add_variant=''
                
                if string:
                    add_variant += ' | '
                add_variant += f"{title_variant}"
                if add_variant not in string and title_variant not in string:
                    add_variant_len = len(add_variant)
                    if add_variant_len <= need_len[-1]:
                        string+= add_variant
                        need_len = [need_len[0] - add_variant_len,need_len[1] - add_variant_len]
                    
            
        else:
            string = truncate_text(string,max_len_max)#[string_len - max_len_min,string_len - max_len_max]
    return string
def pad_or_trim(typ, string, platform=None,domain=None,title_variants=None):
    if not isinstance(string, str):
        return ""
    string = string.strip()
    limits = META_VARS.get(typ, {"max": [0, float('inf')]})
    return truncate_or_add(string=string,size_range=limits,title_variants=title_variants)

def title_add(current_string="", size_range=None,domain=None,title_variants=None):
    if not size_range or (not domain and not title_potentials and not current_string) or not isinstance(current_string, str):
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


def validate_image(image_url):
    try:
        response = requests.get(image_url)
        if response.status_code != 200 or len(response.content) > 5 * 1024 * 1024:
            return False
        img = Image.open(BytesIO(response.content))
        fmt = img.format.lower()
        if fmt not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            return False
        return img
    except Exception:
        return False

def resize_image(img, target_width=1200, target_height=627):
    width, height = img.size
    target_ratio = target_width / target_height
    current_ratio = width / height
    
    if width != target_width or height != target_height:
        if current_ratio > target_ratio:
            new_height = target_height
            new_width = int(new_height * current_ratio)
        else:
            new_width = target_width
            new_height = int(new_width / current_ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        img = img.crop((left, top, left + target_width, top + target_height))
    return img

def generate_meta_tags_ultra(meta,**kwargs):
    """
    Universal, future-proof, fully recursive meta tag generator.
    Converts ALL metadata (including nested OG/Twitter/article/feeds/geo/apps/languages)
    into correct <meta>, <link>, <title>, <script type="application/ld+json"> blocks.
    """

    tags = []

    def add(line):
        if line and line not in tags:
            tags.append(line)

    # -------------------------------------------------------------------------
    # 1. Title
    # -------------------------------------------------------------------------
    if meta.get("title"):
        add(f"<title>{meta['title']}</title>")

    # -------------------------------------------------------------------------
    # 2. Canonical
    # -------------------------------------------------------------------------
    canonical = meta.get("canonical")
    if canonical:
        add(f'<link rel="canonical" href="{canonical}" />')

    # -------------------------------------------------------------------------
    # 3. Recursive writer for <meta> and <link> tags
    # -------------------------------------------------------------------------
    def write_meta(prefix, obj):
        """
        Recursively write:
          - <meta name="x:x2:x3" content="...">
          - <meta property="og:image:width" content="1200">
        """
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = f"{prefix}:{k}" if prefix else k
                write_meta(key, v)

        elif isinstance(obj, list):
            # Lists (like article:tag)
            for item in obj:
                write_meta(prefix, item)

        else:
            # Base value: decide attribute type
            # OG uses "property", Twitter uses "name", other = "name"
            if prefix.startswith("og:"):
                add(f'<meta property="{prefix}" content="{obj}" />')
            else:
                add(f'<meta name="{prefix}" content="{obj}" />')

    # -------------------------------------------------------------------------
    # 4. Write top-level meta keys
    # -------------------------------------------------------------------------
    SIMPLE_META_KEYS = [
        "description",
        "description_html",
        "keywords",
        "viewport",
        "referrer",
        "theme_color",
        "color_scheme",
        "robots",
    ]

    for key in SIMPLE_META_KEYS:
        if meta.get(key):
            add(f'<meta name="{key}" content="{meta[key]}" />')

    # -------------------------------------------------------------------------
    # 5. OpenGraph (FULL)
    # -------------------------------------------------------------------------
    if "og" in meta:
        write_meta("og", meta["og"])

    # -------------------------------------------------------------------------
    # 6. Twitter (FULL)
    # -------------------------------------------------------------------------
    if "twitter" in meta:
        write_meta("twitter", meta["twitter"])

    # -------------------------------------------------------------------------
    # 7. Other metadata (FULL)
    # -------------------------------------------------------------------------
    if "other" in meta:
        other = meta["other"]

        # charset
        if other.get("charset"):
            add(f'<meta charset="{other["charset"]}" />')

        # http-equiv
        if other.get("content_type"):
            add(f'<meta http-equiv="content-type" content="{other["content_type"]}" />')

        # manifest
        if other.get("manifest"):
            add(f'<link rel="manifest" href="{other["manifest"]}" />')

        # any remaining “other” fields → meta name="other:key"
        for k, v in other.items():
            if k in ["charset", "content_type", "manifest", "alternate", "geo", "hreflang"]:
                continue
            add(f'<meta name="{k}" content="{v}" />')

        # alternate feed
        if other.get("alternate"):
            alt = other["alternate"]
            add(f'<link rel="{alt["rel"]}" type="{alt["type"]}" href="{alt["href"]}" />')

        # geo metadata
        if other.get("geo"):
            geo = other["geo"]
            for k, v in geo.items():
                add(f'<meta name="geo.{k}" content="{v}" />')

        # hreflang list
        if other.get("hreflang"):
            for h in other["hreflang"]:
                add(f'<link rel="alternate" hreflang="{h["lang"]}" href="{h["href"]}" />')

    # -------------------------------------------------------------------------
    # 8. Favicon
    # -------------------------------------------------------------------------
    favicon = (
        meta.get("thumbnail_url_resized")
        or meta.get("thumbnail_resized")
        or meta.get("thumbnail_link")
        or "/imgs/favicon.ico"
    )
    add(f'<link rel="icon" href="{favicon}" />')

    # -------------------------------------------------------------------------
    # 9. JSON-LD Schema (AUTO-GENERATED)
    # -------------------------------------------------------------------------
    # You can expand this to article/video/product/etc.
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta.get("title"),
        "image": meta.get("thumbnail_url_resized") or meta.get("thumbnail_link"),
        "datePublished": meta.get("og", {}).get("article", {}).get("published_time"),
        "dateModified": meta.get("og", {}).get("article", {}).get("modified_time"),
        "author": meta.get("other", {}).get("author"),
        "description": meta.get("description"),
        "mainEntityOfPage": canonical,
    }
    add(f'<script type="application/ld+json">{json.dumps(schema)}</script>')

    return "\n".join(tags)
# Function to generate meta tags
def generate_meta_tags(meta, base_url=None, json_path=None):
    base_url = base_url or meta.get('variants')[0]
    tags = []
    json_path=json_path or ""
    json_path = json_path.split('json_pages/')[-1]
    # Base Tags
    tags.append(f'<title>{meta.get("title")}</title>')
    tags.append(f'<meta name="description" content="{meta.get("description_html") or meta.get("description") or "Explore content from The Daily Dialectics."}" />')
    tags.append(f'<meta name="keywords" content="{meta.get("keywords", "")}" />')

    # Favicon
    favicon = (
        meta.get("thumbnail_resized_link") or
        (meta.get("og", {}).get("image") if meta.get("og") else None) or
        meta.get("thumbnail_link") or
        meta.get("thumbnail_resized") or
        meta.get("thumbnail") or
        "/imgs/favicon.ico"
    )
    tags.append(f'<link rel="icon" href="{favicon}" type="image/x-icon" />')

    # Universal Crawler Tags
    other = meta.get("other", {})
    tags.append(f'<meta name="robots" content="{other.get("robots", "index, follow")}" />')
    tags.append(f'<meta name="googlebot" content="{other.get("googlebot", "index, follow")}" />')
    tags.append(f'<meta name="bingbot" content="{other.get("bingbot", "noarchive")}" />')
    tags.append(f'<meta name="yahooContent" content="{other.get("yahooContent", "article")}" />')
    tags.append(f'<meta name="author" content="{other.get("author", "The Daily Dialectics Team")}" />')
    tags.append(f'<meta name="revisit-after" content="{other.get("revisit-after", "7 days")}" />')
    tags.append(f'<meta name="rating" content="{other.get("rating", "General")}" />')
    tags.append(f'<meta name="distribution" content="{other.get("distribution", "global")}" />')
    if other.get("msvalidate.01"):
        tags.append(f'<meta name="msvalidate.01" content="{other["msvalidate.01"]}" />')
    if other.get("yandex-verification"):
        tags.append(f'<meta name="yandex-verification" content="{other["yandex-verification"]}" />')

    # Open Graph (Facebook, etc.)
    og = meta.get("og", {})
    tags.append(f'<meta property="og:title" content="{og.get("title", meta.get("title"))}" />')
    tags.append(f'<meta property="og:description" content="{og.get("description", meta.get("description"))}" />')
    tags.append(f'<meta property="og:url" content="{og.get("url", meta.get("canonical", f"{base_url}{json_path}"))}" />')
    tags.append(f'<meta property="og:image" content="{meta.get("thumbnail_resized_link") or og.get("image") or meta.get("thumbnail_link") or meta.get("thumbnail_resized") or meta.get("thumbnail")}" />')
    if og.get("image_alt"):
        tags.append(f'<meta property="og:image:alt" content="{og["image_alt"]}" />')
    tags.append(f'<meta property="og:image:width" content="{og.get("image_width", "1200")}" />')
    tags.append(f'<meta property="og:image:height" content="{og.get("image_height", "627")}" />')
    tags.append(f'<meta property="og:image:type" content="{og.get("image_type", "image/jpeg")}" />')
    tags.append(f'<meta property="og:type" content="{og.get("type", "article")}" />')
    tags.append(f'<meta property="og:site_name" content="{og.get("site_name")}" />')
    tags.append(f'<meta property="og:locale" content="{og.get("locale", "en_US")}" />')
    if og.get("fb_app_id"):
        tags.append(f'<meta property="fb:app_id" content="{og["fb_app_id"]}" />')
    if og.get("updated_time"):
        tags.append(f'<meta property="og:updated_time" content="{og["updated_time"]}" />')
    if og.get("article"):
        article = og["article"]
        if article.get("published_time"):
            tags.append(f'<meta property="article:published_time" content="{article["published_time"]}" />')
        if article.get("modified_time"):
            tags.append(f'<meta property="article:modified_time" content="{article["modified_time"]}" />')
        if article.get("section"):
            tags.append(f'<meta property="article:section" content="{article["section"]}" />')
        if article.get("tag"):
            for tag in article["tag"]:
                tags.append(f'<meta property="article:tag" content="{tag}" />')

    # Twitter Cards
    twitter = meta.get("twitter", {})
    tags.append(f'<meta name="twitter:card" content="{twitter.get("card", "summary_large_image")}" />')
    tags.append(f'<meta name="twitter:title" content="{twitter.get("title", meta.get("title"))}" />')
    tags.append(f'<meta name="twitter:description" content="{twitter.get("description", meta.get("description"))}" />')
    tags.append(f'<meta name="twitter:image" content="{twitter.get("image", meta.get("thumbnail"))}" />')
    if twitter.get("image_alt"):
        tags.append(f'<meta name="twitter:image:alt" content="{twitter["image_alt"]}" />')
    tags.append(f'<meta name="twitter:image:type" content="{twitter.get("image_type", "image/jpeg")}" />')
    tags.append(f'<meta name="twitter:site" content="{twitter.get("site", "@thedailydialectics")}" />')
    if twitter.get("site:id"):
        tags.append(f'<meta name="twitter:site:id" content="{twitter["site:id"]}" />')
    tags.append(f'<meta name="twitter:creator" content="{twitter.get("creator", "@thedailydialectics")}" />')
    if twitter.get("creator:id"):
        tags.append(f'<meta name="twitter:creator:id" content="{twitter["creator:id"]}" />')
    tags.append(f'<meta name="twitter:domain" content="{twitter.get("domain", "thedailydialectics.com")}" />')

    # Other
    tags.append(f'<meta name="viewport" content="{other.get("viewport", "width=device-width, initial-scale=1")}" />')
    tags.append(f'<meta name="application-name" content="{other.get("application-name")}" />')
    tags.append(f'<meta name="theme-color" content="{other.get("theme_color", "#FFFFFF")}" />')
    tags.append(f'<meta name="color-scheme" content="{other.get("color_scheme", "light")}" />')
    if other.get("charset"):
        tags.append(f'<meta charset="{other["charset"]}" />')
    if other.get("content_type"):
        tags.append(f'<meta http-equiv="content-type" content="{other["content_type"]}" />')
    if other.get("manifest"):
        tags.append(f'<link rel="manifest" href="{other["manifest"]}" />')
    tags.append(f'<link rel="canonical" href="{meta.get("canonical", f"{base_url}{json_path}")}" />')

    # Join and return
    return '\n'.join(tags)

def get_meta_info(info=None,app=False,player_url=False,feed_url=False,geo=False,languages=False,**kwargs):
    info = info
    title_variants = info.get("title_variants")
    path=info.get('path')
    domain = info.get("domain")
    full_url = info.get('variants')[0]
    share_url = info.get("share_url",full_url)
    canonical = full_url
    domain_name = info.get('name')
    tokenized_domain = info.get('tokenized_domain')
    app_name = info.get('app_name')
    author = info.get('author')
    i_url = info.get('i_url')
    title = info.get('title')
    description = info.get('description')
    href = info.get('href', '')
    keywords_str = info.get("keywords_str")
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
        get_resized_image_file_path(
            thumbnail,
            target_width=1200,
            target_height=627,
            save_resize=True,
            check_resize=True,
        )
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

    metadata = {
        "title": pad_or_trim("title", title,title_variants=title_variants),
        "description_html": pad_or_trim("description", description,title_variants=title_variants),
        "description": pad_or_trim("description", description,title_variants=title_variants),
        "keywords": pad_or_trim("keywords", keywords_str,title_variants=title_variants),
        "thumbnail": thumbnail,
        "thumbnail_link": thumbnail_link,
        "thumbnail_resized": thumbnail_resized,
        "thumbnail_url_resized": thumbnail_url_resized,
        "canonical": share_url,
        "mobile_url": mobile_url,
        "oembed_url": oembed_url,
        "og": {
            "type": "article.other",
            "title": pad_or_trim("title", title, "og",title_variants=title_variants),
            "description": pad_or_trim("description", description, "og",title_variants=title_variants),
            "url": share_url,
            "image": thumbnail_url_resized or thumbnail_link,  # Prioritize resized
            "image_alt": pad_or_trim("alt", thumbnail_alt, "og",title_variants=title_variants),
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
            "title": pad_or_trim("title", title, "twitter",title_variants=title_variants),
            "description": pad_or_trim("description", description, "twitter",title_variants=title_variants),
            "site": author,
            "site:id": info.get("twitter_site_id", "123456789"),  # Replace with actual ID
            "creator": author,
            "creator:id": info.get("twitter_creator_id", "123456789"),  # Replace with actual ID
            "image": thumbnail_url_resized or thumbnail_link,  # Prioritize resized
            "image_alt": pad_or_trim("alt", thumbnail_alt, "twitter",title_variants=title_variants),
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
def get_pared_url_info(info):
    domain = info.get("domain", "")
    url_mgr = urlManager(domain)
    info.update(url_mgr.parsed)
    description = info.get('description', '')
    info["description"] = pad_or_trim('description',string=description,title_variants=info["title_variants"])

    return info
def is_string_in_range(string, size_range):
    """Check if string length is within the given range."""
    if not isinstance(string, str):
        return False
    str_length = len(string.strip())
    return size_range[0] <= str_length <= size_range[1]



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
        data['title'] = pad_to_max('title', data['title'],domain=data['domain'],title_variants=data.get('title_variants'))
    
    # Process description
    if 'description' in data:
        data['description'] = pad_to_max('description', data['description'],domain=data['domain'])
    
    # Add other fields as needed
    return data

