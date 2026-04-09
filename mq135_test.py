import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Initialize I2C and ADS1115

i2c = busio.I2C(board.D3, board.D2)
ads = ADS.ADS1115(i2c)
channel = AnalogIn(ads, 0)

print("SmartFactory MQ-135 Air Quality Test")
print("Reading air quality every 5 seconds...")
print("Press CTRL+C to stop\n")

while True:
    try:
        value = channel.value
        voltage = channel.voltage
        print(f"Raw Value: {value} | Voltage: {voltage:.3f}V")

        # Basic air quality interpretation
        if voltage < 1.0:
            print("Air Quality: GOOD ")
        elif voltage < 2.0:
            print("Air Quality: MODERATE ")
        else:
            print("Air Quality: POOR ")

    except KeyboardInterrupt:
        print("\nTest stopped by user. Goodbye!")
        break

    except Exception as e:
        print(f"Reading failed: {e}")

    time.sleep(5)
