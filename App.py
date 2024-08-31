import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.distance import geodesic

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

def geocode_location(geolocator, location, attempt=1, max_attempts=3):
    try:
        return geolocator.geocode(location, exactly_one=True, addressdetails=True)
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        if attempt <= max_attempts:
            print(f"Geocoding attempt {attempt} failed. Retrying...")
            return geocode_location(geolocator, location, attempt + 1, max_attempts)
        else:
            print(f"Failed to geocode after {max_attempts} attempts: {e}")
            return None

def calculate_elevation_difference(location1, location2):
    geolocator = Nominatim(user_agent="elevation_calculator")
    
    # Geocode locations
    loc1 = geocode_location(geolocator, location1)
    loc2 = geocode_location(geolocator, location2)
    
    if not loc1 or not loc2:
        return "Unable to geocode one or both locations."
    
    # Get elevations
    elev1 = get_elevation(loc1.latitude, loc1.longitude)
    elev2 = get_elevation(loc2.latitude, loc2.longitude)
    
    if elev1 is None or elev2 is None:
        return "Unable to fetch elevation data for one or both locations."
    
    # Calculate elevation difference
    elev_diff = abs(elev1 - elev2)
    
    # Calculate distance
    distance = geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).kilometers
    
    # Prepare location details
    loc1_details = f"{loc1.raw['address'].get('road', '')}, {loc1.raw['address'].get('city', '')}, {loc1.raw['address'].get('state', '')}, {loc1.raw['address'].get('country', '')}"
    loc2_details = f"{loc2.raw['address'].get('road', '')}, {loc2.raw['address'].get('city', '')}, {loc2.raw['address'].get('state', '')}, {loc2.raw['address'].get('country', '')}"
    
    return f"Location 1: {loc1_details}\n" \
           f"Coordinates: ({loc1.latitude}, {loc1.longitude})\n" \
           f"Elevation: {elev1:.2f}m\n\n" \
           f"Location 2: {loc2_details}\n" \
           f"Coordinates: ({loc2.latitude}, {loc2.longitude})\n" \
           f"Elevation: {elev2:.2f}m\n\n" \
           f"Elevation difference: {elev_diff:.2f}m\n" \
           f"Distance between locations: {distance:.2f}km"

# Example usage
location1 = "Indraprastha Nagari Apartment,Kolhapur Maharashtra"
location2 = "Central Bus Stand, Kolhapur, Maharashtra"
result = calculate_elevation_difference(location1, location2)
print(result)