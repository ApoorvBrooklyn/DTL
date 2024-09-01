import serial
import time

# Replace 'COM3' with your port, which is '/dev/ttyACM0'
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1)

def get_temperature():
    data = arduino.readline().decode('utf-8').strip()  # Read and decode serial data
    if data:
        try:
            temperature = float(data)
            return temperature
        except ValueError:
            print("Invalid data received:", data)
            return None

while True:
    temperature = get_temperature()
    if temperature is not None:
        print(f"Temperature: {temperature} °C")
    time.sleep(2)
