"""Add the pump test service to the company tagline, but only where it is still the original text:
a tagline the client rewrote in the admin is left alone."""
from django.db import migrations

OLD = {
    "tagline_sw": "Wataalamu wa uchimbaji wa visima vya maji kwa mashine kubwa, utafiti wa maji ardhini, pampu na solar",
    "tagline_en": "Specialists in borehole drilling with heavy rigs, groundwater survey, pumps and solar",
}
NEW = {
    "tagline_sw": "Wataalamu wa uchimbaji wa visima vya maji kwa mashine kubwa, utafiti wa maji ardhini, "
                  "upimaji wa wingi wa maji (pump test), pampu na solar",
    "tagline_en": "Specialists in borehole drilling with heavy rigs, groundwater survey, "
                  "water yield testing (pump test), pumps and solar",
}


def forwards(apps, schema_editor):
    CompanyInfo = apps.get_model("website", "CompanyInfo")
    for field in OLD:
        CompanyInfo.objects.filter(**{field: OLD[field]}).update(**{field: NEW[field]})


def backwards(apps, schema_editor):
    CompanyInfo = apps.get_model("website", "CompanyInfo")
    for field in OLD:
        CompanyInfo.objects.filter(**{field: NEW[field]}).update(**{field: OLD[field]})


class Migration(migrations.Migration):
    dependencies = [("website", "0003_watermarks")]
    operations = [migrations.RunPython(forwards, backwards)]
