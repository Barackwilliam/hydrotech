"""Burn the company badge into uploaded videos, away from the web request (it can take minutes)."""
import logging
import os
import tempfile
import threading
from pathlib import Path

from django.conf import settings
from django.core.files import File
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
            with open(dst, "rb") as fh:
                new_name = storage.save(f"videos/{slugify(video.title_sw)[:40] or 'video'}.mp4", File(fh))
        old = video.file.name if video.file else ""
        Video.objects.filter(pk=pk).update(file=new_name, wm_status="done", video_sig=watermark.signature(lines))
        if old and old != new_name:
            storage.delete(old)
        return True
    except Exception:
        log.exception("Could not put the watermark on video %s", pk)
        Video.objects.filter(pk=pk).update(wm_status="failed")
        return False
