import shutil
import tempfile
from io import BytesIO, StringIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Inquiry, Project, Service

MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", stdout=StringIO())

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def test_pages_load(self):
        for name in ["home", "about", "services", "projects", "contact"]:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, "Milan Hydrotech")

    def test_service_page(self):
        r = self.client.get(reverse("service_detail", args=["uchimbaji-visima"]))
        self.assertContains(r, "Uchimbaji wa Visima vya Maji")
        self.assertEqual(self.client.get("/huduma/haipo/").status_code, 404)

    def test_seed_runs_twice_without_duplicates(self):
        before = (Service.objects.count(), Project.objects.count())
        call_command("seed_site", stdout=StringIO())
        self.assertEqual(before, (Service.objects.count(), Project.objects.count()))
        self.assertEqual(before, (9, 26))

    def test_language_switch(self):
        r = self.client.get(reverse("set_language", args=["en"]) + "?next=/huduma/")
        self.assertRedirects(r, "/huduma/")
        r = self.client.get(reverse("services"))
        self.assertContains(r, "Borehole Drilling &amp; Construction")
        self.assertContains(r, 'lang="en"')

    def test_language_switch_refuses_outside_redirect(self):
        r = self.client.get(reverse("set_language", args=["en"]) + "?next=https://evil.example/")
        self.assertEqual(r["Location"], "/")

    def test_contact_form_saves_request(self):
        r = self.client.post(reverse("contact"), {
            "name": "Juma", "phone": "0712 345 678", "region": "Njombe",
            "service": Service.objects.get(slug="pump-test").pk, "message": "Nahitaji pump test."})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Inquiry.objects.get().region, "Njombe")

    def test_contact_form_rejects_bad_phone(self):
        r = self.client.post(reverse("contact"), {"name": "A", "phone": "12", "message": "x"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Inquiry.objects.exists())

    def test_honeypot_drops_spam(self):
        self.client.post(reverse("contact"), {
            "name": "Bot", "phone": "0712345678", "message": "spam", "website": "http://spam"})
        self.assertFalse(Inquiry.objects.exists())

    def test_large_upload_is_shrunk(self):
        buf = BytesIO()
        Image.new("RGB", (4000, 3000), "blue").save(buf, "PNG")
        p = Project(title_sw="Kubwa", image=SimpleUploadedFile("kubwa.png", buf.getvalue(), "image/png"))
        p.save()
        with Image.open(p.image.path) as img:
            self.assertEqual(max(img.size), 1600)
            self.assertEqual(img.format, "JPEG")

    def test_sitemap_and_robots(self):
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)
        self.assertContains(self.client.get("/robots.txt"), "Sitemap:")

    def test_service_text_is_paragraphs_not_escaped_html(self):
        r = self.client.get(reverse("service_detail", args=["uchimbaji-visima"]))
        self.assertContains(r, "<p>Kisima kizuri")
        self.assertNotContains(r, "&lt;p&gt;")

    def test_paragraph_text_is_escaped(self):
        from .models import CompanyInfo
        c = CompanyInfo.load()
        c.about_sw = "Mstari wa kwanza\n<script>alert(1)</script>"
        c.save()
        r = self.client.get(reverse("about"))
        self.assertContains(r, "<p>Mstari wa kwanza</p>")
        self.assertContains(r, "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>")

    def test_language_popup_only_on_first_visit(self):
        self.assertContains(self.client.get(reverse("home")), 'id="lang-modal"')
        self.client.cookies["lang"] = "sw"
        self.assertNotContains(self.client.get(reverse("home")), 'id="lang-modal"')

    def test_choosing_english_in_popup_is_remembered(self):
        self.client.get(reverse("set_language", args=["en"]) + "?next=/")
        r = self.client.get(reverse("about"))
        self.assertContains(r, 'lang="en"')
        self.assertNotContains(r, 'id="lang-modal"')


    def test_page_heads_have_sliding_pictures(self):
        for name in ["about", "services", "projects", "contact"]:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertContains(r, 'class="slides"')
                self.assertGreater(len(r.context["slides"]), 1)
        r = self.client.get(reverse("service_detail", args=["pump-test"]))
        self.assertIn("pump-test", r.context["slides"][0])


