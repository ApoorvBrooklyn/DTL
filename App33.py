import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import joblib
import pandas as pd

# Load environment variables and API keys
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_API_KEY')

# Load the ML model
model = joblib.load('ev_range_model.joblib')


def predict_range(battery_temp, current_charging, soc, battery_capacity, elevation, traffic_status, speed, wind_speed, ac_usage):
    input_data = pd.DataFrame({
        'battery_temp': [battery_temp],
        'current_charging': [current_charging],
        'soc': [soc],
        'battery_capacity': [battery_capacity],
        'elevation': [elevation],
        'traffic_status': [traffic_status],
        'speed': [speed],
        'wind_speed': [wind_speed],
        'ac_usage': [ac_usage]
    })
    input_encoded = pd.get_dummies(input_data)
    
    # Ensure all columns from training are present
    for col in model.feature_names_in_:
        if col not in input_encoded.columns:
            input_encoded[col] = 0
    
    # Reorder columns to match training data
    input_encoded = input_encoded[model.feature_names_in_]
    
    return model.predict(input_encoded)[0]

def optimal_charging_suggestion(current_soc, predicted_range, trip_distance):
    if predicted_range >= trip_distance * 1.2:  # 20% buffer
        return "No charging needed for this trip."
    elif current_soc < 20:
        return "Charge immediately to at least 50% for battery health."
    else:
        charge_needed = min((trip_distance / predicted_range) * 100, 80)
        return f"Charge to {charge_needed:.0f}% for optimal range and battery health."

def recommend_charging_point(charging_stations, current_location, destination, current_soc, battery_capacity, battery_temp, wind_speed, ac_usage):
    best_station = None
    best_score = float('-inf')
    
    for station in charging_stations:
        # Calculate distance to station
        station_location = f"{station['geometry']['location']['lat']},{station['geometry']['location']['lng']}"
        distance_to_station, _, _, _ = get_route_and_traffic(current_location, station_location)
        distance_to_station = float(distance_to_station.split()[0])  # Convert '5 km' to 5.0
        
        # Calculate remaining distance after charging
        distance_to_destination, _, _, _ = get_route_and_traffic(station_location, destination)
        distance_to_destination = float(distance_to_destination.split()[0])
        
        # Predict range after charging to 80%
        predicted_range = predict_range(battery_temp, 80, 80, battery_capacity, 0, 'Moderate', 60, wind_speed, ac_usage)
        
        # Calculate score (higher is better)
        score = predicted_range - (distance_to_station + distance_to_destination)
        
        if score > best_score:
            best_score = score
            best_station = station
    
    return best_station

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

def calculate_travel_info(source, destination, current_soc, battery_capacity, battery_temp, wind_speed, ac_usage):
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
    
    # Estimate average speed
    distance_km = float(distance.split()[0])
    duration_hours = sum(x * int(t) for x, t in zip([1, 1/60, 1/3600], duration.split()[:3]))
    avg_speed = distance_km / duration_hours if duration_hours > 0 else 60  # default to 60 km/h if calculation fails
    
    # Predict range
    predicted_range = predict_range(
        battery_temp=battery_temp,
        current_charging=current_soc,  # Assuming current_charging is the same as SOC
        soc=current_soc,
        battery_capacity=battery_capacity,
        elevation=elev_diff,
        traffic_status=traffic_updates[0]['status'],
        speed=avg_speed,
        wind_speed=wind_speed,
        ac_usage=ac_usage
    )
    
    # Get charging suggestion
    charging_suggestion = optimal_charging_suggestion(current_soc, predicted_range, distance_km)
    
    # Find EV charging stations along the route
    charging_stations = get_ev_charging_stations_along_route(waypoints)
    
    # Recommend best charging point
    best_station = recommend_charging_point(charging_stations, source, destination, current_soc, battery_capacity, battery_temp, wind_speed, ac_usage)
    
    result = f"Source: {loc1['display_name']}\n" \
             f"Coordinates: ({loc1['lat']}, {loc1['lon']})\n" \
             f"Elevation: {elev1:.2f}m\n\n" \
             f"Destination: {loc2['display_name']}\n" \
             f"Coordinates: ({loc2['lat']}, {loc2['lon']})\n" \
             f"Elevation: {elev2:.2f}m\n\n" \
             f"Elevation change: {abs(elev_diff):.2f}m ({elev_direction})\n" \
             f"Shortest travel distance: {distance}\n" \
             f"Estimated travel time: {duration}\n" \
             f"Average speed: {avg_speed:.2f} km/h\n" \
             f"Predicted range: {predicted_range:.2f} km\n" \
             f"Charging suggestion: {charging_suggestion}\n\n" \
             f"Route Details:\n"
    
    for i, step in enumerate(route_details, 1):
        result += f"{i}. {step['instruction']} ({step['distance']}, {step['duration']})\n"
    
    result += "\nTraffic Updates:\n"
    for update in traffic_updates:
        result += f"{update['segment']}: {update['status']} (ETA: {update['estimated_arrival']})\n"
    
    result += "\nRecommended Charging Point:\n"
    if best_station:
        result += f"Name: {best_station['name']}\n" \
                  f"Address: {best_station['vicinity']}\n" \
                  f"Location: {best_station['geometry']['location']['lat']}, {best_station['geometry']['location']['lng']}\n"
    else:
        result += "No suitable charging stations found along the route.\n"
    
    return result

# Get user input
source = input("Enter the source location: ")
destination = input("Enter the destination location: ")
current_soc = float(input("Enter current state of charge (%): "))
battery_capacity = float(input("Enter battery capacity (kWh): "))
battery_temp = float(input("Enter battery temperature (°C): "))
wind_speed = float(input("Enter wind speed (km/h): "))
ac_usage = int(input("Is AC in use? (1 for yes, 0 for no): "))

result = calculate_travel_info(source, destination, current_soc, battery_capacity, battery_temp, wind_speed, ac_usage)
print(result)