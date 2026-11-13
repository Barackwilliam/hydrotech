"""Burn the company badge into uploaded videos, away from the web request (it can take minutes)."""
import logging
import os
import tempfile
import threading
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import close_old_connections
from django.utils.text import slugify

from . import watermark

log = logging.getLogger(__name__)


def start(pk):
    if getattr(settings, "VIDEO_WATERMARK_SYNC", False):
        process(pk)
        return
    threading.Thread(target=_run, args=(pk,), daemon=True, name=f"video-watermark-{pk}").start()


def _run(pk):
    try:
        process(pk)
    finally:
        close_old_connections()


def _frame(src, out_path):
    """JPEG bytes of a frame about a third into the video (the first frames are often dark), or None."""
    import subprocess
    try:
        reader = __import__("imageio_ffmpeg").read_frames(src)
        meta = next(reader)
        reader.close()
        at = max(0.5, min(4.0, (meta.get("duration") or 3) / 3))
        subprocess.run([watermark.ffmpeg_exe(), "-y", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", src,
                        "-frames:v", "1", "-q:v", "3", out_path], check=True, capture_output=True, timeout=120)
        with open(out_path, "rb") as fh:
            return fh.read()
    except Exception:
        log.exception("Could not take a cover picture from %s", src)
        return None


def process(pk, lines=None):
    """Stamp one video from its untouched copy. Returns True when done."""
    from .models import Video

    video = Video.objects.filter(pk=pk).first()
    if video is None:
        return False
    if not video.file_original and video.file:
        # uploaded before watermarks existed: the current file is the untouched one
        video.file_original.save(Path(video.file.name).name, video.file.file, save=False)
        Video.objects.filter(pk=pk).update(file_original=video.file_original.name)
    if not video.file_original:
        return False
    lines = lines or watermark.texts()
    storage = video.file_original.storage
    Video.objects.filter(pk=pk).update(wm_status="pending")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = os.path.join(tmp, "in"), os.path.join(tmp, "out.mp4")
            with storage.open(video.file_original.name, "rb") as fh, open(src, "wb") as out:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    out.write(chunk)
            watermark.stamp_video(src, dst, lines)
            width, height = watermark._video_size(src)
            cover = None if video.poster else _frame(src, os.path.join(tmp, "cover.jpg"))
            with open(dst, "rb") as fh:
                new_name = storage.save("videos/" + watermark.fresh_name(slugify(video.title_sw)[:40] or "video", "mp4"), File(fh))
        old = video.file.name if video.file else ""
        changes = {"file": new_name, "wm_status": "done", "video_sig": watermark.signature(lines)}
        if video.orientation == "auto":  # filmed upright (phones, Reels) or lying down
            changes["orientation"] = "portrait" if height > width else "landscape"
        Video.objects.filter(pk=pk).update(**changes)
        if old and old != new_name:
            storage.delete(old)
        if cover:
            # a cover picture from inside the video; saved through the model, so it gets the badge too
            fresh = Video.objects.get(pk=pk)
            fresh.poster = ContentFile(cover, name=f"{slugify(video.title_sw)[:40] or 'video'}.jpg")
            fresh.save()
        return True
    except Exception:
        log.exception("Could not put the watermark on video %s", pk)
        Video.objects.filter(pk=pk).update(wm_status="failed")
        return False
