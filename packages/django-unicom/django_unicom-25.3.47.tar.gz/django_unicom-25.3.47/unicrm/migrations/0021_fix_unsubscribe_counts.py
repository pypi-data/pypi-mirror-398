from django.db import migrations


def refresh_status_summaries(apps, schema_editor):
    from unicrm.models import Communication

    for communication in Communication.objects.all().iterator():
        communication.refresh_status_summary()


class Migration(migrations.Migration):

    dependencies = [
        ('unicrm', '0020_communication_skip_antispam_guards'),
    ]

    operations = [
        migrations.RunPython(
            refresh_status_summaries,
            migrations.RunPython.noop,
        ),
    ]
