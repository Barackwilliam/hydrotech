from django.contrib import admin
from django.utils.html import format_html

from .models import CompanyInfo, Inquiry, Project, Region, Service, TeamMember, Video


def thumb(image, size=60):
    if not image:
        return "—"
    return format_html('<img src="{}" style="height:{}px;width:auto;border-radius:6px">', image.url, size)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Kampuni", {"fields": ["name", "founded_year", "ceo_name", "tagline_sw", "tagline_en"]}),
        ("Kuhusu sisi", {"fields": ["about_sw", "about_en", "about_image"]}),
        ("Mawasiliano", {"fields": ["phone_1", "phone_2", "whatsapp", "email", "po_box",
                                    "address_sw", "address_en", "map_query"]}),
        ("Mitandao ya kijamii", {"fields": ["facebook_url", "instagram_url", "tiktok_url"]}),
        ("Ukurasa wa mwanzo", {"fields": ["hero_image"]}),
    ]

    def has_add_permission(self, request):
        return not CompanyInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["title_sw", "preview", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ["title_sw"]}
    fieldsets = [
        (None, {"fields": ["title_sw", "title_en", "slug", "icon", "image", "order", "is_active"]}),
        ("Kiswahili", {"fields": ["summary_sw", "body_sw", "steps_sw"]}),
        ("English", {"fields": ["summary_en", "body_en", "steps_en"]}),
    ]

    @admin.display(description="Picha")
    def preview(self, obj):
        return thumb(obj.image)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ["name", "role_sw", "preview", "order", "is_active"]
    list_editable = ["order", "is_active"]

    @admin.display(description="Picha")
    def preview(self, obj):
        return thumb(obj.photo)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title_sw", "preview", "service", "region", "featured", "is_active", "order"]
    list_editable = ["featured", "is_active", "order"]
    list_filter = ["service", "region", "featured", "is_active"]
    search_fields = ["title_sw", "title_en", "place"]
    fieldsets = [
        (None, {"fields": ["image", "title_sw", "title_en", "service", "region", "place", "date_done"]}),
        ("Maelezo", {"fields": ["description_sw", "description_en"]}),
        ("Kuonekana", {"fields": ["featured", "is_active", "order"]}),
    ]

    @admin.display(description="Picha")
    def preview(self, obj):
        return thumb(obj.image)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ["name", "phone_link", "service", "region", "created_at", "handled"]
    list_editable = ["handled"]
    list_filter = ["handled", "service", "created_at"]
    search_fields = ["name", "phone", "email", "region", "message"]
    readonly_fields = ["name", "phone", "email", "region", "service", "message", "created_at"]

    def has_add_permission(self, request):
        return False

    @admin.display(description="Simu")
    def phone_link(self, obj):
        digits = "".join(c for c in obj.phone if c.isdigit())
        if digits.startswith("0"):
            digits = "255" + digits[1:]
        return format_html('<a href="tel:+{}">{}</a> · <a href="https://wa.me/{}" target="_blank">WhatsApp</a>',
                           digits, obj.phone, digits)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ["title_sw", "preview", "source", "featured", "is_active", "order"]
    list_editable = ["featured", "is_active", "order"]
    list_filter = ["featured", "is_active", "service"]
    search_fields = ["title_sw", "title_en", "url"]
    fieldsets = [
        ("Video: pakia faili AU bandika link (YouTube, Facebook, Instagram)", {"fields": ["file", "url", "poster", "orientation"]}),
        ("Maelezo", {"fields": ["title_sw", "title_en", "description_sw", "description_en", "service"]}),
        ("Kuonekana", {"fields": ["featured", "is_active", "order"]}),
    ]

    @admin.display(description="Picha")
    def preview(self, obj):
        if obj.thumb:
            return format_html('<img src="{}" style="height:60px;width:auto;border-radius:6px">', obj.thumb)
        return "—"

    @admin.display(description="Chanzo")
    def source(self, obj):
        return {"file": "Faili", "youtube": "YouTube", "facebook": "Facebook", "instagram": "Instagram"}.get(obj.kind, "—")
