"""The drilling service's steps now end with the pump test (water yield). Only steps that are still the
original text are changed: steps the client rewrote in the admin are left alone."""
from django.db import migrations

OLD = {
    "steps_sw": "Utafiti wa maji ardhini na kuchagua sehemu ya kuchimba\nKuchimba kwa rig hadi kufikia tabaka la maji\n"
                "Kuweka casing, screen na gravel pack\nKusafisha kisima (development / flushing)\n"
                "Kupima wingi wa maji (pump test)\nKukabidhi kisima pamoja na ripoti",
    "steps_en": "Groundwater survey and choosing the drilling point\nRig drilling down to the water-bearing layer\n"
                "Installing casing, screens and gravel pack\nCleaning the borehole (development / flushing)\n"
                "Yield test (pump test)\nHandover with a report",
}
NEW = {
    "steps_sw": "Utafiti wa maji ardhini na kuchagua sehemu ya kuchimba\nKuchimba kwa rig hadi kufikia tabaka la maji\n"
                "Kuweka casing, screen na gravel pack\nKusafisha kisima (development / flushing)\n"
                "Kukabidhi kisima pamoja na ripoti\nPump Test: Kupima Wingi wa Maji",
    "steps_en": "Groundwater survey and choosing the drilling point\nRig drilling down to the water-bearing layer\n"
                "Installing casing, screens and gravel pack\nCleaning the borehole (development / flushing)\n"
                "Handover with a report\nPump Test: measuring the water yield",
}


def forwards(apps, schema_editor):
    Service = apps.get_model("website", "Service")
    for field in OLD:
        Service.objects.filter(slug="uchimbaji-visima", **{field: OLD[field]}).update(**{field: NEW[field]})


def backwards(apps, schema_editor):
    Service = apps.get_model("website", "Service")
    for field in OLD:
        Service.objects.filter(slug="uchimbaji-visima", **{field: NEW[field]}).update(**{field: OLD[field]})


class Migration(migrations.Migration):
    dependencies = [("website", "0005_watermark_team_posters")]
    operations = [migrations.RunPython(forwards, backwards)]
