# Generated by Django 4.1.3 on 2024-04-06 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0039_issueloan_interest_amount"),
    ]

    operations = [
        migrations.AddField(
            model_name="issueloan",
            name="original_loan_amount",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
    ]