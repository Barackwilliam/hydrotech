from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Service


class StaticSitemap(Sitemap):
    changefreq = "monthly"

    def items(self):
        return ["home", "about", "services", "projects", "videos", "contact"]

    def location(self, item):
        return reverse(item)


class ServiceSitemap(Sitemap):
    changefreq = "monthly"

    def items(self):
        return Service.objects.filter(is_active=True)
