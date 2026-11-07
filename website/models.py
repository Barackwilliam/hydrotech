"""
Content of the site. Text the visitor reads exists in Swahili (_sw) and English (_en); when the English
is left empty, the Swahili is shown.
"""
from django.db import models
from django.urls import reverse

from .images import shrink

ICONS = [
    ("drill", "Uchimbaji / Drilling"),
    ("search", "Utafiti / Survey"),
    ("pump", "Pump"),
    ("sun", "Solar"),
    ("tank", "Tenki / Tank"),
    ("wrench", "Ukarabati / Repair"),
    ("flask", "Maabara / Lab"),
    ("gauge", "Kipimo / Test"),
    ("dam", "Bwawa / Dam"),
    ("sprout", "Umwagiliaji / Irrigation"),
]


class ShrinkImagesMixin:
    image_fields = ()

    def save(self, *args, **kwargs):
        for name in self.image_fields:
            shrink(getattr(self, name))
        super().save(*args, **kwargs)


class CompanyInfo(ShrinkImagesMixin, models.Model):
    """One row only: the details shown in the header, footer and contact page."""
    image_fields = ("hero_image", "about_image")

    name = models.CharField(max_length=120, default="Milan Hydrotech")
    tagline_sw = models.CharField("kauli mbiu (SW)", max_length=200, blank=True)
    tagline_en = models.CharField("tagline (EN)", max_length=200, blank=True)
    about_sw = models.TextField("kuhusu sisi (SW)", blank=True)
    about_en = models.TextField("about us (EN)", blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    ceo_name = models.CharField(max_length=120, blank=True)
    phone_1 = models.CharField(max_length=30, blank=True, help_text="Mfano: +255714425262")
    phone_2 = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True, help_text="Namba ya WhatsApp, mfano +255714425262")
    email = models.EmailField(blank=True)
    po_box = models.CharField("S.L.P", max_length=60, blank=True)
    address_sw = models.CharField("ofisi kuu (SW)", max_length=200, blank=True)
    address_en = models.CharField("head office (EN)", max_length=200, blank=True)
    map_query = models.CharField(
        max_length=200, blank=True, help_text="Mahali pa kuonyesha kwenye ramani, mfano 'Mafinga, Iringa, Tanzania'")
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    hero_image = models.ImageField(upload_to="site/", blank=True, help_text="Picha kubwa ya ukurasa wa mwanzo")
    about_image = models.ImageField(upload_to="site/", blank=True)

    class Meta:
        verbose_name = "Taarifa za kampuni"
        verbose_name_plural = "Taarifa za kampuni"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @staticmethod
    def _digits(number):
        return "".join(ch for ch in number if ch.isdigit())

    @property
    def phone_1_tel(self):
        return "+" + self._digits(self.phone_1) if self.phone_1 else ""

    @property
    def phone_2_tel(self):
        return "+" + self._digits(self.phone_2) if self.phone_2 else ""

    @property
    def whatsapp_digits(self):
        return self._digits(self.whatsapp or self.phone_1)


class Region(models.Model):
    name = models.CharField(max_length=60, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Mkoa"
        verbose_name_plural = "Mikoa tunayohudumia"

    def __str__(self):
        return self.name


class Service(ShrinkImagesMixin, models.Model):
    image_fields = ("image",)

    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=20, choices=ICONS, default="drill")
    title_sw = models.CharField("jina (SW)", max_length=120)
    title_en = models.CharField("name (EN)", max_length=120, blank=True)
    summary_sw = models.CharField("maelezo mafupi (SW)", max_length=260)
    summary_en = models.CharField("short text (EN)", max_length=260, blank=True)
    body_sw = models.TextField("maelezo kamili (SW)", blank=True, help_text="Kila mstari mpya ni aya mpya.")
    body_en = models.TextField("full text (EN)", blank=True)
    steps_sw = models.TextField("hatua (SW)", blank=True, help_text="Hatua moja kwa kila mstari.")
    steps_en = models.TextField("steps (EN)", blank=True)
    image = models.ImageField(upload_to="services/", blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField("ionekane", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Huduma"
        verbose_name_plural = "Huduma"

    def __str__(self):
        return self.title_sw

    def get_absolute_url(self):
        return reverse("service_detail", args=[self.slug])


class TeamMember(ShrinkImagesMixin, models.Model):
    image_fields = ("photo",)

    name = models.CharField(max_length=120)
    role_sw = models.CharField("cheo (SW)", max_length=120, blank=True)
    role_en = models.CharField("role (EN)", max_length=120, blank=True)
    photo = models.ImageField(upload_to="team/", blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField("aonekane", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Mfanyakazi"
        verbose_name_plural = "Timu"

    def __str__(self):
        return self.name

    @property
    def initials(self):
        parts = [p for p in self.name.split() if p[:1].isalpha()]
        return "".join(p[0] for p in parts[:2]).upper()


class Project(ShrinkImagesMixin, models.Model):
    """A finished job shown in the gallery."""
    image_fields = ("image",)

    title_sw = models.CharField("jina (SW)", max_length=160)
    title_en = models.CharField("title (EN)", max_length=160, blank=True)
    description_sw = models.TextField("maelezo (SW)", blank=True)
    description_en = models.TextField("description (EN)", blank=True)
    image = models.ImageField(upload_to="projects/")
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL, related_name="projects")
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="projects")
    place = models.CharField("mahali", max_length=120, blank=True, help_text="Mfano: Shule ya Msingi X, Makambako")
    date_done = models.DateField("tarehe ya kukamilika", null=True, blank=True)
    featured = models.BooleanField("onyesha ukurasa wa mwanzo", default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField("ionekane", default=True)

    class Meta:
        ordering = ["order", "-date_done", "-id"]
        verbose_name = "Mradi"
        verbose_name_plural = "Miradi / Gallery"

    def __str__(self):
        return self.title_sw


class Inquiry(models.Model):
    """A request sent from the contact form."""
    name = models.CharField("jina", max_length=120)
    phone = models.CharField("simu", max_length=30)
    email = models.EmailField("barua pepe", blank=True)
    region = models.CharField("mkoa / mahali", max_length=120, blank=True)
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField("ujumbe")
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField("imeshughulikiwa", default=False)

    class Meta:
        ordering = ["handled", "-created_at"]
        verbose_name = "Ombi la mteja"
        verbose_name_plural = "Maombi ya wateja"

    def __str__(self):
        return f"{self.name} ({self.phone})"
