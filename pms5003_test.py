import time 
from pms5003 import PMS5003

pms5003 = PMS5003(device='/dev/ttyS0')

print("SmartFactory PMS5003 Dust Sensor Test")
print("Reading air quality every 5 seconds...")
print("Press CTRL+C to stop\n")


try:
    data = pms5003.read()
    print(f"PM1.0: {data.pm_ug_per_m3(1.0)} ug/m3")
    print(f"PM2.5: {data.pm_ug_per_m3(2.5)} ug/m3")
    print(f"PM10:  {data.pm_ug_per_m3(10.0)} ug/m3")
except Exception as e:
    print(f"Reading failed: {e}")
