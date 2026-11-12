import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET

from . import i18n
from .forms import InquiryForm
from .models import CompanyInfo, Project, Region, Service, TeamMember, Video

log = logging.getLogger(__name__)


def _active_services():
    return Service.objects.filter(is_active=True)


def _active_projects():
    return Project.objects.filter(is_active=True).select_related("service", "region")


def _active_videos():
    # an uploaded video shows only once it carries the watermark
    return Video.objects.filter(is_active=True).exclude(wm_status__in=["pending", "failed"]).select_related("service")


SLIDES_MAX = 5


def _slides(*image_lists):
    """Picture links for the sliding background of a page head: the given pictures first, then the
    hero picture and project photos, without repeats."""
    urls = []
    company = CompanyInfo.load()
    defaults = [company.hero_image] + [p.image for p in _active_projects()[:SLIDES_MAX]]
    for image in [img for images in image_lists for img in images] + defaults:
        if image and image.url not in urls:
            urls.append(image.url)
        if len(urls) == SLIDES_MAX:
            break
    return urls


def home(request):
    projects = list(_active_projects().filter(featured=True)[:6]) or list(_active_projects()[:6])
    return render(request, "website/home.html", {
        "services": _active_services(),
        "projects": projects,
        # pictures for the hero and the "why us" block; None while there are no projects yet
        "hero_second": projects[0] if projects else None,
        "why_project": projects[2] if len(projects) > 2 else (projects[0] if projects else None),
        "regions": Region.objects.all(),
        "team_count": TeamMember.objects.filter(is_active=True).count(),
        "videos": list(_active_videos().filter(featured=True)[:7]),
    })


def about(request):
    return render(request, "website/about.html", {
        "team": TeamMember.objects.filter(is_active=True),
        "regions": Region.objects.all(),
        "slides": _slides([CompanyInfo.load().about_image]),
    })


def services(request):
    items = _active_services()
    return render(request, "website/services.html", {
        "services": items, "slides": _slides([s.image for s in items])})


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    return render(request, "website/service_detail.html", {
        "service": service,
        "projects": _active_projects().filter(service=service)[:6],
        "others": _active_services().exclude(pk=service.pk),
        "slides": _slides([service.image], [p.image for p in _active_projects().filter(service=service)]),
    })


def projects(request):
    items = _active_projects()
    used = Service.objects.filter(is_active=True, projects__is_active=True).distinct()
    return render(request, "website/projects.html", {
        "projects": items, "filters": used, "slides": _slides([p.image for p in items])})


def videos(request):
    items = list(_active_videos())
    return render(request, "website/videos.html", {
        "videos": items, "slides": _slides([v.poster for v in items if v.poster])})


def contact(request):
    lang = i18n.get_lang(request)
    t = i18n.strings(lang)
    initial = {}
    if request.GET.get("service"):
        initial["service"] = Service.objects.filter(slug=request.GET["service"], is_active=True).first()
    form = InquiryForm(request.POST or None, t=t, lang=lang, initial=initial)
    if request.method == "POST":
        if form.is_valid():
            if not form.is_spam():
                inquiry = form.save()
                _notify_office(inquiry)
            messages.success(request, t["form_sent"])
            return redirect(reverse("contact") + "#fomu")
        messages.error(request, t["form_error"])
    return render(request, "website/contact.html", {
        "form": form, "regions": Region.objects.all(), "slides": _slides()})


def _notify_office(inquiry):
    to = settings.INQUIRY_NOTIFY_EMAIL
    if not to:
        return
    body = (f"Jina: {inquiry.name}\nSimu: {inquiry.phone}\nEmail: {inquiry.email or '-'}\n"
            f"Mahali: {inquiry.region or '-'}\nHuduma: {inquiry.service or '-'}\n\n{inquiry.message}")
    try:
        send_mail(f"Ombi jipya la mteja: {inquiry.name}", body, None, [to])
    except Exception:  # the request is saved in the admin either way
        log.exception("Could not email the new inquiry")


@require_GET
def set_language(request, lang):
    target = request.GET.get("next") or "/"
    if not url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
        target = "/"
    response = redirect(target)
    if lang in i18n.LANGS:
        response.set_cookie(i18n.COOKIE, lang, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response


@require_GET
def robots_txt(request):
    base = settings.SITE_URL or request.build_absolute_uri("/").rstrip("/")
    lines = ["User-agent: *", f"Disallow: /{settings.ADMIN_URL}", f"Sitemap: {base}/sitemap.xml", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def page_not_found(request, exception):
    return render(request, "website/404.html", {"slides": _slides()}, status=404)
