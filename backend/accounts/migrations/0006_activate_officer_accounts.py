from django.db import migrations


def activate_officers(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="OFFICER").update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_email_verification")]

    operations = [migrations.RunPython(activate_officers, migrations.RunPython.noop)]
