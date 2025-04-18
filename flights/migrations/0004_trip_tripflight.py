# Generated by Django 5.2 on 2025-04-15 18:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flights", "0003_airport_inbound_connections_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Trip",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("departure_time", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "destination",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trip_destination",
                        to="flights.airport",
                    ),
                ),
                (
                    "origin",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trip_origin",
                        to="flights.airport",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TripFlight",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "flight",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="flights.flight"
                    ),
                ),
                (
                    "trip",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="flights",
                        to="flights.trip",
                    ),
                ),
            ],
        ),
    ]
