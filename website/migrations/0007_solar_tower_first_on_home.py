"""The client asked for the steel tank tower with solar panels on the home page: put it first among the
featured projects. A no-op where the project does not exist yet (seed_site then creates it in first place)."""
from django.db import migrations

TITLE = "Mnara wa chuma wa matenki na paneli za solar"


def forwards(apps, schema_editor):
    Project = apps.get_model("website", "Project")
    Project.objects.filter(title_sw=TITLE).update(order=0, featured=True, is_active=True)


class Migration(migrations.Migration):
    dependencies = [("website", "0006_drilling_ends_with_pump_test")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
