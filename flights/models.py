from django.db import models

class Airport(models.Model): 
    code = models.CharField(max_length=3, unique=True) # Airport codes, e.g. LAX
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    outbound_connections = models.PositiveIntegerField(default=0)
    inbound_connections = models.PositiveIntegerField(default=0)
    
    def __str__(self): 
        return f"{self.code} - {self.name}"
    
class Route(models.Model): 
    origin = models.ForeignKey(Airport, related_name="outbound_routes", on_delete=models.CASCADE)
    destination = models.ForeignKey(Airport, related_name="inbound_routes", on_delete=models.CASCADE)
    distance = models.FloatField() # Distance in km
    
    class Meta: 
        unique_together = ('origin', 'destination')
    
    def __str__(self): 
        return f"{self.origin.code} -> {self.destination.code}"
    
class Flight(models.Model): 
    flight_number = models.CharField(max_length=10)
    origin = models.ForeignKey(Airport, related_name="departures", on_delete=models.CASCADE)
    destination = models.ForeignKey(Airport, related_name="arrivals", on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    
    class Statuses(models.TextChoices): 
        scheduled = "SCH", "Scheduled"
        enroute = "ENR", "Enroute"
        delayed = "DEL", "Delayed"
        landed = "LAN", "Landed"
        
    status = models.CharField(max_length=3, choices=Statuses.choices)
    
    def __str__(self): 
        return f"{self.flight_number}: {self.origin.code} -> {self.destination.code}"
    
class Trip(models.Model): 
    origin = models.ForeignKey(Airport, related_name="trip_origin", on_delete=models.CASCADE)
    destination = models.ForeignKey(Airport, related_name="trip_destination", on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Trip from {self.origin.code} to {self.destination.code} at {self.departure_time.isoformat()}"
    
class TripFlight(models.Model):
    trip = models.ForeignKey(Trip, related_name="flights", on_delete=models.CASCADE)
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.trip} includes {self.flight}"
