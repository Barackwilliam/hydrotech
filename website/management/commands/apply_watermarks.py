"""
Put the company badge on every picture and uploaded video that does not have the current one yet.

    python manage.py apply_watermarks          # only what is missing or out of date (fast when nothing changed)
    python manage.py apply_watermarks --all    # redraw everything

Runs on every deploy (build.sh). The badge is always drawn on the untouched copy kept in originals/,
never on top of an older badge. Pictures uploaded before watermarks existed become their own original.
"""
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from website import video_jobs, watermark
from website.models import CompanyInfo, Project, Service, Video


class Command(BaseCommand):
    help = "Stamp the company badge on pictures and uploaded videos."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="redraw even when up to date")

    def handle(self, *args, **opts):
        company = CompanyInfo.load()
        lines = company._watermark_lines()
        sig = watermark.signature(lines)
        done = 0
        for model, fields in ((CompanyInfo, ("hero_image", "about_image")), (Service, ("image",)), (Project, ("image",))):
            for obj in model.objects.all():
                if obj.wm_sig == sig and not opts["all"]:
                    continue
                changes = {}
                for name in fields:
                    image, original = getattr(obj, name), getattr(obj, name + "_original")
                    if not image:
                        continue
                    if original:
                        with original.open("rb") as fh:
                            data = fh.read()
                    else:
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
                changes["wm_sig"] = sig
                model.objects.filter(pk=obj.pk).update(**changes)
        videos = 0
        for video in Video.objects.exclude(file="", file_original=""):
            if video.wm_sig == sig and video.wm_status == "done" and not opts["all"]:
                continue
            self.stdout.write(f"Video: {video.title_sw} …")
            videos += video_jobs.process(video.pk, lines)
        self.stdout.write(self.style.SUCCESS(f"Watermark: {done} pictures, {videos} videos updated ({' | '.join(lines)})."))
