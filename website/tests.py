import shutil
import tempfile
from io import BytesIO, StringIO

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
        self.assertEqual(before, (9, 10))

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

    def test_uploaded_video_plays_from_storage(self):
        from .models import Video
        with override_settings(MEDIA_ROOT=MEDIA):
            Video.objects.create(title_sw="Faili", file=SimpleUploadedFile("kisima.mp4", b"0000", "video/mp4"))
            r = self.client.get(reverse("videos"))
            self.assertContains(r, 'data-kind="file"')
            self.assertContains(r, "/media/videos/kisima")
