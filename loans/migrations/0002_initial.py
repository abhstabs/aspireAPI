# Generated by Django 4.2 on 2023-04-30 09:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("loans", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="loanapplication",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="applications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
