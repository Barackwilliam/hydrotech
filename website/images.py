"""Shrink large uploads (phone photos are often 4-8 MB) before they go to the bucket."""
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_SIDE = 1600
QUALITY = 82


def shrunk_bytes(fileobj):
    """JPEG bytes of the picture, no wider/taller than MAX_SIDE, or None when Pillow cannot read it."""
    try:
        fileobj.seek(0)
        img = ImageOps.exif_transpose(Image.open(fileobj))  # phone photos store rotation in EXIF
    except Exception:
        return None  # not a picture; the form validation already handles that
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    out = BytesIO()
    img.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return out.getvalue()


def shrink(field):
    """Re-encode a newly uploaded image as a JPEG no wider/taller than MAX_SIDE. Leaves saved files alone."""
    if not field or getattr(field, "_committed", True):
        return
    data = shrunk_bytes(field.file)
    if data is not None:
        from .watermark import fresh_name
        field.save(fresh_name(field.name), ContentFile(data), save=False)
