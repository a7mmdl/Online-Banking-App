# Generated by Django 4.1.3 on 2024-03-05 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0017_remove_userprofile_fund_transfer_limit"),
    ]

    operations = [
        migrations.AddField(
            model_name="dailytransfer",
            name="transfer_limit",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
