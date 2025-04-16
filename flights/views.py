from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, make_aware, is_naive, get_current_timezone, localtime
from django.core.cache import cache

from flights.models import Airport, Route, Flight, Trip, TripFlight
from flights.utils.routing import a_star_routing

import random
import json
import heapq
from datetime import timedelta
from collections import defaultdict

def trip_list(request):
    trips = Trip.objects.select_related('origin', 'destination').order_by('-created_at')[:20]  # Limit to 20 most recent trips
    
    result = []
    for trip in trips:
        # Get first and last flight for arrival time
        first_flight = TripFlight.objects.filter(trip=trip).order_by('flight__departure_time').first()
        last_flight = TripFlight.objects.filter(trip=trip).order_by('flight__arrival_time').last()
        
        if first_flight and last_flight:
            result.append({
                "id": trip.id,
                "origin_code": trip.origin.code,
                "origin_name": trip.origin.name,
                "destination_code": trip.destination.code,
                "destination_name": trip.destination.name,
                "departure_time": first_flight.flight.departure_time.isoformat(),
                "arrival_time": last_flight.flight.arrival_time.isoformat(),
                "num_flights": TripFlight.objects.filter(trip=trip).count()
            })
    
    return JsonResponse({"trips": result})

def trip_detail(request, trip_id): 
    try:
        trip = Trip.objects.select_related('origin', 'destination').get(id=trip_id)
    except Trip.DoesNotExist:
        return HttpResponseNotFound("Trip not found")
    
    # Get all flights in this trip
    trip_flights = TripFlight.objects.filter(trip=trip).select_related(
        'flight', 'flight__origin', 'flight__destination'
    ).order_by('flight__departure_time')
    
    flights = []
    route_segments = []
    
    for trip_flight in trip_flights:
        flight = trip_flight.flight
        
        flights.append({
            "flight_number": flight.flight_number,
            "origin_code": flight.origin.code,
            "origin_name": flight.origin.name,
            "destination_code": flight.destination.code,
            "destination_name": flight.destination.name,
            "departure_time": flight.departure_time.isoformat(),
            "arrival_time": flight.arrival_time.isoformat(),
            "status": flight.get_status_display()
        })
        
        # Add route segment for highlighting on the globe
        route_segments.append({
            "source": flight.origin.code,
            "target": flight.destination.code
        })
    
    result = {
        "id": trip.id,
        "origin_code": trip.origin.code,
        "origin_name": trip.origin.name,
        "destination_code": trip.destination.code,
        "destination_name": trip.destination.name,
        "departure_time": trip.departure_time.isoformat(),
        "flights": flights,
        "route_segments": route_segments
    }
    
    return JsonResponse(result)

def airport_detail(request, code): 
    try: 
        airport = Airport.objects.get(code=code.upper())
    except Airport.DoesNotExist: 
        return HttpResponseNotFound("Airport not found")
    
    upcoming_departures = Flight.objects.filter(origin=airport).order_by("departure_time")[:5]
    upcoming_arrivals = Flight.objects.filter(destination=airport).order_by("arrival_time")[:5]

    def flight_to_dict(flight):
        return {
            "flight_number": flight.flight_number,
            "origin": flight.origin.code,
            "destination": flight.destination.code,
            "departure_time": flight.departure_time.isoformat(),
            "arrival_time": flight.arrival_time.isoformat(),
            "status": flight.get_status_display()
        }

    return JsonResponse({
        "code": airport.code,
        "name": airport.name,
        "latitude": airport.latitude,
        "longitude": airport.longitude,
        "outbound_connections": airport.outbound_connections,
        "inbound_connections": airport.inbound_connections,
        "departures": [flight_to_dict(f) for f in upcoming_departures],
        "arrivals": [flight_to_dict(f) for f in upcoming_arrivals],
    })
        
