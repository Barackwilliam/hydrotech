"""Shrink large uploads (phone photos are often 4-8 MB) before they go to the bucket."""
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_SIDE = 1600
QUALITY = 82


def shrink(field):
    """Re-encode a newly uploaded image as a JPEG no wider/taller than MAX_SIDE. Leaves saved files alone."""
    if not field or getattr(field, "_committed", True):
        return
    try:
        field.file.seek(0)
        img = Image.open(field.file)
        img = ImageOps.exif_transpose(img)  # phone photos store rotation in EXIF
    except Exception:
        return  # not an image Pillow can read; the form validation already handles that
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    out = BytesIO()
    img.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    name = Path(field.name).stem + ".jpg"
    field.save(name, ContentFile(out.getvalue()), save=False)
