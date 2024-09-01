#include <DHT.h>

#define DHTPIN 2       // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11  // DHT 11 

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float temperature = dht.readTemperature();
  
  if (isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  
  Serial.println(temperature);
  delay(2000); // Send data every 2 seconds
}
