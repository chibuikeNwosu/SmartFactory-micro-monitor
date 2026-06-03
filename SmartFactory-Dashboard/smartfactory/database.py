# ================================================================
# SmartFactory Micro-Monitor — Database Module
# File: database.py
#
# Purpose:
# Creates and manages the SQLite database that stores all
# sensor readings and threshold breach events.
#
# Tables:
#   readings       — one row per sensor poll (every 60s)
#   breach_events  — one row per threshold breach detected
#
# Usage:
#   from database import init_db, save_reading, save_breach
# ================================================================

import sqlite3
import os
from datetime import datetime

# Database file stored in the same folder as this script
DB_PATH = os.path.join(os.path.dirname(__file__), 'smartfactory.db')


def init_db():
    """
    Creates the database and tables if they don't already exist.
    Safe to call on every startup — does nothing if tables exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Main readings table — one row per sensor poll
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           TEXT    NOT NULL,
            temperature         REAL,
            humidity            REAL,
            air_quality_voltage REAL,
            noise_voltage       REAL,
            pm1                 REAL,
            pm25                REAL,
            pm10                REAL,
            energy_watts        REAL
        )
    ''')

    # Breach events table — one row per threshold breach
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS breach_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            sensor      TEXT    NOT NULL,
            value       REAL    NOT NULL,
            threshold   REAL    NOT NULL,
            severity    TEXT    NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialised at: {DB_PATH}")


def save_reading(temperature, humidity, air_quality_voltage,
                 noise_voltage, pm1, pm25, pm10, energy_watts):
    """
    Saves one complete set of sensor readings to the database.

    Args:
        temperature         (float): DHT22 temperature in °C
        humidity            (float): DHT22 humidity in %
        air_quality_voltage (float): MQ-135 voltage via ADS1115
        noise_voltage       (float): KY-037 voltage via ADS1115
        pm1                 (float): PMS5003 PM1.0 in μg/m³
        pm25                (float): PMS5003 PM2.5 in μg/m³
        pm10                (float): PMS5003 PM10 in μg/m³
        energy_watts        (float): SCT-013 energy in watts
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO readings (
            timestamp, temperature, humidity,
            air_quality_voltage, noise_voltage,
            pm1, pm25, pm10, energy_watts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp, temperature, humidity,
        air_quality_voltage, noise_voltage,
        pm1, pm25, pm10, energy_watts
    ))

    conn.commit()
    conn.close()


def save_breach(sensor, value, threshold, severity):
    """
    Logs a threshold breach event to the database.

    Args:
        sensor    (str):   Sensor name e.g. 'air_quality'
        value     (float): The reading that triggered the breach
        threshold (float): The threshold that was exceeded
        severity  (str):   'warn' or 'bad'
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO breach_events (timestamp, sensor, value, threshold, severity)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, sensor, value, threshold, severity))

    conn.commit()
    conn.close()


def get_latest_reading():
    """
    Returns the most recent reading row as a dict.

    Returns:
        dict or None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM readings
        ORDER BY timestamp DESC
        LIMIT 1
    ''')

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# Initialise database on import
init_db()