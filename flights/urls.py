from django.urls import path
from flights import views

urlpatterns = [
    path("api/globe-data/", views.globe_data, name="globe-data"),
    path("api/airport/<str:code>/", views.airport_detail, name="airport-detail"),
    path("api/compute_trip/", views.compute_trip, name="compute-trip"),
    path("api/trips/", views.trip_list, name="trip-list"), 
    path("api/trips/<int:trip_id>/", views.trip_detail, name="trip-detail"),
]