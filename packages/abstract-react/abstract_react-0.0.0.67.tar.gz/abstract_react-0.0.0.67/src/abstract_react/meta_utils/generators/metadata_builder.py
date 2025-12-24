from ..titles import pad_or_trim
from ..images.image_utils import validate_image, resize_image
from ..opengraph.og_utils import build_og
from ..twitter.twitter_utils import build_twitter
import os
from datetime import datetime

def generate_metadata(info):
    title = info.get("title", "")
    description = info.get("description", "")

    meta = {
        "title": pad_or_trim("title", title),
        "description": pad_or_trim("description", description),
        "canonical": info.get("share_url"),
    }

    thumbnail = info.get("thumbnail")
    thumbnail_link = info.get("thumbnail_link")

    img = validate_image(thumbnail_link) if thumbnail_link else None
    if img and img.size != (1200, 627):
        img = resize_image(img)
        new_path = os.path.splitext(thumbnail)[0] + "_resized.jpg"
        img.save(new_path, "JPEG", quality=85)
        meta["thumbnail_url_resized"] = new_path
    else:
        meta["thumbnail_url_resized"] = thumbnail_link

    meta["og"] = build_og(meta)
    meta["twitter"] = build_twitter(meta)

    return meta
