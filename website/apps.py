import logging
import os
import sys
import threading

from django.apps import AppConfig

log = logging.getLogger(__name__)
LOCK_KEY = 7_316_442  # any fixed number; names the Postgres lock below


def _is_web_server():
    prog = os.path.basename(sys.argv[0] if sys.argv else "")
    if "gunicorn" in prog:
        return True
    return len(sys.argv) > 1 and sys.argv[1] == "runserver" and os.environ.get("RUN_MAIN") == "true"


def _left_without_badge(lines):
    from . import watermark
    from .models import CompanyInfo, Project, Service, TeamMember, Video
    sig = watermark.signature(lines)
    return sum(m.objects.exclude(wm_sig=sig).exclude(**{m.watermark_fields[0]: ""}).count()
               for m in (CompanyInfo, Service, Project, TeamMember, Video))


def _stamp_missing():
    """Background: badge every picture/video that lacks the current one. One server at a time."""
    from django.db import close_old_connections, connection

    from .management.commands.apply_watermarks import run

    got_lock = True
    try:
        if connection.vendor == "postgresql":
            with connection.cursor() as cur:
                cur.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_KEY])
                got_lock = cur.fetchone()[0]
        if not got_lock:
            print("Watermark on start: another server is doing it", flush=True)
            return
        print("Watermark on start: checking every picture…", flush=True)
        pictures, videos, posters, lines = run(out=lambda msg: print(msg, flush=True))
        left = _left_without_badge(lines)
        print(f"Watermark on start: {pictures} pictures, {videos} videos, {posters} YouTube covers stamped; "
              f"{left} still without the current badge.", flush=True)
    except Exception:
        log.exception("Watermark on start failed")
        print("Watermark on start: FAILED, see the error above", flush=True)  # the site keeps running; build.sh tries again next deploy
    finally:
        if got_lock and connection.vendor == "postgresql":
            try:
                with connection.cursor() as cur:
                    cur.execute("SELECT pg_advisory_unlock(%s)", [LOCK_KEY])
            except Exception:
                pass
        close_old_connections()


class WebsiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "website"
    verbose_name = "Website"

    def ready(self):
        from django.conf import settings

        if settings.WATERMARK_ON_START and _is_web_server():
            print(f"Watermark on start: will check pictures in 8 s (pid {os.getpid()})", flush=True)
            # a few seconds after start, so the first visitors are served first
            threading.Timer(8, _stamp_missing).start()
