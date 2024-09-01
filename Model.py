import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib  # Import joblib for saving/loading models

# Function to generate random time in HH:MM:SS format
def generate_random_time():
    return f'{np.random.randint(0, 24):02}:{np.random.randint(0, 60):02}:{np.random.randint(0, 60):02}'

# Generate Random Data
np.random.seed(42)  # For reproducibility

num_samples = 1000

data = {
    'Battery_Capacity': np.random.uniform(50, 100, num_samples).astype(int),
    'Battery_Voltage': np.random.uniform(350, 450, num_samples).astype(int),
    'Battery_SOC': np.random.uniform(10, 100, num_samples).astype(int),
    'Battery_Temperature': np.random.uniform(20, 35, num_samples).astype(int),
    'Departure_Time': [generate_random_time() for _ in range(num_samples)],
    'Arrival_Time': [generate_random_time() for _ in range(num_samples)],
    'Distance': np.random.uniform(50, 300, num_samples).astype(int),
    'Traffic_Intensity': np.random.choice(['Low', 'Medium', 'High'], num_samples),
    'Elevation': np.random.uniform(0, 1000, num_samples).astype(int),
    'Optimal_Charging_Start': [generate_random_time() for _ in range(num_samples)],
    'Optimal_Charging_End': [generate_random_time() for _ in range(num_samples)],
    'Range': np.random.uniform(80, 250, num_samples).astype(int)
}

# Create DataFrame
df = pd.DataFrame(data)

# Convert time columns to numeric features (e.g., seconds from midnight)
def time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s

df['Departure_Time'] = df['Departure_Time'].apply(time_to_seconds)
df['Arrival_Time'] = df['Arrival_Time'].apply(time_to_seconds)
df['Optimal_Charging_Start'] = df['Optimal_Charging_Start'].apply(time_to_seconds)
df['Optimal_Charging_End'] = df['Optimal_Charging_End'].apply(time_to_seconds)

# Split data into features and target variables
X = df.drop(['Optimal_Charging_Start', 'Optimal_Charging_End', 'Range'], axis=1)
y_start = df['Optimal_Charging_Start']
y_end = df['Optimal_Charging_End']
y_range = df['Range']

# Encode categorical variables
label_encoder = LabelEncoder()
X['Traffic_Intensity'] = label_encoder.fit_transform(X['Traffic_Intensity'])

# Train-Test Split
X_train, X_test, y_train_start, y_test_start = train_test_split(X, y_start, test_size=0.2, random_state=42)
X_train, X_test, y_train_end, y_test_end = train_test_split(X, y_end, test_size=0.2, random_state=42)
X_train, X_test, y_train_range, y_test_range = train_test_split(X, y_range, test_size=0.2, random_state=42)

# Train Models
model_start = RandomForestRegressor()
model_end = RandomForestRegressor()
model_range = RandomForestRegressor()

model_start.fit(X_train, y_train_start)
model_end.fit(X_train, y_train_end)
model_range.fit(X_train, y_train_range)

# Save the trained models
joblib.dump(model_start, 'model_start.pkl')
joblib.dump(model_end, 'model_end.pkl')
joblib.dump(model_range, 'model_range.pkl')

# Make Predictions
start_predictions = model_start.predict(X_test)
end_predictions = model_end.predict(X_test)
range_predictions = model_range.predict(X_test)

# Calculate metrics for start time predictions
start_mae = mean_absolute_error(y_test_start, start_predictions)
start_mse = mean_squared_error(y_test_start, start_predictions)
start_r2 = r2_score(y_test_start, start_predictions)

# Calculate metrics for end time predictions
end_mae = mean_absolute_error(y_test_end, end_predictions)
end_mse = mean_squared_error(y_test_end, end_predictions)
end_r2 = r2_score(y_test_end, end_predictions)

# Calculate metrics for range predictions
range_mae = mean_absolute_error(y_test_range, range_predictions)
range_mse = mean_squared_error(y_test_range, range_predictions)
range_r2 = r2_score(y_test_range, range_predictions)

# Convert seconds back to HH:MM:SS for reporting
def seconds_to_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f'{h:02}:{m:02}:{s:02}'

start_predictions_time = [seconds_to_time(int(pred)) for pred in start_predictions]
end_predictions_time = [seconds_to_time(int(pred)) for pred in end_predictions]

print("Optimal Charging Start Time Predictions:", start_predictions_time[:10])  # Print first 10 for brevity
print("Optimal Charging End Time Predictions:", end_predictions_time[:10])    # Print first 10 for brevity
print("Range Predictions:", range_predictions[:10])                          # Print first 10 for brevity

print("\nModel Evaluation Metrics:")
print(f"Start Time - MAE: {start_mae:.2f}, MSE: {start_mse:.2f}, R²: {start_r2:.2f}")
print(f"End Time - MAE: {end_mae:.2f}, MSE: {end_mse:.2f}, R²: {end_r2:.2f}")
print(f"Range - MAE: {range_mae:.2f}, MSE: {range_mse:.2f}, R²: {range_r2:.2f}")
