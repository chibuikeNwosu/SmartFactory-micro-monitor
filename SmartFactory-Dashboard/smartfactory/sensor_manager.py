# ================================================================
# SmartFactory Micro-Monitor — Sensor Manager
# File: sensor_manager.py
#
# Purpose:
# The core daemon of the SmartFactory system. Runs continuously,
# polling all sensors every 60 seconds, saving readings to the
# database, and evaluating thresholds to trigger alerts.
#
# This is the heartbeat of the entire system.
#
# Sensors managed:
#   DHT22    → Temperature and Humidity (GPIO Pin 7)
#   MQ-135   → Air Quality via ADS1115 ADC (I2C)
#   KY-037   → Noise Level via ADS1115 ADC (I2C)
#   PMS5003  → Dust Particles via UART (/dev/serial0)
#   SCT-013  → Energy via ADS1115 ADC (I2C) [optional]
#
# Usage:
#   python sensor_manager.py
# ================================================================

import time
import board
import busio
import smbus2
import adafruit_dht
from pms5003 import PMS5003
from database import init_db, save_reading
from threshold_engine import setup_gpio, cleanup_gpio, evaluate_reading

# ── SENSOR CONFIGURATION ─────────────────────────────────────────

# How often to poll sensors in seconds
POLL_INTERVAL = 60

# ADS1115 I2C address (confirmed via i2cdetect -y 1)
ADS1115_ADDRESS = 0x48

# PMS5003 serial port (primary UART after Bluetooth disabled)
PMS5003_PORT = '/dev/serial0'

# MQ-135 on ADS1115 Channel 0
# KY-037  on ADS1115 Channel 1
ADS_MQ135_CHANNEL = 0
ADS_KY037_CHANNEL = 1


# ── SENSOR INITIALISATION ────────────────────────────────────────

def init_sensors():
    """
    Initialises all sensor connections.

    Returns:
        tuple: (dht_sensor, i2c_bus, pms_sensor)
    """
    print("Initialising sensors...")

    # DHT22 on GPIO Pin 4 (Physical Pin 7)
    dht_sensor = adafruit_dht.DHT22(board.D4)
    print("  DHT22     → ready")

    # I2C bus for ADS1115
    i2c_bus = smbus2.SMBus(1)
    print("  ADS1115   → ready (address 0x48)")

    # PMS5003 via UART
    pms_sensor = PMS5003(device=PMS5003_PORT)
    print("  PMS5003   → ready")

    print("All sensors initialised\n")
    return dht_sensor, i2c_bus, pms_sensor


# ── SENSOR READ FUNCTIONS ────────────────────────────────────────

def read_dht22(sensor):
    """
    Reads temperature and humidity from the DHT22 sensor.

    Args:
        sensor: Adafruit DHT22 sensor object

    Returns:
        tuple: (temperature_celsius, humidity_percent)
                Returns (None, None) on failure.
    """
    try:
        temperature = sensor.temperature
        humidity    = sensor.humidity
        return temperature, humidity
    except RuntimeError as e:
        # DHT sensors occasionally miss a reading — normal behaviour
        print(f"  DHT22 read error (will retry next cycle): {e}")
        return None, None


def read_ads1115_channel(bus, channel=0):
    """
    Reads a voltage from a specific ADS1115 channel using smbus2.

    Uses direct I2C register writes to configure the ADS1115
    for single-shot conversion on the specified channel.

    Note: The Adafruit ADS1x15 library produced Remote I/O errors
    on this Pi setup. smbus2 direct register access is more reliable.

    Args:
        bus (smbus2.SMBus): Open I2C bus
        channel (int): ADC channel 0-3. Default 0.

    Returns:
        tuple: (raw_value, voltage) or (None, None) on failure
    """
    try:
        # Build config register value for single-shot conversion
        # Bits 14-12: MUX — select channel (0=AIN0, 1=AIN1, etc.)
        mux_settings = {0: 0xC3, 1: 0xD3, 2: 0xE3, 3: 0xF3}
        config_msb = mux_settings.get(channel, 0xC3)

        # Write config register to start conversion
        bus.write_i2c_block_data(ADS1115_ADDRESS, 0x01, [config_msb, 0x83])
        time.sleep(0.1)  # Wait for conversion to complete

        # Read conversion result register
        data = bus.read_i2c_block_data(ADS1115_ADDRESS, 0x00, 2)
        value = (data[0] << 8) | data[1]

        # Convert from two's complement
        if value > 32767:
            value -= 65536

        # Convert raw value to voltage (±4.096V range)
        voltage = value * 4.096 / 32767

        return value, voltage

    except Exception as e:
        print(f"  ADS1115 channel {channel} error: {e}")
        return None, None


def read_pms5003(sensor):
    """
    Reads particulate matter levels from the PMS5003 sensor.

    Args:
        sensor: PMS5003 sensor object

    Returns:
        tuple: (pm1, pm25, pm10) in μg/m³
                Returns (None, None, None) on failure.
    """
    try:
        data = sensor.read()
        pm1  = data.pm_ug_per_m3(1.0)
        pm25 = data.pm_ug_per_m3(2.5)
        pm10 = data.pm_ug_per_m3(10.0)
        return pm1, pm25, pm10
    except Exception as e:
        print(f"  PMS5003 read error: {e}")
        return None, None, None


