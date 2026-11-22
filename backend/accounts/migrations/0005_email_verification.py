from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_seed_default_departments")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="passwordresetotp",
            name="purpose",
            field=models.CharField(
                choices=[("PASSWORD_RESET", "Password reset"), ("EMAIL_VERIFICATION", "Email verification")],
                default="PASSWORD_RESET",
                max_length=20,
            ),
        ),
    ]
