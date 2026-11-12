"""
The company badge (logo, name, website and phone) stamped at the top centre of every photo and video.

Pictures are stamped when saved (website/models.py). The untouched upload is kept under originals/ with a
random name, so the badge can be redrawn from it when the text changes (manage.py apply_watermarks).
Videos are re-encoded with ffmpeg in the background, because that takes longer than a web request.
"""
import hashlib
import logging
import os
import subprocess
import tempfile
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

log = logging.getLogger(__name__)

ASSETS = Path(__file__).resolve().parent / "watermark_assets"
VERSION = "4"  # 4: three centred lines, no logo (3: fresh file names)


def fresh_name(name, ext="jpg"):
    """A file name never used before: the readable part of `name` plus a random tag.

    Pictures are cached for a year by browsers and the storage CDN, so a stamped picture must never be
    saved under a name an older (unstamped) picture once had: the old one would keep being shown."""
    import re
    import uuid

    stem = Path(name or "picha").stem
    # drop tags added earlier: ours (-1a2b3c4d) and Django's (_AbC12xY); real words are kept
    stem = re.sub(r"(-[0-9a-f]{8}|_[A-Za-z0-9]{7})+$", "", stem) or "picha"
    return f"{stem[:50]}-{uuid.uuid4().hex[:8]}.{ext}"


def local_phone(number):
    """+255 714 425 262 -> 0714 425 262, the way people in Tanzania write it."""
    digits = "".join(ch for ch in number or "" if ch.isdigit())
    if digits.startswith("255") and len(digits) == 12:
        digits = "0" + digits[3:]
    if len(digits) == 10:
        return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
    return (number or "").strip()


def texts():
    """(name, website, phone) from the company details in the admin."""
    from .models import CompanyInfo
    c = CompanyInfo.load()
    return c.name or "Milan Hydrotech", (c.website_domain or "").strip(), local_phone(c.phone_1)


def signature(lines=None):
    """Changes whenever the badge would look different; stored on each row to skip work already done."""
    raw = "|".join((VERSION,) + tuple(lines or texts()))
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


@lru_cache(maxsize=None)
def _font(weight, size):
    return ImageFont.truetype(str(ASSETS / f"PlusJakartaSans-{weight}.ttf"), max(8, int(size)))


@lru_cache(maxsize=None)
def _asset(name):
    return Image.open(ASSETS / name).convert("RGBA")


def _icon(name, size):
    return _asset(name).resize((max(1, int(size)), max(1, int(size))), Image.LANCZOS)


def _spaced_width(font, text, spacing):
    return sum(font.getlength(ch) for ch in text) + spacing * max(0, len(text) - 1)


def _draw_spaced(draw, x, y, text, font, spacing, **style):
    for ch in text:
        draw.text((x, y), ch, font=font, anchor="lm", **style)
        x += font.getlength(ch) + spacing
    return x


def badge_layer(size, lines=None):
    """A transparent layer the size of the picture with the badge at the top centre, three centred lines:
    MILAN HYDROTECH, then the website, then the phone. Big black capitals, no panel behind them; a thin
    white edge round every letter keeps them readable on dark parts of the photo."""
    name, website, phone = lines or texts()
    # (text, weight, size, letter spacing, line height), in hundredths of the picture's shorter side:
    # the sizes of the preview the client approved (B)
    rows = [(name.upper(), 800, 6.4, .35, 7.6), (website.upper(), 800, 3.6, .25, 4.8), (phone, 800, 4.0, .30, 5.4)]
    rows = [r for r in rows if r[0]]
    w, h = size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if min(w, h) < 120 or not rows:  # thumbnails too small to carry readable text
        return layer

    u = min(w, h) / 100
    for _ in range(4):  # shrink until the widest line fits across the picture
        fonts = [_font(weight, k * u) for _, weight, k, _, _ in rows]
        spacing = [sp * u for _, _, _, sp, _ in rows]
        ph = _icon("phone.png", 3.8 * u) if phone else None
        widths = []
        for (text, *_), f, sp in zip(rows, fonts, spacing):
            extra = ph.width + 1.2 * u if (ph and text == phone) else 0
            widths.append(extra + _spaced_width(f, text, sp))
        if max(widths) <= w * 0.92:
            break
        u *= w * 0.92 / max(widths)
    heights = [lh * u for *_, lh in rows]

    d = ImageDraw.Draw(layer)
    edge = dict(stroke_width=max(1, int(.45 * u)), stroke_fill=(255, 255, 255, 235))
    ink = dict(fill=(10, 10, 10, 255), **edge)
    y = 3 * min(w, h) / 100
    for (text, *_), f, sp, width, lh in zip(rows, fonts, spacing, widths, heights):
        x, cy = (w - width) / 2, y + lh / 2
        if ph and text == phone:
            halo = Image.new("RGBA", ph.size, (255, 255, 255, 235))
            halo.putalpha(ph.split()[3].filter(ImageFilter.MaxFilter(5)))
            layer.alpha_composite(halo, (int(x), int(cy - ph.height / 2)))
            layer.alpha_composite(ph, (int(x), int(cy - ph.height / 2)))
            x += ph.width + 1.2 * u
        _draw_spaced(d, x, cy, text, f, sp, **ink)
        y += lh
    return layer


def stamp_image(data, lines=None):
    """JPEG bytes of the picture with the badge on it."""
    img = ImageOps.exif_transpose(Image.open(BytesIO(data))).convert("RGBA")
    out = Image.alpha_composite(img, badge_layer(img.size, lines)).convert("RGB")
    buf = BytesIO()
    out.save(buf, "JPEG", quality=86, optimize=True, progressive=True)
    return buf.getvalue()


# ---------- video ----------

VIDEO_MAX_SIDE = 1280


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _video_size(path):
    import imageio_ffmpeg
    reader = imageio_ffmpeg.read_frames(str(path))
    meta = next(reader)
    reader.close()
    return meta["size"]


def stamp_video(src_path, dst_path, lines=None):
    """Re-encode the video (at most 1280 px) with the badge burnt in. Raises on failure."""
    w, h = _video_size(src_path)
    k = min(1.0, VIDEO_MAX_SIDE / max(w, h))
    w, h = int(w * k) // 2 * 2, int(h * k) // 2 * 2
    with tempfile.TemporaryDirectory() as tmp:
        badge = os.path.join(tmp, "badge.png")
        badge_layer((w, h), lines).save(badge)
        cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(src_path), "-i", badge,
               "-filter_complex", f"[0:v]scale={w}:{h}[v];[v][1:v]overlay=0:0",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst_path)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60 * 20)
