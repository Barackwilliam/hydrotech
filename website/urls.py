from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("kuhusu-sisi/", views.about, name="about"),
    path("huduma/", views.services, name="services"),
    path("huduma/<slug:slug>/", views.service_detail, name="service_detail"),
    path("miradi/", views.projects, name="projects"),
    path("video/", views.videos, name="videos"),
    path("wasiliana-nasi/", views.contact, name="contact"),
    path("lugha/<str:lang>/", views.set_language, name="set_language"),
]