@csrf_exempt
def compute_trip(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
        start_code = data["origin_id"].upper()
        destination_code = data["destination_id"].upper()
        departure_time = parse_datetime(data["departure_time"])

        try:
            origin = Airport.objects.get(code=start_code)
            destination = Airport.objects.get(code=destination_code)
        except Airport.DoesNotExist:
            return JsonResponse({"error": "Invalid airport code"}, status=404)
        
        globe_data_cache = cache.get('globe_data')
        if not globe_data_cache:
            return JsonResponse({"error": "Globe data not available"}, status=500)
        
        graph = defaultdict(list)
        airports_cache = {}
        
        for node in globe_data_cache['nodes']:
            airports_cache[node['id']] = {
                'code': node['id'],
                'latitude': node['lat'],
                'longitude': node['lon']
            }
        
        for link in globe_data_cache['links']:
            source = link['source']
            target = link['target']
            distance = link['distance']
            
            graph[source].append((target, distance))
            graph[target].append((source, distance))
        
        # Use our custom A* function with cached data
        path = a_star_routing(origin.code, destination.code, graph, airports_cache)
        
        if not path or len(path) < 2:
            return JsonResponse({"error": "No route found"}, status=404)
        
        departure_time = parse_datetime(data["departure_time"])
        if is_naive(departure_time):
            departure_time = make_aware(departure_time)
        departure_time = localtime(departure_time)
        trip = Trip.objects.create(origin=origin, destination=destination, departure_time=departure_time)
        
        flights_created = []
        time_cursor = departure_time
        
        for i in range(len(path) - 1):
            segment_origin_code = path[i]
            segment_destination_code = path[i + 1]
            
            segment_origin = Airport.objects.get(code=segment_origin_code)
            segment_destination = Airport.objects.get(code=segment_destination_code)
            
            distance = next((dist for neighbor, dist in graph[segment_origin_code] 
                           if neighbor == segment_destination_code), None)
            
            if distance is None:
                route = Route.objects.filter(
                    origin=segment_origin, 
                    destination=segment_destination
                ).order_by('distance').first()
                
                if route is None:
                    return JsonResponse({"error": f"No route found between {segment_origin_code} and {segment_destination_code}"}, status=404)
                
                distance = route.distance
            
            # Calculate flight time based on distance
            flight_duration = timedelta(hours=distance / 800)  # Assuming 800km/hr flight speed
            arrival_time = time_cursor + flight_duration
            
            if is_naive(time_cursor):
                time_cursor = make_aware(time_cursor)
            if is_naive(arrival_time):
                arrival_time = make_aware(arrival_time)

            time_cursor = localtime(time_cursor)
            arrival_time = localtime(arrival_time)

            flight = Flight.objects.create(
                flight_number="AS" + str(random.randint(1000, 9999)),
                origin=segment_origin,
                destination=segment_destination,
                departure_time=time_cursor,
                arrival_time=arrival_time,
                status=Flight.Statuses.scheduled
            )

            TripFlight.objects.create(trip=trip, flight=flight)
            flights_created.append({
                "flight_number": flight.flight_number,
                "origin": segment_origin.code,
                "destination": segment_destination.code,
                "departure_time": flight.departure_time.isoformat(),
                "arrival_time": flight.arrival_time.isoformat()
            })

            time_cursor = arrival_time + timedelta(minutes=30)  # Assume 30 min layover

        return JsonResponse({
            "trip_id": trip.id,
            "route": flights_created,
            "total_duration_minutes": (time_cursor - departure_time).total_seconds() / 60
        })

    except KeyError as e:
        return JsonResponse({"error": f"Missing parameter: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def globe_data(request): 
    # Limited dataset for development
    N = 800
    
    # Good seed for graph
    random.seed(31)
    
    route_ids = list(Route.objects.values_list("id", flat=True))
    sampled_ids = random.sample(route_ids, N)

    routes = Route.objects.filter(id__in=sampled_ids)

    airport_codes = set()
    for route in routes:
        airport_codes.add(route.origin.code)
        airport_codes.add(route.destination.code)

    airports = Airport.objects.filter(code__in=airport_codes)
    
    nodes = [
        {
            "id": airport.code, 
            "name": airport.name, 
            "lat": airport.latitude, 
            "lon": airport.longitude
        } for airport in airports
    ]
    
    links = [
        {
            "source": route.origin.code, 
            "target": route.destination.code,
            "distance": route.distance
        } for route in routes
    ]
    
    globe_data = {"nodes": nodes, "links": links}
    cache.set('globe_data', globe_data, timeout=3600)
    
    return JsonResponse(globe_data)



