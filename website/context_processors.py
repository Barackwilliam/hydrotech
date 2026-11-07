from django.conf import settings

from . import i18n
from .models import CompanyInfo, Service


def site(request):
    lang = i18n.get_lang(request)
    request.lang = lang
    return {
        "lang": lang,
        "t": i18n.strings(lang),
        "company": CompanyInfo.load(),
        "nav_services": Service.objects.filter(is_active=True).only("slug", "title_sw", "title_en", "icon"),
        "site_url": settings.SITE_URL or request.build_absolute_uri("/").rstrip("/"),
    }
