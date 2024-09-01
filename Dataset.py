import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

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

# Save to CSV
df.to_csv('battery_data.csv', index=False)
df.head()