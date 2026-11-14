from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponsePermanentRedirect
from django.templatetags.static import static as static_url
from django.urls import include, path

from website import views
from website.sitemaps import ServiceSitemap, StaticSitemap

admin.site.site_header = "Milan Hydrotech — Usimamizi"
admin.site.site_title = "Milan Hydrotech"
admin.site.index_title = "Simamia website"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": {"pages": StaticSitemap, "services": ServiceSitemap}},
         name="sitemap"),
    path("robots.txt", views.robots_txt),
    path("favicon.ico", lambda request: HttpResponsePermanentRedirect(static_url("img/favicon.png"))),
    path("", include("website.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "website.views.page_not_found"
