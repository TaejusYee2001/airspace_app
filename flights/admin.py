from django.contrib import admin

from flights.models import Airport, Flight, Route, Trip, TripFlight

admin.site.register(Airport)
admin.site.register(Flight)
admin.site.register(Route)
admin.site.register(Trip)
admin.site.register(TripFlight)