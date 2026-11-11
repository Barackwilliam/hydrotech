"""
Recognise a video link (YouTube, Facebook, Instagram) and build the address its player is embedded from.
Pure functions, no network: the visitor's browser loads the player only when they press play.
"""
import re
from urllib.parse import parse_qs, quote, urlparse

YOUTUBE = "youtube"
FACEBOOK = "facebook"
INSTAGRAM = "instagram"
FILE = "file"

_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _host(url):
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def platform(url):
    host = _host(url or "")
    if host in ("youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "youtube-nocookie.com"):
        return YOUTUBE
    if host in ("facebook.com", "m.facebook.com", "web.facebook.com", "fb.watch", "fb.com"):
        return FACEBOOK
    if host in ("instagram.com", "instagr.am"):
        return INSTAGRAM
    return ""


def youtube_id(url):
    parsed = urlparse(url)
    host = _host(url)
    parts = [p for p in parsed.path.split("/") if p]
    candidate = ""
    if host == "youtu.be" and parts:
        candidate = parts[0]
    elif parts and parts[0] in ("shorts", "embed", "live", "v") and len(parts) > 1:
        candidate = parts[1]
    else:
        candidate = (parse_qs(parsed.query).get("v") or [""])[0]
    return candidate if _YT_ID.match(candidate) else ""


def instagram_code(url):
    parts = [p for p in urlparse(url).path.split("/") if p]
    for i, part in enumerate(parts[:-1]):
        if part in ("p", "reel", "reels", "tv"):
            return ("reel" if part == "reels" else part), parts[i + 1]
    return "", ""


def is_vertical_link(url):
    """Shorts, Reels and Instagram posts are usually filmed upright."""
    path = urlparse(url or "").path.lower()
    kind = platform(url)
    return (kind == YOUTUBE and "/shorts/" in path) or (kind == FACEBOOK and "/reel" in path) or kind == INSTAGRAM


def is_short_share_link(url):
    """facebook.com/share/... links redirect after a log-in check; the embedded player cannot follow them."""
    return platform(url) == FACEBOOK and urlparse(url).path.startswith("/share/")


def embed_url(url):
    kind = platform(url)
    if kind == YOUTUBE:
        vid = youtube_id(url)
        return f"https://www.youtube-nocookie.com/embed/{vid}?autoplay=1&rel=0&modestbranding=1&playsinline=1" if vid else ""
    if kind == FACEBOOK:
        return ("https://www.facebook.com/plugins/video.php?show_text=false&autoplay=true&allowfullscreen=true&href="
                + quote(url, safe=""))
    if kind == INSTAGRAM:
        kind_part, code = instagram_code(url)
        return f"https://www.instagram.com/{kind_part}/{code}/embed/" if code else ""
    return ""


def thumbnail_url(url):
    """Only YouTube gives a picture without asking its servers first."""
    if platform(url) == YOUTUBE:
        vid = youtube_id(url)
        return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else ""
    return ""
