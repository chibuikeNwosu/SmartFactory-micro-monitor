import time
import busio
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Initialize I2C using hardware I2C bus 1
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Channel 0 = where KY-037 AO is connected
channel = AnalogIn(ads, 0)

print("SmartFactory KY-037 Sound Sensor Test")
print("Reading noise level every 2 seconds...")
print("Press CTRL+C to stop\n")

while True:
    try:
        value = channel.value
        voltage = channel.voltage
        print(f"Raw Value: {value} | Voltage: {voltage:.3f}V")

        if voltage < 0.5:
            print("Noise Level: QUIET")
        elif voltage < 1.5:
            print("Noise Level: MODERATE")
        else:
            print("Noise Level: LOUD")

    except KeyboardInterrupt:
        print("\nTest stopped. Goodbye!")
        break

    except Exception as e:
        print(f"Reading failed: {e}")

    time.sleep(2)
