from django.core.management.base import BaseCommand

from flights.models import Route, Airport

import csv
from collections import defaultdict
from math import radians, cos, sin, sqrt, atan2

class Command(BaseCommand): 
    help = "Loads route data into the Route model"
    
    def haversine(self, lat1, lon1, lat2, lon2): 
        """
        Computes great-circle distance between two points using the Haversine formula.
        Inputs are in degrees. Output is in kilometers.
        """
        
        R = 6371 # Radius of Earth in km
        
        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        
        # Haversine formula
        a = sin(delta_lat / 2)**2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def handle(self, *args, **kwargs):
        route_objs = []
        skipped = 0
        duplicates = 0
        outbound_counts = defaultdict(int)
        inbound_counts = defaultdict(int)
        
        with open("data/routes.dat", encoding="utf-8") as f:
            reader = csv.reader(f)
            
            for row in reader:
                try:
                    source_code = row[2].strip().upper()
                    dest_code = row[4].strip().upper()

                    # Skip missing airport codes
                    if source_code == "\\N" or dest_code == "\\N":
                        skipped += 1
                        continue

                    try:
                        origin = Airport.objects.get(code=source_code)
                        destination = Airport.objects.get(code=dest_code)
                    except Airport.DoesNotExist:
                        skipped += 1
                        continue

                    # Calculate distance between airports
                    distance = self.haversine(
                        origin.latitude, origin.longitude,
                        destination.latitude, destination.longitude
                    )

                    # Check for duplicate before adding
                    if Route.objects.filter(origin=origin, destination=destination).exists():
                        duplicates += 1
                        continue

                    route_objs.append(
                        Route(origin=origin, destination=destination, distance=distance)
                    )
                    
                    outbound_counts[origin.code] += 1
                    inbound_counts[destination.code] += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing row: {row}"))
                    self.stdout.write(self.style.ERROR(str(e)))
                    skipped += 1

        # Bulk create all Route objects at once
        Route.objects.all().delete()
        Route.objects.bulk_create(route_objs)
        
        # Update airports with connection counts
        airports = Airport.objects.all()
        for airport in airports:
            airport.outbound_connections = outbound_counts[airport.code]
            airport.inbound_connections = inbound_counts[airport.code]
        Airport.objects.bulk_update(airports, ['outbound_connections', 'inbound_connections'])

        self.stdout.write(self.style.SUCCESS(f"Routes created: {len(route_objs)}"))
        self.stdout.write(self.style.WARNING(f"Routes skipped (invalid/missing): {skipped}"))
        self.stdout.write(self.style.WARNING(f"Routes skipped (duplicates): {duplicates}"))