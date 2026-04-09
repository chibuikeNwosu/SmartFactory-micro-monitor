import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Set gain explicitly
ads.gain = 1

channel = AnalogIn(ads, 0)

print(f"Value: {channel.value}")
print(f"Voltage: {channel.voltage:.3f}V")
print("Success!")