class EmptySiteTests(TestCase):
    """A fresh database (no seed_site yet) must still show every page, never a server error."""

    def test_pages_load_without_any_content(self):
        for name in ["home", "about", "services", "projects", "contact"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_home_with_one_project(self):
        buf = BytesIO()
        Image.new("RGB", (40, 30), "blue").save(buf, "JPEG")
        with override_settings(MEDIA_ROOT=MEDIA):
            Project.objects.create(title_sw="Moja", image=SimpleUploadedFile("moja.jpg", buf.getvalue(), "image/jpeg"))
            self.assertContains(self.client.get(reverse("home")), "moja")


class VideoTests(TestCase):
    def test_link_recognition(self):
        from . import videos as v
        cases = {
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=5": ("youtube", "dQw4w9WgXcQ", False),
            "https://youtu.be/dQw4w9WgXcQ": ("youtube", "dQw4w9WgXcQ", False),
            "https://youtube.com/shorts/dQw4w9WgXcQ?si=x": ("youtube", "dQw4w9WgXcQ", True),
            "https://www.facebook.com/milan/videos/123456789/": ("facebook", None, False),
            "https://www.facebook.com/reel/123456789": ("facebook", None, True),
            "https://www.instagram.com/reel/C8abcDEF12/?igsh=x": ("instagram", None, True),
        }
        for url, (kind, yt, vertical) in cases.items():
            with self.subTest(url=url):
                self.assertEqual(v.platform(url), kind)
                self.assertTrue(v.embed_url(url))
                self.assertEqual(v.is_vertical_link(url), vertical)
                if yt:
                    self.assertEqual(v.youtube_id(url), yt)
                    self.assertIn(f"/embed/{yt}", v.embed_url(url))
                    self.assertIn(yt, v.thumbnail_url(url))
        self.assertEqual(v.embed_url("https://www.instagram.com/reel/C8abcDEF12/"), "https://www.instagram.com/reel/C8abcDEF12/embed/")
        self.assertEqual(v.platform("https://vimeo.com/1"), "")
        self.assertEqual(v.youtube_id("https://www.youtube.com/watch?v=bad"), "")

    def test_video_needs_exactly_one_source(self):
        from django.core.exceptions import ValidationError
        from .models import Video
        with self.assertRaises(ValidationError):
            Video(title_sw="Tupu").full_clean()
        with self.assertRaises(ValidationError):
            Video(title_sw="Vimeo", url="https://vimeo.com/1").full_clean()
        with self.assertRaises(ValidationError):  # short share links cannot be embedded
            Video(title_sw="FB", url="https://www.facebook.com/share/r/1DyHyjQpKW/").full_clean()
        Video(title_sw="YT", url="https://youtu.be/dQw4w9WgXcQ").full_clean()

    def test_video_file_type_and_size(self):
        from django.core.exceptions import ValidationError
        from .models import validate_video_file
        with self.assertRaises(ValidationError):
            validate_video_file(SimpleUploadedFile("a.exe", b"x"))
        with override_settings(VIDEO_MAX_MB=0):
            with self.assertRaises(ValidationError):
                validate_video_file(SimpleUploadedFile("a.mp4", b"x"))
        validate_video_file(SimpleUploadedFile("a.mp4", b"x"))

    def test_pages_show_videos(self):
        from .models import Video
        self.assertContains(self.client.get(reverse("videos")), "empty__icon")
        self.assertNotContains(self.client.get(reverse("home")), "data-video")
        Video.objects.create(title_sw="Kuchimba Njombe", url="https://youtu.be/dQw4w9WgXcQ")
        Video.objects.create(title_sw="Reel", url="https://www.instagram.com/reel/C8abcDEF12/")
        for name in ["home", "videos"]:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertContains(r, "Kuchimba Njombe")
                self.assertContains(r, "youtube-nocookie.com/embed/dQw4w9WgXcQ")
                self.assertContains(r, 'id="vplayer"')
                self.assertContains(r, "vcard--tall")

    def test_uploaded_video_shows_only_with_its_watermark(self):
        from .models import Video
        with override_settings(MEDIA_ROOT=MEDIA, VIDEO_WATERMARK_SYNC=True):
            with self.captureOnCommitCallbacks(execute=True):
                v = Video.objects.create(title_sw="Kisima Mafinga", file=SimpleUploadedFile("kisima.mp4", make_mp4(), "video/mp4"))
            v.refresh_from_db()
            self.assertEqual(v.wm_status, "done")
            self.assertTrue(v.file_original.name.startswith("originals/"))
            self.assertRegex(v.file.name, r"^videos/kisima-mafinga-[0-9a-f]{8}\.mp4$")
            r = self.client.get(reverse("videos"))
            self.assertContains(r, 'data-kind="file"')
            self.assertContains(r, "/media/videos/kisima-mafinga")
            self.assertNotContains(r, "originals/")

    def test_video_still_being_stamped_is_hidden(self):
        from .models import Video
        with override_settings(MEDIA_ROOT=MEDIA):
            Video.objects.create(title_sw="Bado", file=SimpleUploadedFile("bado.mp4", b"0000", "video/mp4"))
            self.assertEqual(Video.objects.get().wm_status, "pending")
            self.assertNotContains(self.client.get(reverse("videos")), "Bado")


def make_mp4(seconds=1):
    import subprocess
    from . import watermark
    out = Path(tempfile.mkdtemp()) / "sample.mp4"
    subprocess.run([watermark.ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"color=c=blue:s=320x240:d={seconds}", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out.read_bytes()


def jpeg(size=(800, 600), colour="blue"):
    buf = BytesIO()
    Image.new("RGB", size, colour).save(buf, "JPEG")
    return buf.getvalue()


@override_settings(MEDIA_ROOT=MEDIA)
class WatermarkTests(TestCase):
    def setUp(self):
        from .models import CompanyInfo
        c = CompanyInfo.load()
        c.name, c.website_domain, c.phone_1 = "Milan Hydrotech", "milanhydrotech.co.tz", "+255 714 425 262"
        c.save()

    def test_local_phone(self):
        from .watermark import local_phone
        self.assertEqual(local_phone("+255 714 425 262"), "0714 425 262")
        self.assertEqual(local_phone("0714425262"), "0714 425 262")

    def test_new_picture_gets_badge_and_keeps_original(self):
        p = Project.objects.create(title_sw="Kisima", image=SimpleUploadedFile("k.jpg", jpeg(), "image/jpeg"))
        self.assertTrue(p.image_original.name.startswith("originals/"))
        self.assertTrue(p.wm_sig)
        with Image.open(p.image.path) as marked, Image.open(p.image_original.path) as plain:
            self.assertEqual(marked.size, plain.size)
            top = marked.convert("RGB").getpixel((400, 40))     # badge at the top centre
            corner = marked.convert("RGB").getpixel((10, 590))  # untouched elsewhere
            self.assertNotEqual(top, plain.convert("RGB").getpixel((400, 40)))
            self.assertEqual(corner, plain.convert("RGB").getpixel((10, 590)))

    def test_apply_watermarks_redraws_from_original_when_text_changes(self):
        from .models import CompanyInfo
        p = Project.objects.create(title_sw="Kisima", image=SimpleUploadedFile("k.jpg", jpeg(), "image/jpeg"))
        first, original = p.image.name, p.image_original.name
        call_command("apply_watermarks", stdout=StringIO())  # nothing changed: nothing redone
        p.refresh_from_db()
        self.assertEqual(p.image.name, first)
        c = CompanyInfo.load(); c.phone_1 = "+255 784 822 566"; c.save()
        call_command("apply_watermarks", stdout=StringIO())
        p.refresh_from_db()
        self.assertNotEqual(p.image.name, first)
        self.assertEqual(p.image_original.name, original)       # badge drawn on the clean copy
        self.assertFalse(p.image.storage.exists(first))           # old stamped file removed

    def test_old_pictures_become_their_own_original(self):
        Project.objects.create(title_sw="Kisima", image=SimpleUploadedFile("k.jpg", jpeg(), "image/jpeg"))
        Project.objects.update(image_original="", wm_sig="")       # as if uploaded before watermarks
        call_command("apply_watermarks", stdout=StringIO())
        p = Project.objects.get()
        self.assertTrue(p.image_original and p.wm_sig)

    def test_seeded_pictures_carry_the_badge(self):
        call_command("seed_site", stdout=StringIO())
        self.assertFalse(Project.objects.filter(wm_sig="").exists())
        self.assertFalse(Service.objects.exclude(image="").filter(wm_sig="").exists())


class PumpTestEverywhereTests(TestCase):
    """The pump test (water yield) service shows wherever services are listed."""

    @classmethod
    def setUpTestData(cls):
        with override_settings(MEDIA_ROOT=MEDIA):
            call_command("seed_site", stdout=StringIO())

    def test_listed_on_every_page_footer_and_home(self):
        url = reverse("service_detail", args=["pump-test"])
        for name in ["home", "about", "services", "projects", "videos", "contact"]:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertContains(r, f'href="{url}"')                       # footer (and tiles)
                self.assertContains(r, "Upimaji wa Wingi wa Maji (Pump Test)")
        home = self.client.get(reverse("home"))
        self.assertContains(home, "Upimaji wa wingi wa maji (pump test)")        # hero highlights + tagline
        self.assertContains(home, '"name": "Upimaji wa Wingi wa Maji (Pump Test)"')  # Google service list

    def test_in_contact_form_and_english(self):
        self.assertContains(self.client.get(reverse("contact")), ">Upimaji wa Wingi wa Maji (Pump Test)</option>")
        self.client.get(reverse("set_language", args=["en"]))
        r = self.client.get(reverse("home"))
        self.assertContains(r, "Pump Test (Yield Test)")
        self.assertContains(r, "Water yield testing (pump test)")

    def test_old_tagline_is_updated_but_a_rewritten_one_is_kept(self):
        import importlib
        from django.apps import apps as django_apps
        from .models import CompanyInfo
        mig = importlib.import_module("website.migrations.0004_tagline_pump_test")
        c = CompanyInfo.load()
        c.tagline_sw, c.tagline_en = mig.OLD["tagline_sw"], "Our own words"
        c.save()
        mig.forwards(django_apps, None)
        c.refresh_from_db()
        self.assertEqual(c.tagline_sw, mig.NEW["tagline_sw"])
        self.assertEqual(c.tagline_en, "Our own words")



@override_settings(MEDIA_ROOT=MEDIA)
class WatermarkEverywhereTests(TestCase):
    """Every picture the site serves carries the badge: team photos, video posters, YouTube covers too."""

    def test_team_photo_and_video_poster_get_badge(self):
        from .models import TeamMember, Video
        m = TeamMember.objects.create(name="Imani", photo=SimpleUploadedFile("i.jpg", jpeg(), "image/jpeg"))
        v = Video.objects.create(title_sw="FB", url="https://www.facebook.com/milan/videos/1/",
                                 poster=SimpleUploadedFile("p.jpg", jpeg(), "image/jpeg"))
        for obj, name in ((m, "photo"), (v, "poster")):
            with self.subTest(field=name):
                self.assertTrue(getattr(obj, name + "_original").name.startswith("originals/"))
                self.assertTrue(obj.wm_sig)

    def test_youtube_cover_is_kept_as_watermarked_poster(self):
        from unittest import mock
        from .models import Video
        with override_settings(FETCH_YOUTUBE_POSTERS=True), \
                mock.patch("website.videos.download_thumbnail", return_value=jpeg((1280, 720))) as dl:
            v = Video.objects.create(title_sw="YT", url="https://youtu.be/dQw4w9WgXcQ")
        dl.assert_called_once()
        self.assertRegex(v.poster.name, r"^videos/posters/youtube-dQw4w9WgXcQ-[0-9a-f]{8}\.jpg$")
        self.assertTrue(v.poster_original and v.wm_sig)
        self.assertEqual(v.thumb, v.poster.url)  # the card shows our copy, never YouTube's own picture

    def test_youtube_without_cover_shows_no_outside_picture(self):
        from .models import Video
        v = Video.objects.create(title_sw="YT", url="https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(v.thumb, "")
        self.assertNotContains(self.client.get(reverse("videos")), "i.ytimg.com")

    def test_apply_watermarks_catches_everything_left_unstamped(self):
        from .models import CompanyInfo, TeamMember, Video
        TeamMember.objects.create(name="Imani", photo=SimpleUploadedFile("i.jpg", jpeg(), "image/jpeg"))
        Video.objects.create(title_sw="FB", url="https://www.facebook.com/milan/videos/1/",
                             poster=SimpleUploadedFile("p.jpg", jpeg(), "image/jpeg"))
        Project.objects.create(title_sw="K", image=SimpleUploadedFile("k.jpg", jpeg(), "image/jpeg"))
        for model in (TeamMember, Video, Project, CompanyInfo):  # as if saved before the badge existed
            model.objects.update(wm_sig="")
        TeamMember.objects.update(photo_original="")
        call_command("apply_watermarks", stdout=StringIO())
        for model in (TeamMember, Video, Project):
            with self.subTest(model=model.__name__):
                self.assertFalse(model.objects.filter(wm_sig="").exists())
        self.assertTrue(TeamMember.objects.get().photo_original)

    def test_background_stamping_runs_only_in_the_web_server(self):
        import sys
        from unittest import mock
        from . import apps
        with mock.patch.object(sys, "argv", ["manage.py", "migrate"]):
            self.assertFalse(apps._is_web_server())
        with mock.patch.object(sys, "argv", ["/venv/bin/gunicorn", "config.wsgi"]):
            self.assertTrue(apps._is_web_server())
        Project.objects.create(title_sw="K", image=SimpleUploadedFile("k.jpg", jpeg(), "image/jpeg"))
        Project.objects.update(wm_sig="")
        with mock.patch("website.apps.close_old_connections", create=True):
            apps._stamp_missing()
        self.assertFalse(Project.objects.filter(wm_sig="").exists())


@override_settings(MEDIA_ROOT=MEDIA)
class WatermarkRobustnessTests(TestCase):
    def test_one_broken_picture_does_not_stop_the_others(self):
        good1 = Project.objects.create(title_sw="A", image=SimpleUploadedFile("a.jpg", jpeg(), "image/jpeg"))
        bad = Project.objects.create(title_sw="Haipo", image=SimpleUploadedFile("b.jpg", jpeg(), "image/jpeg"))
        good2 = Project.objects.create(title_sw="C", image=SimpleUploadedFile("c.jpg", jpeg(), "image/jpeg"))
        Project.objects.update(wm_sig="", image_original="")
        bad.refresh_from_db(); bad.image.storage.delete(bad.image.name)   # file gone from storage
        out = StringIO()
        call_command("apply_watermarks", stdout=out)                       # no exception: the deploy goes on
        self.assertIn("WATERMARK FAILED", out.getvalue())
        self.assertIn("Haipo", out.getvalue())
        self.assertIn("1 rows with a picture still without the current badge", out.getvalue())
        for p in (good1, good2):
            p.refresh_from_db()
            self.assertTrue(p.wm_sig and p.image_original)


class SmallThingsTests(TestCase):
    def test_favicon_ico_points_to_the_logo(self):
        r = self.client.get("/favicon.ico")
        self.assertEqual(r.status_code, 301)
        self.assertIn("img/favicon", r["Location"])


@override_settings(MEDIA_ROOT=MEDIA)
class FreshNameTests(TestCase):
    """A stamped picture never reuses a URL an older picture had: browsers and the CDN cache them a year."""

    def test_fresh_name_keeps_readable_part_and_drops_old_tags(self):
        from .watermark import fresh_name
        self.assertRegex(fresh_name("services/solar-pump-shambani.jpg"), r"^solar-pump-shambani-[0-9a-f]{8}\.jpg$")
        self.assertRegex(fresh_name("solar-pump-shambani-1a2b3c4d.jpg"), r"^solar-pump-shambani-[0-9a-f]{8}\.jpg$")
        self.assertRegex(fresh_name("solar-pump-shambani_AbC12xY.jpg"), r"^solar-pump-shambani-[0-9a-f]{8}\.jpg$")
        self.assertNotEqual(fresh_name("a.jpg"), fresh_name("a.jpg"))

    def test_redrawing_never_reuses_a_previous_url(self):
        p = Project.objects.create(title_sw="S", image=SimpleUploadedFile("solar.jpg", jpeg(), "image/jpeg"))
        seen = {p.image.name}
        for _ in range(3):
            call_command("apply_watermarks", "--all", stdout=StringIO())
            p.refresh_from_db()
            self.assertNotIn(p.image.name, seen)
            seen.add(p.image.name)


class ClientRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        with override_settings(MEDIA_ROOT=MEDIA):
            call_command("seed_site", stdout=StringIO())

    def test_drilling_steps_end_with_pump_test_and_link_to_it(self):
        r = self.client.get(reverse("service_detail", args=["uchimbaji-visima"]))
        steps = r.context["service"].steps_sw.splitlines()
        self.assertEqual(steps[-1], "Pump Test: Kupima Wingi wa Maji")
        self.assertContains(r, 'class="final-step" href="/huduma/pump-test/"')
        self.assertNotContains(self.client.get(reverse("service_detail", args=["umwagiliaji"])), 'class="final-step"')

    def test_migration_updates_original_steps_only(self):
        import importlib
        from django.apps import apps as django_apps
        mig = importlib.import_module("website.migrations.0006_drilling_ends_with_pump_test")
        Service.objects.filter(slug="uchimbaji-visima").update(steps_sw=mig.OLD["steps_sw"], steps_en="Our own steps")
        mig.forwards(django_apps, None)
        s = Service.objects.get(slug="uchimbaji-visima")
        self.assertEqual(s.steps_sw, mig.NEW["steps_sw"])
        self.assertEqual(s.steps_en, "Our own steps")

    def test_all_client_pictures_in_projects_and_survey_has_its_picture(self):
        r = self.client.get(reverse("projects"))
        self.assertEqual(len(r.context["projects"]), 26)
        for title in ["Utafiti wa maji ardhini, Dodoma", "Rig ya kuchimba visima virefu", "Maji ni uhai: maji safi na salama"]:
            self.assertContains(r, title)
        self.assertTrue(Service.objects.get(slug="utafiti-wa-maji-ardhini").image)
        self.assertEqual(Project.objects.filter(service__slug="uchimbaji-visima").count(), 10)



@override_settings(MEDIA_ROOT=MEDIA, SEED_PROCESS_VIDEOS=True)
class SeedVideoTests(TestCase):
    def test_client_videos_get_watermark_orientation_and_cover(self):
        from .models import Video
        with self.captureOnCommitCallbacks(execute=True):
            call_command("seed_site", stdout=StringIO())
        videos = Video.objects.order_by("order")
        self.assertEqual(videos.count(), 2)
        for v in videos:
            with self.subTest(video=v.title_sw):
                self.assertEqual(v.wm_status, "done")
                self.assertTrue(v.file_original.name.startswith("originals/"))
                self.assertRegex(v.file.name, r"^videos/.+-[0-9a-f]{8}\.mp4$")
                self.assertEqual(v.orientation, "portrait")       # filmed upright on a phone
                self.assertTrue(v.poster and v.poster_original and v.wm_sig)  # cover from the video, stamped
        r = self.client.get(reverse("videos"))
        self.assertContains(r, "Rig yetu ikichimba kisima, maji yakitoka")
        self.assertContains(r, "vcard--tall")
        with self.captureOnCommitCallbacks(execute=True):
            call_command("seed_site", stdout=StringIO())      # a second run adds nothing
        self.assertEqual(Video.objects.count(), 2)



class HomePageTowerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        with override_settings(MEDIA_ROOT=MEDIA):
            call_command("seed_site", stdout=StringIO())

    def test_solar_tower_is_first_in_our_work_on_home(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.context["projects"][0].title_sw, "Mnara wa chuma wa matenki na paneli za solar")
        self.assertEqual(r.context["hero_second"].title_sw, "Mnara wa chuma wa matenki na paneli za solar")
        self.assertContains(r, "Mnara wa chuma wa matenki na paneli za solar")

    def test_migration_moves_an_existing_tower_to_the_front(self):
        import importlib
        from django.apps import apps as django_apps
        mig = importlib.import_module("website.migrations.0007_solar_tower_first_on_home")
        Project.objects.filter(title_sw=mig.TITLE).update(order=26, featured=False)   # as on the live site
        mig.forwards(django_apps, None)
        self.assertEqual(self.client.get(reverse("home")).context["projects"][0].title_sw, mig.TITLE)



class NoSourceLabelsTests(TestCase):
    """Videos show no 'YouTube / Facebook / Instagram' labels and no 'watch on ...' link."""

    def test_cards_and_player_carry_no_platform_names(self):
        from .models import Video
        Video.objects.create(title_sw="Rig", url="https://www.facebook.com/milan/videos/1/")
        Video.objects.create(title_sw="Reel", url="https://www.instagram.com/reel/C8abcDEF12/")
        Video.objects.create(title_sw="YT", url="https://youtu.be/dQw4w9WgXcQ")
        for name in ["home", "videos"]:
            with self.subTest(page=name):
                html = self.client.get(reverse(name)).content.decode()
                for word in ["vcard__badge", "vplayer__link", "Tazama kwenye", ">Facebook<", ">Instagram<", ">YouTube<"]:
                    self.assertNotIn(word, html)
