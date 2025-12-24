def build_twitter(meta):
    twitter = meta.get("twitter", {})
    return {
        "twitter:card": twitter.get("card", "summary_large_image"),
        "twitter:title": twitter.get("title", meta.get("title")),
        "twitter:description": twitter.get("description", meta.get("description")),
        "twitter:image": twitter.get("image", meta.get("thumbnail_url_resized")),
        "twitter:image:alt": twitter.get("image_alt", meta.get("title")),
        "twitter:site": twitter.get("site", "@thedailydialectics"),
        "twitter:creator": twitter.get("creator", "@thedailydialectics"),
    }
