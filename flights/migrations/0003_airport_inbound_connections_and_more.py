# Generated by Django 5.2 on 2025-04-15 03:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flights", "0002_route"),
    ]

    operations = [
        migrations.AddField(
            model_name="airport",
            name="inbound_connections",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="airport",
            name="outbound_connections",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
