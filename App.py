import requests

# Function to get latitude and longitude from a place name
def get_coordinates(place_name, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name}&key={api_key}"
    response = requests.get(url)
    result = response.json()

    if result['status'] == 'OK':
        location = result['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        raise Exception(f"Error fetching coordinates: {result['status']}")

# Function to get elevation data for a given latitude and longitude
def get_elevation(lat, lon, api_key):
    url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lon}&key={api_key}"
    response = requests.get(url)
    result = response.json()

    if result['status'] == 'OK':
        elevation = result['results'][0]['elevation']
        return elevAPIsation
    else:
        raise Exception(f"Error fetching elevation data: {result['status']}")

# Function to calculate elevation difference between two places
def calculate_elevation_difference(place1, place2, api_key):
    lat1, lon1 = get_coordinates(place1, api_key)
    lat2, lon2 = get_coordinates(place2, api_key)
    
    elevation1 = get_elevation(lat1, lon1, api_key)
    elevation2 = get_elevation(lat2, lon2, api_key)
    
    elevation_difference = elevation2 - elevation1
    return elevation_difference

# Example usage
if __name__ == "__main__":
    # Replace with your own API key
    API_KEY = ""
    
    # Enter the names of the two places
    place1 = "San Francisco, CA"
    place2 = "Los Angeles, CA"
    
    elevation_difference = calculate_elevation_difference(place1, place2, API_KEY)
    print(f"Elevation difference between {place1} and {place2}: {elevation_difference:.2f} meters")
