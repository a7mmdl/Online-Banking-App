# Generated by Django 4.1.3 on 2024-04-05 02:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0037_issueloan_approved"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="issueloan",
            name="interest",
        ),
        migrations.AlterField(
            model_name="issueloan",
            name="approved",
            field=models.BooleanField(default=True),
        ),
    ]