# ── READING INTERPRETER ──────────────────────────────────────────

def interpret(sensor, value):
    """
    Returns a plain English status label for a reading.

    Args:
        sensor (str): Sensor key
        value (float): Reading value

    Returns:
        str: Human readable status
    """
    if value is None:
        return "NO DATA"

    interpretations = {
        'air_quality': [
            (1.0,  "GOOD"),
            (2.0,  "MODERATE"),
            (999,  "POOR"),
        ],
        'noise': [
            (0.18, "QUIET"),
            (0.25, "MODERATE"),
            (999,  "LOUD"),
        ],
        'pm25': [
            (12,   "GOOD"),
            (35,   "MODERATE"),
            (999,  "POOR"),
        ],
    }

    levels = interpretations.get(sensor)
    if not levels:
        return str(value)

    for threshold, label in levels:
        if value < threshold:
            return label
    return levels[-1][1]


# ── MAIN POLLING LOOP ────────────────────────────────────────────

def run():
    """
    Main entry point. Initialises everything and runs the
    continuous sensor polling loop.

    Runs indefinitely until CTRL+C or system shutdown.
    """
    print("\n" + "=" * 52)
    print("  SmartFactory Micro-Monitor")
    print("  Environmental Compliance Station")
    print("  Raspberry Pi 3B — Sensor Manager")
    print("=" * 52)
    print(f"\nPolling all sensors every {POLL_INTERVAL} seconds")
    print("Press CTRL+C to stop\n")

    # Initialise database tables
    init_db()

    # Initialise GPIO pins for LED and buzzer
    setup_gpio()

    # Initialise all sensors
    dht_sensor, i2c_bus, pms_sensor = init_sensors()

    reading_count = 0

    try:
        while True:
            reading_count += 1

            print("\n" + "─" * 52)
            print(f"  Reading #{reading_count} — {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("─" * 52)

            # ── Read all sensors ─────────────────────────────────
            temperature, humidity = read_dht22(dht_sensor)
            air_raw, air_voltage  = read_ads1115_channel(i2c_bus, ADS_MQ135_CHANNEL)
            noise_raw, noise_voltage = read_ads1115_channel(i2c_bus, ADS_KY037_CHANNEL)
            pm1, pm25, pm10       = read_pms5003(pms_sensor)

            # Energy reading (SCT-013 on channel 2 when available)
            # Returns None if not connected
            energy_raw, energy_voltage = read_ads1115_channel(i2c_bus, 2)
            energy_watts = (energy_voltage * 30.0 * 1000) if energy_voltage else None

            # ── Display readings ──────────────────────────────────
            print(f"  🌡️  Temperature : {temperature}°C" if temperature else "  🌡️  Temperature : NO DATA")
            print(f"  💧  Humidity    : {humidity}%"     if humidity    else "  💧  Humidity    : NO DATA")
            print(f"  💨  Air Quality : {air_voltage:.3f}V → {interpret('air_quality', air_voltage)}" if air_voltage else "  💨  Air Quality : NO DATA")
            print(f"  🔊  Noise Level : {noise_voltage:.3f}V → {interpret('noise', noise_voltage)}"   if noise_voltage else "  🔊  Noise Level : NO DATA")
            print(f"  🌫️  PM1.0       : {pm1} μg/m³"    if pm1  else "  🌫️  PM1.0       : NO DATA")
            print(f"  🌫️  PM2.5       : {pm25} μg/m³ → {interpret('pm25', pm25)}" if pm25 else "  🌫️  PM2.5       : NO DATA")
            print(f"  🌫️  PM10        : {pm10} μg/m³"   if pm10 else "  🌫️  PM10        : NO DATA")
            print(f"  ⚡  Energy      : {energy_watts:.0f}W" if energy_watts else "  ⚡  Energy      : NOT CONNECTED")

            # ── Save to database ──────────────────────────────────
            save_reading(
                temperature=temperature,
                humidity=humidity,
                air_quality_voltage=air_voltage,
                noise_voltage=noise_voltage,
                pm1=pm1,
                pm25=pm25,
                pm10=pm10,
                energy_watts=energy_watts
            )
            print("\n  ✅ Reading saved to database")

            # ── Evaluate thresholds and trigger alerts ────────────
            result = evaluate_reading(
                temperature=temperature  or 20.0,
                humidity=humidity        or 50.0,
                air_quality=air_voltage  or 0.0,
                noise=noise_voltage      or 0.0,
                pm25=pm25                or 0.0,
                energy=energy_watts      or 0.0
            )

            overall = result.get('overall', 'good')
            status_icons = {'good': '🟢', 'warn': '🟡', 'bad': '🔴'}
            print(f"  {status_icons.get(overall, '⚪')} Overall status: {overall.upper()}")

            # ── Wait for next poll ────────────────────────────────
            print(f"\n  Waiting {POLL_INTERVAL} seconds until next reading...\n")
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nSmartFactory stopped by user.")

    finally:
        # Always clean up GPIO on exit
        cleanup_gpio()
        print("Shutdown complete.")


# ── ENTRY POINT ──────────────────────────────────────────────────

if __name__ == '__main__':
    run()