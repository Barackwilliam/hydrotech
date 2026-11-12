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
VERSION = "1"  # bump when the look of the badge changes, so apply_watermarks redraws everything
NAVY = (4, 25, 46)
ORANGE = (255, 181, 71)
LIGHT = (214, 228, 242)


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


def badge_layer(size, lines=None):
    """A transparent layer the size of the picture with the badge drawn at the top centre."""
    name, website, phone = lines or texts()
    w, h = size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if min(w, h) < 120:  # thumbnails too small to carry readable text
        return layer
    line2 = ([("icon", "")] if phone else []) + ([("phone", phone)] if phone else [])
    if website:
        line2.append(("site", ("  ·  " if phone else "") + website))

    u = min(w, h) / 100
    for _ in range(4):  # shrink the badge until it fits across the picture
        f_name, f_small = _font(800, 4.4 * u), _font(700, 3.3 * u)
        logo, ph = _icon("logo.png", 9.6 * u), _icon("phone.png", 3 * u)
        gap, pad = 1.1 * u, 2.2 * u
        line2_w = sum(ph.width + gap if kind == "icon" else f_small.getlength(t) for kind, t in line2)
        bw = int(pad * 2 + logo.width + 2 * u + max(f_name.getlength(name), line2_w))
        if bw <= w * 0.94:
            break
        u *= w * 0.94 / bw
    bh = int(logo.height + pad * 1.6)
    x, y = int((w - bw) / 2), int(3 * min(w, h) / 100)
    radius = int(bh / 2.6)

    shadow = ImageDraw.Draw(layer)
    shadow.rounded_rectangle((x, y + u, x + bw, y + bh + u), radius=radius, fill=(0, 0, 0, 90))
    layer = layer.filter(ImageFilter.GaussianBlur(u * 1.2))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x, y, x + bw, y + bh), radius=radius, fill=NAVY + (178,),
                        outline=(255, 255, 255, 60), width=max(1, int(u * .25)))
    layer.alpha_composite(logo, (int(x + pad), int(y + (bh - logo.height) / 2)))
    tx = x + pad + logo.width + 2 * u
    d.text((tx, y + bh * .30), name, font=f_name, fill=(255, 255, 255, 255), anchor="lm")
    cx, cy = tx, y + bh * .70
    for kind, t in line2:
        if kind == "icon":
            layer.alpha_composite(ph, (int(cx), int(cy - ph.height / 2)))
            cx += ph.width + gap
        else:
            d.text((cx, cy), t, font=f_small, fill=(ORANGE if kind == "phone" else LIGHT) + (255,), anchor="lm")
            cx += f_small.getlength(t)
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
