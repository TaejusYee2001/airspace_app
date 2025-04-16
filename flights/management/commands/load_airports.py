from django.core.management.base import BaseCommand

from flights.models import Airport

import csv

class Command(BaseCommand): 
    help = "Loads airport data into the Airport model"
    
    def handle(self, *args, **kwargs): 
        with open("data/airports.dat", encoding="utf-8") as f: 
            reader = csv.reader(f)
            airports = []

            for row in reader:
                code = row[4]
                if code == "\\N" or len(code) != 3:
                    continue
                name = row[1]
                lat = float(row[6])
                lon = float(row[7])

                airports.append(
                    Airport(
                        code=code,
                        name=name,
                        latitude=lat,
                        longitude=lon,
                    )
                )
                
            Airport.objects.all().delete()
            Airport.objects.bulk_create(airports)
                
        self.stdout.write(self.style.SUCCESS(f"Imported {len(airports)} airports in bulk"))