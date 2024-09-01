import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Generate synthetic dataset
np.random.seed(42)
n_samples = 10000

data = {
    'battery_temp': np.random.uniform(0, 40, n_samples),
    'current_charging': np.random.uniform(0, 100, n_samples),
    'soc': np.random.uniform(0, 100, n_samples),
    'battery_capacity': np.random.uniform(50, 100, n_samples),
    'elevation': np.random.uniform(-100, 1000, n_samples),
    'traffic_status': np.random.choice(['Light', 'Moderate', 'Heavy'], n_samples),
    'speed': np.random.uniform(0, 120, n_samples),
    'wind_speed': np.random.uniform(0, 30, n_samples),
    'ac_usage': np.random.choice([0, 1], n_samples)
}

df = pd.DataFrame(data)

# Calculate range based on factors
df['range'] = (
    df['battery_capacity'] * 5  # Base range
    - df['battery_temp'] * 0.5  # Temperature impact
    - (df['elevation'].clip(lower=0) * 0.02)  # Elevation impact (only for positive elevation)
    - (df['speed'] ** 2 * 0.001)  # Speed impact
    - (df['wind_speed'] * 0.5)  # Wind impact
    - (df['ac_usage'] * 10)  # AC usage impact
)

# Traffic impact
traffic_impact = {'Light': 1, 'Moderate': 0.9, 'Heavy': 0.7}
df['range'] *= df['traffic_status'].map(traffic_impact)

# Ensure range is always positive
df['range'] = df['range'].clip(lower=0)

# Split data
X = df.drop('range', axis=1)
y = df['range']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# One-hot encode categorical variables
X_train_encoded = pd.get_dummies(X_train)
X_test_encoded = pd.get_dummies(X_test)

# Train Random Forest model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train_encoded, y_train)

# Make predictions
y_pred = rf_model.predict(X_test_encoded)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse}")
print(f"R-squared Score: {r2}")

# Function to predict range
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
    for col in X_train_encoded.columns:
        if col not in input_encoded.columns:
            input_encoded[col] = 0
    
    # Reorder columns to match training data
    input_encoded = input_encoded[X_train_encoded.columns]
    
    return rf_model.predict(input_encoded)[0]

# Example prediction
print(predict_range(25, 50, 80, 75, 100, 'Moderate', 60, 10, 1))

# Feature importance
feature_importance = pd.DataFrame({'feature': X_train_encoded.columns, 'importance': rf_model.feature_importances_})
print(feature_importance.sort_values('importance', ascending=False).head(10))


# Save the model
joblib.dump(rf_model, 'ev_range_model.joblib')

# Function to load the model
def load_model():
    return joblib.load('ev_range_model.joblib')

# Function to predict range
def predict_range(model, battery_temp, current_charging, soc, battery_capacity, elevation, traffic_status, speed, wind_speed, ac_usage):
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
    for col in X_train_encoded.columns:
        if col not in input_encoded.columns:
            input_encoded[col] = 0
    
    # Reorder columns to match training data
    input_encoded = input_encoded[X_train_encoded.columns]
    
    return model.predict(input_encoded)[0]

# Function to suggest optimal charging
def optimal_charging_suggestion(current_soc, predicted_range, trip_distance):
    if predicted_range >= trip_distance * 1.2:  # 20% buffer
        return "No charging needed for this trip."
    elif current_soc < 20:
        return "Charge immediately to at least 50% for battery health."
    else:
        charge_needed = min((trip_distance / predicted_range) * 100, 80)
        return f"Charge to {charge_needed:.0f}% for optimal range and battery health."

# Example usage
if __name__ == "__main__":
    model = load_model()
    print(predict_range(model, 25, 50, 80, 75, 100, 'Moderate', 60, 10, 1))
    print(optimal_charging_suggestion(30, 200, 180))