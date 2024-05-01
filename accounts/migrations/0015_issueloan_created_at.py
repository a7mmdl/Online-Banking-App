# Generated by Django 4.1.3 on 2024-02-27 11:22

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_alter_issueloan_approved"),
    ]

    operations = [
        migrations.AddField(
            model_name="issueloan",
            name="created_at",
            field=models.DateTimeField(default=timezone.now, auto_now_add=True),
            preserve_default=False,
        ),
    ]