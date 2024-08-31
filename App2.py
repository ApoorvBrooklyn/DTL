import requests
import json
from geopy.distance import geodesic
import os

# Replace with your actual Google Maps API key
GOOGLE_MAPS_API_KEY = "AIzaSyBgE59yFelBI4VhtmV8HLP34MzT4tPr6mw"

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

def geocode_osm(location):
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
    headers = {'User-Agent': 'ElevationCalculator/1.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
    except requests.RequestException as e:
        print(f"Error with OSM geocoding: {e}")
    return None

def geocode_google(location):
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

def geocode_location(location):
    result = geocode_osm(location)
    if result is None:
        print(f"OSM geocoding failed for {location}, trying Google Maps...")
        result = geocode_google(location)
    return result

def calculate_elevation_difference(location1, location2):
    loc1 = geocode_location(location1)
    loc2 = geocode_location(location2)
    
    if not loc1 or not loc2:
        return "Unable to geocode one or both locations."
    
    elev1 = get_elevation(loc1['lat'], loc1['lon'])
    elev2 = get_elevation(loc2['lat'], loc2['lon'])
    
    if elev1 is None or elev2 is None:
        return "Unable to fetch elevation data for one or both locations."
    
    elev_diff = abs(elev1 - elev2)
    distance = geodesic((loc1['lat'], loc1['lon']), (loc2['lat'], loc2['lon'])).kilometers
    
    return f"Location 1: {loc1['display_name']}\n" \
           f"Coordinates: ({loc1['lat']}, {loc1['lon']})\n" \
           f"Elevation: {elev1:.2f}m\n\n" \
           f"Location 2: {loc2['display_name']}\n" \
           f"Coordinates: ({loc2['lat']}, {loc2['lon']})\n" \
           f"Elevation: {elev2:.2f}m\n\n" \
           f"Elevation difference: {elev_diff:.2f}m\n" \
           f"Distance between locations: {distance:.2f}km"

# Example usage
location1 = "Indraprastha Nagari Apartment, Mohite Colony, Salokhe Nagar, Kolhapur, Maharashtra"
location2 = "Majestic, Bengaluru"
result = calculate_elevation_difference(location1, location2)
print(result)