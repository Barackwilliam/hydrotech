"""
Put the company badge on every picture and uploaded video that does not have the current one yet.

    python manage.py apply_watermarks          # only what is missing or out of date (fast when nothing changed)
    python manage.py apply_watermarks --all    # redraw everything

Runs on every deploy (build.sh) and, in the background, each time the web server starts (website/apps.py),
so pictures get their badge even when the host does not use build.sh. The badge is always drawn on the
untouched copy kept in originals/, never on top of an older badge; pictures uploaded before watermarks
existed become their own original.
"""
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from website import video_jobs, watermark
from website.models import CompanyInfo, Project, Service, TeamMember, Video

MODELS = (CompanyInfo, Service, Project, TeamMember, Video)


def stamp_row(model, pk, lines, sig, redo=False):
    """Stamp the pictures of one row. Locked, so two servers starting together never stamp twice."""
    with transaction.atomic():
        obj = model.objects.select_for_update().filter(pk=pk).first()
        if obj is None or (obj.wm_sig == sig and not redo):
            return 0
        changes, done = {"wm_sig": sig}, 0
        for name in model.watermark_fields:
            image, original = getattr(obj, name), getattr(obj, name + "_original")
            if not image:
                continue
            if original:
                with original.open("rb") as fh:
                    data = fh.read()
            else:  # an older picture without the badge: it becomes its own original
                with image.open("rb") as fh:
                    data = fh.read()
                original.save("x.jpg", ContentFile(data), save=False)
                changes[name + "_original"] = original.name
            old = image.name
            image.save(Path(old).stem.split("_")[0] + ".jpg", ContentFile(watermark.stamp_image(data, lines)), save=False)
            changes[name] = image.name
            if old != image.name:
                image.storage.delete(old)
            done += 1
        model.objects.filter(pk=pk).update(**changes)
        return done


def run(redo=False, out=None):
    company = CompanyInfo.load()
    lines = company._watermark_lines()
    sig = watermark.signature(lines)

    posters = 0
    for video in Video.objects.filter(poster="", file="", file_original="").exclude(url=""):
        if video.fetch_youtube_poster():  # YouTube cover kept as our own picture, so it gets the badge too
            video.save()
            posters += 1

    pictures = 0
    for model in MODELS:
        rows = model.objects.all() if redo else model.objects.exclude(wm_sig=sig)
        for pk in rows.values_list("pk", flat=True):
            pictures += stamp_row(model, pk, lines, sig, redo)

    videos = 0
    for video in Video.objects.exclude(file="", file_original=""):
        if video.wm_status == "done" and video.file and not redo and video.video_sig == sig:
            continue
        if out:
            out(f"Video: {video.title_sw} …")
        videos += video_jobs.process(video.pk, lines)
    return pictures, videos, posters, lines


class Command(BaseCommand):
    help = "Stamp the company badge on pictures and uploaded videos."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="redraw even when up to date")

    def handle(self, *args, **opts):
        pictures, videos, posters, lines = run(opts["all"], self.stdout.write)
        self.stdout.write(self.style.SUCCESS(
            f"Watermark: {pictures} pictures, {videos} videos, {posters} YouTube covers ({' | '.join(lines)})."))
