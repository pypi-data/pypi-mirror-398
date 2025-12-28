from ..titles.titles import pad_or_trim
from ..titles.title_variants import title_variants_from_domain
from ..generators.metadata_builder import generate_metadata

### Imports from user-provided files
##from .social_media import create_post, create_post_url  # :contentReference[oaicite:4]{index=4}
##from .social_media_utils import get_output_params       # :contentReference[oaicite:5]{index=5}
##from .twitter import prepare_tweet                      # :contentReference[oaicite:6]{index=6}
##from .metadata import generate_meta_tags                # :contentReference[oaicite:7]{index=7}


def social_share(platform, *, text, url, via=None, hashtags=None):
    """
    Create a platform-optimized text-only social share post.
    Example:
        social_share("x", text="My post!", url="https://mysite.com/123")
    """
    output = create_post(
        platform,
        text=text,
        url=url,
        via=via,
        hashtags=hashtags
    )
    return output


def social_share_url(platform, *, text, url, via=None, hashtags=None):
    """
    Create a share link:
        https://twitter.com/intent/tweet?text=...
    """
    share_url = create_post_url(
        platform,
        text=text,
        url=url,
        via=via,
        hashtags=hashtags
    )
    return share_url


def generate_full_social_package(info):
    """
    Produces:
      - SEO metadata
      - OpenGraph tags
      - Twitter card
      - Thread/FB/X/Email share links
      - Hashtags
      - Clean padded titles/descriptions

    This is the FINAL unified API.
    """
    # STEP 1 → SEO metadata
    meta = generate_metadata(info)

    url = meta.get("canonical")
    title = meta.get("title")
    desc = meta.get("description")
    keywords = meta.get("keywords", "")

    platforms = ["x", "facebook", "threads", "mailto", "minds"]

    share_links = {
        platform: social_share_url(
            platform,
            text=desc,
            url=url,
            via=info.get("via"),
            hashtags=keywords
        )
        for platform in platforms
    }

    share_posts = {
        platform: social_share(
            platform,
            text=desc,
            url=url,
            via=info.get("via"),
            hashtags=keywords
        )
        for platform in platforms
    }

    tweet = prepare_tweet(
        keyWords=keywords,
        pageTitle=title,
        description=desc,
        title=title,
        link_address=url
    )

    return {
        "metadata": meta,
        "open_graph_tags": generate_meta_tags(meta, json_path=info.get("json_path", "")),
        "tweet": tweet,
        "share_links": share_links,
        "share_posts": share_posts,
        "title_variants": title_variants_from_domain(info.get("domain", "")),
    }
