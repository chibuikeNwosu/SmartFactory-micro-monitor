import time
import board 
import adafruit_dht

sensor = adafruit_dht.DHT22(board.D4)

print("SmartFactory DHT22 Sensor Test")
print("Reading temperature and humidity every 5 seconds...")
print("Press CRTL + C to stop \n")

while True: 
	try: 
		temperature = sensor.temperature
		humidity = sensor.humidity

		print(f"Temperature: {temperature:.1f}C | Humidity: {humidity:.1f}%")
	except RuntimeError as e: 
		print(f"Sensor reading failed (will retry): {e}")

	time.sleep(5)
