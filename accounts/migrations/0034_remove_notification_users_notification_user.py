# Generated by Django 4.1.3 on 2024-04-03 13:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0033_notification"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notification",
            name="users",
        ),
        migrations.AddField(
            model_name="notification",
            name="user",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]