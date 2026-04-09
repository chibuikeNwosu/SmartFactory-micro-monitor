import smbus2
import time

# ADS1115 address
ADS1115_ADDRESS = 0x48

# Initialize I2C bus 1
bus = smbus2.SMBus(1)

def read_ads1115():
    # Write config register
    config = [0xC3, 0x83]
    bus.write_i2c_block_data(ADS1115_ADDRESS, 0x01, config)
    time.sleep(0.1)

    # Read conversion register
    data = bus.read_i2c_block_data(ADS1115_ADDRESS, 0x00, 2)
    value = (data[0] << 8) | data[1]

    # Convert to voltage
    if value > 32767:
        value -= 65536
    voltage = value * 4.096 / 32767
    return value, voltage

print("SmartFactory KY-037 Sound Sensor Test")
print("Reading noise level every 2 seconds...")
print("Press CTRL+C to stop\n")

while True:
    try:
        value, voltage = read_ads1115()
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
