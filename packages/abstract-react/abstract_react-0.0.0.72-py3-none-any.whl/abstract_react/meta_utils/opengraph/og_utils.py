def build_og(meta):
    og = meta.get("og", {})
    title = og.get("title", meta.get("title"))
    desc = og.get("description", meta.get("description"))

    return {
        "og:title": title,
        "og:description": desc,
        "og:url": og.get("url", meta.get("canonical")),
        "og:image": og.get("image", meta.get("thumbnail_url_resized")),
        "og:image:alt": og.get("image_alt", title),
        "og:image:width": "1200",
        "og:image:height": "627",
        "og:image:type": "image/jpeg",
        "og:type": og.get("type", "article"),
        "og:site_name": og.get("site_name", "The Daily Dialectics"),
        "og:locale": "en_US",
    }
