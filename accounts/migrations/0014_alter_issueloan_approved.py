# Generated by Django 4.1.3 on 2024-02-27 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_issueloan"),
    ]

    operations = [
        migrations.AlterField(
            model_name="issueloan",
            name="approved",
            field=models.BooleanField(default=True),
        ),
    ]
