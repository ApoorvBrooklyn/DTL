import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Replace with your actual Google Maps API key
load_dotenv()

# Access the API keys
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_API_KEY')

def get_elevation(lat, lon):
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['results'][0]['elevation']
    except requests.RequestException as e:
        print(f"Error fetching elevation data: {e}")
        return None

def geocode_location(location):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            result = data['results'][0]
            return {
                'lat': result['geometry']['location']['lat'],
                'lon': result['geometry']['location']['lng'],
                'display_name': result['formatted_address']
            }
    except requests.RequestException as e:
        print(f"Error with Google geocoding: {e}")
    return None

def get_route_and_traffic(origin, destination):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={GOOGLE_MAPS_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            route = data['routes'][0]
            distance = route['legs'][0]['distance']['text']
            duration = route['legs'][0]['duration']['text']
            steps = route['legs'][0]['steps']
            
            route_details = []
            for step in steps:
                route_details.append({
                    'instruction': step['html_instructions'],
                    'distance': step['distance']['text'],
                    'duration': step['duration']['text']
                })
            
            waypoints = [f"{step['start_location']['lat']},{step['start_location']['lng']}" for step in steps]
            waypoints.append(f"{steps[-1]['end_location']['lat']},{steps[-1]['end_location']['lng']}")
            
            return distance, duration, route_details, waypoints
    except requests.RequestException as e:
        print(f"Error fetching route data: {e}")
    return None, None, None, None

def get_traffic_updates(waypoints):
    traffic_updates = []
    current_time = datetime.now()
    
    for i, waypoint in enumerate(waypoints[:-1]):
        next_waypoint = waypoints[i + 1]
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={waypoint}&destinations={next_waypoint}&departure_time=now&key={GOOGLE_MAPS_API_KEY}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                duration_in_traffic = element['duration_in_traffic']['value']
                normal_duration = element['duration']['value']
                
                traffic_ratio = duration_in_traffic / normal_duration
                if traffic_ratio > 1.5:
                    traffic_status = "Heavy traffic"
                elif traffic_ratio > 1.2:
                    traffic_status = "Moderate traffic"
                else:
                    traffic_status = "Light traffic"
                
                estimated_arrival = current_time + timedelta(seconds=duration_in_traffic)
                
                traffic_updates.append({
                    'segment': f"Segment {i+1}",
                    'status': traffic_status,
                    'estimated_arrival': estimated_arrival.strftime("%H:%M:%S")
                })
                
                current_time = estimated_arrival
        
        except requests.RequestException as e:
            print(f"Error fetching traffic data: {e}")
    
    return traffic_updates

def get_nearby_ev_charging_stations(location, radius=5000):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location['lat']},{location['lon']}&radius={radius}&type=charging_station&key={GOOGLE_MAPS_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            return data['results']
    except requests.RequestException as e:
        print(f"Error fetching EV charging station data: {e}")
    return []

def get_ev_charging_stations_along_route(waypoints, radius=5000):
    charging_stations = []
    for waypoint in waypoints:
        location = {'lat': waypoint.split(',')[0], 'lon': waypoint.split(',')[1]}
        stations_near_waypoint = get_nearby_ev_charging_stations(location, radius)
        charging_stations.extend(stations_near_waypoint)
    return charging_stations

def calculate_travel_info(source, destination):
    loc1 = geocode_location(source)
    loc2 = geocode_location(destination)
    
    if not loc1 or not loc2:
        return "Unable to geocode source or destination."
    
    elev1 = get_elevation(loc1['lat'], loc1['lon'])
    elev2 = get_elevation(loc2['lat'], loc2['lon'])
    
    if elev1 is None or elev2 is None:
        return "Unable to fetch elevation data for source or destination."
    
    elev_diff = elev2 - elev1
    elev_direction = "positive" if elev_diff > 0 else "negative" if elev_diff < 0 else "no"
    
    distance, duration, route_details, waypoints = get_route_and_traffic(source, destination)
    
    if not distance or not duration or not route_details or not waypoints:
        return "Unable to fetch route information."
    
    traffic_updates = get_traffic_updates(waypoints)
    
    # Find EV charging stations along the route
    charging_stations = get_ev_charging_stations_along_route(waypoints)
    
    result = f"Source: {loc1['display_name']}\n" \
             f"Coordinates: ({loc1['lat']}, {loc1['lon']})\n" \
             f"Elevation: {elev1:.2f}m\n\n" \
             f"Destination: {loc2['display_name']}\n" \
             f"Coordinates: ({loc2['lat']}, {loc2['lon']})\n" \
             f"Elevation: {elev2:.2f}m\n\n" \
             f"Elevation change: {abs(elev_diff):.2f}m ({elev_direction})\n" \
             f"Shortest travel distance: {distance}\n" \
             f"Estimated travel time: {duration}\n\n" \
             f"Route Details:\n"
    
    for i, step in enumerate(route_details, 1):
        result += f"{i}. {step['instruction']} ({step['distance']}, {step['duration']})\n"
    
    result += "\nTraffic Updates:\n"
    for update in traffic_updates:
        result += f"{update['segment']}: {update['status']} (ETA: {update['estimated_arrival']})\n"
    
    result += "\nEV Charging Stations Along Route:\n"
    if charging_stations:
        for station in charging_stations:
            result += f"- {station['name']} at {station['vicinity']}\n"
    else:
        result += "No EV charging stations found along the route.\n"
    
    return result

# Get user input
source = input("Enter the source location: ")
destination = input("Enter the destination location: ")

result = calculate_travel_info(source, destination)
print(result)