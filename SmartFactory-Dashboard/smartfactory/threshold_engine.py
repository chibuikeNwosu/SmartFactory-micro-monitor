# ================================================================
# SmartFactory Micro-Monitor — Threshold Engine
# File: threshold_engine.py
#
# Purpose:
# Evaluates every incoming sensor reading against configured
# compliance thresholds. When a threshold is breached:
#   1. Activates the RGB LED (amber or red)
#   2. Sounds the buzzer
#   3. Logs the breach to the database
#   4. Returns a status report for the dashboard
#
# Usage:
#   from threshold_engine import evaluate_reading, cleanup_gpio
# ================================================================

import RPi.GPIO as GPIO
import time
from database import save_breach

# ── GPIO PIN NUMBERS (BCM numbering) ────────────────────────────
PIN_LED_RED   = 22   # Pi Pin 15
PIN_LED_GREEN = 23   # Pi Pin 16
PIN_LED_BLUE  = 27   # Pi Pin 13
PIN_BUZZER    = 17   # Pi Pin 11
PIN_RELAY     = 5    # Pi Pin 29

# ── COMPLIANCE THRESHOLDS ────────────────────────────────────────
# These values define what is considered good, moderate, and poor
# for each sensor. Adjust these to match your client's requirements.
THRESHOLDS = {
    'temperature': {
        'good_min': 16.0,
        'good_max': 26.0,
        'warn_min': 12.0,
        'warn_max': 30.0,
    },
    'humidity': {
        'good_min': 30.0,
        'good_max': 70.0,
        'warn_min': 15.0,
        'warn_max': 85.0,
    },
    'air_quality': {
        'warn': 1.0,
        'bad':  2.0,
    },
    'noise': {
        'warn': 0.18,
        'bad':  0.25,
    },
    'pm25': {
        'warn': 12.0,
        'bad':  35.0,
    },
    'energy': {
        'warn': 4000.0,
        'bad':  5500.0,
    },
}

# ── GPIO SETUP ───────────────────────────────────────────────────

def setup_gpio():
    """
    Initialises all GPIO pins for LED, buzzer and relay output.
    Sets all outputs LOW (off) on startup.
    """
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    output_pins = [
        PIN_LED_RED, PIN_LED_GREEN,
        PIN_LED_BLUE, PIN_BUZZER, PIN_RELAY
    ]

    for pin in output_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    print("GPIO initialised — all outputs set LOW")


def cleanup_gpio():
    """
    Safely cleans up all GPIO pins on system shutdown.
    Always call this before exiting the program.
    """
    all_off()
    GPIO.cleanup()
    print("GPIO cleaned up")


# ── LED CONTROL ──────────────────────────────────────────────────

def all_off():
    """Turns off all LED channels and buzzer."""
    GPIO.output(PIN_LED_RED,   GPIO.LOW)
    GPIO.output(PIN_LED_GREEN, GPIO.LOW)
    GPIO.output(PIN_LED_BLUE,  GPIO.LOW)
    GPIO.output(PIN_BUZZER,    GPIO.LOW)


def set_led_green():
    """Green LED — all sensors compliant."""
    all_off()
    GPIO.output(PIN_LED_GREEN, GPIO.HIGH)


def set_led_amber():
    """Amber LED (red + green) — approaching threshold."""
    all_off()
    GPIO.output(PIN_LED_RED,   GPIO.HIGH)
    GPIO.output(PIN_LED_GREEN, GPIO.HIGH)


def set_led_red():
    """Red LED — threshold breached."""
    all_off()
    GPIO.output(PIN_LED_RED, GPIO.HIGH)


def sound_buzzer(duration=0.5):
    """
    Sounds the buzzer for a given duration in seconds.

    Args:
        duration (float): How long to sound in seconds. Default 0.5.
    """
    GPIO.output(PIN_BUZZER, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(PIN_BUZZER, GPIO.LOW)


# ── THRESHOLD EVALUATION ─────────────────────────────────────────

def get_sensor_status(sensor_key, value):
    """
    Determines whether a reading is good, warn, or bad.

    Args:
        sensor_key (str): Key matching THRESHOLDS dict
        value (float):    Current sensor reading

    Returns:
        str: 'good', 'warn', or 'bad'
    """
    t = THRESHOLDS.get(sensor_key)
    if not t:
        return 'good'

    # Range-based threshold (temperature, humidity)
    if 'good_min' in t:
        if value < t['warn_min'] or value > t['warn_max']:
            return 'bad'
        if value < t['good_min'] or value > t['good_max']:
            return 'warn'
        return 'good'

    # Upper-limit threshold (air, noise, dust, energy)
    if value >= t['bad']:
        return 'bad'
    if value >= t['warn']:
        return 'warn'
    return 'good'


def evaluate_reading(temperature, humidity, air_quality,
                     noise, pm25, energy):
    """
    Evaluates a complete set of sensor readings against thresholds.
    Updates the RGB LED and buzzer based on the worst status found.
    Logs any breaches to the database.

    Args:
        temperature  (float): DHT22 reading in °C
        humidity     (float): DHT22 reading in %
        air_quality  (float): MQ-135 voltage
        noise        (float): KY-037 voltage
        pm25         (float): PMS5003 PM2.5 in μg/m³
        energy       (float): SCT-013 in watts

    Returns:
        dict: Status report with overall status and per-sensor results
    """
    readings = {
        'temperature': temperature,
        'humidity':    humidity,
        'air_quality': air_quality,
        'noise':       noise,
        'pm25':        pm25,
        'energy':      energy,
    }

    results = {}
    worst_status = 'good'

    # Evaluate each sensor
    for sensor_key, value in readings.items():
        if value is None:
            results[sensor_key] = 'unknown'
            continue

        status = get_sensor_status(sensor_key, value)
        results[sensor_key] = status

        # Log breach to database
        if status in ('warn', 'bad'):
            threshold_val = THRESHOLDS[sensor_key].get(
                'bad' if status == 'bad' else 'warn',
                THRESHOLDS[sensor_key].get('good_max')
            )
            save_breach(sensor_key, value, threshold_val, status)

        # Track the worst status across all sensors
        if status == 'bad':
            worst_status = 'bad'
        elif status == 'warn' and worst_status == 'good':
            worst_status = 'warn'

    # Update LED based on worst status
    if worst_status == 'bad':
        set_led_red()
        sound_buzzer(duration=1.0)
    elif worst_status == 'warn':
        set_led_amber()
        sound_buzzer(duration=0.3)
    else:
        set_led_green()

    results['overall'] = worst_status
    return results


# ── RUN DIRECTLY FOR TESTING ─────────────────────────────────────

if __name__ == '__main__':
    print("Testing threshold engine...")
    setup_gpio()

    try:
        # Test with a normal reading — should show green LED
        print("\nTest 1 — Normal reading:")
        result = evaluate_reading(21.4, 58.2, 0.85, 0.15, 5.0, 2400.0)
        print(f"Overall status: {result['overall']}")

        time.sleep(2)

        # Test with a warning reading — should show amber LED
        print("\nTest 2 — Warning reading:")
        result = evaluate_reading(21.4, 58.2, 1.20, 0.15, 5.0, 2400.0)
        print(f"Overall status: {result['overall']}")

        time.sleep(2)

        # Test with a critical reading — should show red LED + buzzer
        print("\nTest 3 — Critical reading:")
        result = evaluate_reading(21.4, 58.2, 2.50, 0.15, 5.0, 2400.0)
        print(f"Overall status: {result['overall']}")

        time.sleep(2)

    finally:
        cleanup_gpio()
        print("\nTest complete.")