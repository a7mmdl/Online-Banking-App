# Generated by Django 4.1.3 on 2024-04-06 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0041_installment"),
    ]

    operations = [
        migrations.AddField(
            model_name="installment",
            name="selected",
            field=models.BooleanField(default=False),
        ),
    ]