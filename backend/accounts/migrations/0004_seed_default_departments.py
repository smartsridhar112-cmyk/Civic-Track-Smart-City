from django.db import migrations


DEFAULT_DEPARTMENTS = [
    ("Public Works", "ROAD", "Road maintenance and damage reports."),
    ("Sanitation", "GARBAGE", "Garbage collection and sanitation reports."),
    ("Water Supply", "WATER", "Water supply and service reports."),
    ("Electricity", "ELECTRICITY", "Street lighting and electrical service reports."),
    ("Drainage", "DRAINAGE", "Drainage and sewerage reports."),
    ("General Services", "OTHER", "Reports that do not fit another department."),
]


def create_default_departments(apps, schema_editor):
    Department = apps.get_model("accounts", "Department")
    for name, category, description in DEFAULT_DEPARTMENTS:
        department = Department.objects.filter(complaint_category=category).first()
        if department:
            continue

        department = Department.objects.filter(name=name).first()
        if department:
            department.complaint_category = category
            department.description = department.description or description
            department.save(update_fields=["complaint_category", "description"])
        else:
            Department.objects.create(
                name=name,
                complaint_category=category,
                description=description,
            )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_password_reset_otp")]

    operations = [migrations.RunPython(create_default_departments, migrations.RunPython.noop)]
