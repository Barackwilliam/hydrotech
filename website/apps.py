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
        if got_lock:
            pictures, videos, posters, _ = run()
            if pictures or videos or posters:
                log.info("Watermark on start: %s pictures, %s videos, %s YouTube covers", pictures, videos, posters)
    except Exception:
        log.exception("Watermark on start failed")  # the site keeps running; build.sh tries again next deploy
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
            # a few seconds after start, so the first visitors are served first
            threading.Timer(8, _stamp_missing).start()
