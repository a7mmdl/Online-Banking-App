# Generated by Django 4.1.3 on 2024-04-03 13:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0026_notification_userprofile_notification"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notification",
            name="sender",
        ),
    ]
