# 🏭 SmartFactory Micro-Monitor

> **A Raspberry Pi Environmental Compliance Station for SME Manufacturers**

[![License](https://img.shields.io/badge/license-Academic-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-green.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%203B-red.svg)](https://raspberrypi.com)
[![College](https://img.shields.io/badge/Griffith%20College-Dublin-orange.svg)](https://griffith.ie)

---

## 📋 Table of Contents

- [What is SmartFactory?](#what-is-smartfactory)
- [The Problem It Solves](#the-problem-it-solves)
- [Live Demo](#live-demo)
- [Team](#team)
- [Hardware](#hardware)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Sensor Wiring Guide](#sensor-wiring-guide)
- [Software Setup](#software-setup)
- [Running the System](#running-the-system)
- [Web Dashboard](#web-dashboard)
- [PDF Report Generator](#pdf-report-generator)
- [Connecting Real Pi Data to Dashboard](#connecting-real-pi-data-to-dashboard)
- [Troubleshooting](#troubleshooting)
- [Screenshots](#screenshots)
- [Acknowledgements](#acknowledgements)

---

## 🌿 What is SmartFactory?

SmartFactory Micro-Monitor is a physical environmental compliance station built on a Raspberry Pi 3B. It sits on a factory floor and **automatically collects, monitors, and reports environmental data** — giving small manufacturers the compliance evidence their big clients demand, at a fraction of enterprise software costs.

```
Enterprise ESG tools  →  €15,000 / year
SmartFactory hardware →  ~€80 one time
```

The system measures **air quality, temperature, humidity, noise levels, dust particles, and energy consumption** continuously, triggers real-time alerts when thresholds are exceeded, and generates professional PDF compliance reports on demand.

---

## 🎯 The Problem It Solves

Small and medium-sized manufacturers (SMEs) face a growing compliance gap:

- Large clients increasingly demand sustainability and environmental data from their entire supply chain
- Enterprise environmental monitoring platforms cost €5,000–€50,000 per year — far beyond SME budgets
- Manual data entry is error-prone, time-consuming, and impossible to audit
- **73% of SMEs cite upfront cost as the primary barrier to sustainability reporting** *(Sage/ICC Global Study, 2023)*

SmartFactory bridges this gap by making automated environmental compliance affordable and accessible to the factories that need it most.

---

## 🌐 Live Demo

The interactive dashboard is live at:

**[https://chibuikenwosu.github.io/SmartFactory-micro-monitor](https://chibuikenwosu.github.io/SmartFactory-micro-monitor)**

> The live demo uses simulated sensor data. When connected to the Raspberry Pi on a local network, it displays real factory floor readings updated every 60 seconds.

---

## 👥 Team

| Name | Role |
|------|------|
| **Chibuike Chinedu Nwosu** (3142395) | Lead Developer — Hardware & Software Integration |
| **Prosper Munachimso Obiezue** | Software Development — Dashboard & Testing |
| **Michelle Eberiere Otomewo** | Testing, Evaluation & Documentation |

**Supervisor:** Barry  
**Institution:** Griffith College Dublin  
**Programme:** BSc (Hons) in Computing  
**Year:** 2026

---

## 🔧 Hardware

### Core Components

| Component | Purpose | Interface | Cost |
|-----------|---------|-----------|------|
| Raspberry Pi 3B | Main compute unit | — | — |
| DHT22 | Temperature & humidity | GPIO Digital (Pin 7) | €14.61 |
| MQ-135 | Air quality / VOC / CO2 | ADS1115 ADC → I2C | €3.94 |
| PMS5003 | Dust / particulate matter (PM1, PM2.5, PM10) | UART Serial | €26.64 |
| KY-037 | Noise level monitoring | ADS1115 ADC → I2C | €3.20 |
| SCT-013 | Non-invasive energy monitoring | ADS1115 ADC → I2C | €10.99 |
| ADS1115 | 16-bit analog-to-digital converter | I2C | €7.51 |
| RGB LED | Visual status indicator (Green/Amber/Red) | GPIO Digital | €0.74 |
| Buzzer | Audio threshold breach alerts | GPIO Digital | €3.20 |
| Relay Module | Optional auto power cut-off | GPIO Digital | €8.00 |

**Total hardware cost: ~€78.83**

### GPIO Pin Assignment

```
Pi Pin 1  (3.3V)    → ADS1115 VDD
Pi Pin 2  (5V)      → MQ-135, KY-037, PMS5003, Buzzer power
Pi Pin 3  (SDA)     → ADS1115 I2C data
Pi Pin 5  (SCL)     → ADS1115 I2C clock
Pi Pin 6  (GND)     → Shared ground (all components)
Pi Pin 7  (GPIO4)   → DHT22 data signal
Pi Pin 8  (TX)      → PMS5003 RX
Pi Pin 10 (RX)      → PMS5003 TX
Pi Pin 11 (GPIO17)  → Buzzer signal
Pi Pin 13 (GPIO27)  → RGB LED blue
Pi Pin 15 (GPIO22)  → RGB LED red
Pi Pin 16 (GPIO23)  → RGB LED green
Pi Pin 29 (GPIO5)   → Relay IN1
```

---

## 📁 Project Structure

```
SmartFactory-micro-monitor/
│
├── index.html                  ← Live web dashboard (HTML)
│
├── css/
│   └── style.css               ← All dashboard styles with comments
│
├── js/
│   ├── clock.js                ← Real-time clock updater
│   ├── charts.js               ← Chart.js historical trend charts
│   ├── sensors.js              ← Sensor simulation / live data
│   ├── alerts.js               ← Alert log management
│   └── modal.js                ← Report modal open/close
│
├── sensor_manager.py           ← Polls all sensors every 60 seconds
├── database.py                 ← SQLite database setup and queries
├── threshold_engine.py         ← Evaluates readings, triggers alerts
├── report_generator.py         ← Generates PDF compliance reports
├── dashboard.py                ← Flask web server (when Pi connected)
│
├── reports/                    ← Generated PDF reports saved here
├── smartfactory.db             ← SQLite database (auto-created)
│
└── README.md                   ← This file
```

---

## 🚀 Getting Started

### Prerequisites

- Raspberry Pi 3B running Raspberry Pi OS (Debian Trixie 64-bit)
- Python 3.13+
- Git
- All hardware components wired correctly (see wiring guide below)

### Clone the Repository

```bash
git clone https://github.com/chibuikeNwosu/SmartFactory-micro-monitor.git
cd SmartFactory-micro-monitor
```

### Create Python Virtual Environment

```bash
python -m venv env
source env/bin/activate
```

### Install Dependencies

```bash
pip install RPi.GPIO \
            adafruit-circuitpython-dht \
            adafruit-circuitpython-ads1x15 \
            smbus2 \
            pms5003 \
            flask \
            reportlab \
            --trusted-host pypi.org \
            --trusted-host files.pythonhosted.org
```

---

## 🔌 Sensor Wiring Guide

### Breadboard Layout

All components are placed in column **e** of the breadboard:

```
Rows  1–10  → ADS1115 ADC module
Rows 14–17  → MQ-135 air quality sensor
Rows 21–24  → KY-037 sound sensor
Rows 28–30  → DHT22 temperature/humidity sensor
Rows 34–41  → PMS5003 dust sensor breakout board
Rows 44–46  → Buzzer module
Rows 49–52  → RGB LED module
Row  55     → Shared GND hub → Pi Pin 6
Row  57     → Shared 3.3V hub → Pi Pin 1
Row  54     → Shared 5V hub → Pi Pin 2
```

### Shared Power Rails

Since multiple components share power and ground, breadboard hub rows are used:

```
GND hub  → Row 55 col a → Pi Pin 6 (GND)
3.3V hub → Row 57 col a → Pi Pin 1 (3.3V)
5V hub   → Row 54 col a → Pi Pin 2 (5V)
```

### DHT22 Wiring

```
DHT22 VCC  → Row 57 col b  (3.3V hub)
DHT22 DATA → Pi Pin 7      (GPIO4)
DHT22 GND  → Row 55 col e  (GND hub)
```

### ADS1115 + MQ-135 + KY-037

```
ADS1115 VDD  → Row 57 col b  (3.3V hub)
ADS1115 GND  → Row 55 col b  (GND hub)
ADS1115 SCL  → Pi Pin 5      (SCL)
ADS1115 SDA  → Pi Pin 3      (SDA)
ADS1115 A0   → MQ-135 AO    (analog bridge wire on breadboard)
ADS1115 A1   → KY-037 AO    (analog bridge wire on breadboard)

MQ-135 VCC   → Row 54 col b  (5V hub)
MQ-135 GND   → Row 55 col c  (GND hub)

KY-037 VCC   → Row 54 col c  (5V hub)
KY-037 GND   → Row 55 col d  (GND hub)
```

### PMS5003 Wiring

```
PMS5003 VCC  → Row 54 col d  (5V hub)
PMS5003 GND  → Row 55 col b  (GND hub)
PMS5003 RX   → Pi Pin 10     (UART RX)
PMS5003 TX   → Pi Pin 8      (UART TX)
```

### RGB LED Wiring

```
RGB GND   → Row 55 col b  (GND hub)
RGB Green → Pi Pin 16     (GPIO23)
RGB Red   → Pi Pin 15     (GPIO22)
RGB Blue  → Pi Pin 13     (GPIO27)
```

---

## ⚙️ Software Setup

### Enable Required Interfaces

Run `sudo raspi-config` and enable:

```
Interface Options → I2C      → YES
Interface Options → Serial Port:
    Login shell over serial  → NO
    Serial hardware enabled  → YES
```

### Disable Bluetooth (Required for PMS5003)

Add to `/boot/config.txt`:

```
dtoverlay=disable-bt
```

Then reboot:

```bash
sudo reboot
```

---

## ▶️ Running the System

### Test Individual Sensors First

```bash
# Test DHT22
python dht22_test.py

# Test MQ-135 air quality
python mq135_test.py

# Test PMS5003 dust sensor
python pms5003_test.py

# Test KY-037 sound sensor
python smbus_test.py
```

### Run All Sensors Together

```bash
python sensor_manager.py
```

Expected output:
```
══════════════════════════════════════════════════
  SmartFactory Micro-Monitor
  Environmental Compliance Station
══════════════════════════════════════════════════

──────────────────────────────────────────────────
  Reading at: 2026-06-02 11:30:00
──────────────────────────────────────────────────
🌡️  Temperature : 21.4°C
💧  Humidity    : 58.2%
💨  Air Quality : 1.235V → MODERATE
🔊  Noise Level : 0.153V → QUIET
🌫️  PM2.5       : 5 μg/m³ → GOOD
⚡  Energy      : 2.4kW

  Waiting 60 seconds...
```

### Start the Web Dashboard

```bash
python dashboard.py
```

Then open on any device on the same WiFi network:
```
http://192.168.0.XX:5000
```

### Generate a PDF Report

```bash
python report_generator.py
```

Report saved to:
```
reports/SmartFactory_Report_2026-06-02_11-30.pdf
```

---

## 📊 Web Dashboard

The dashboard provides:

- **Live sensor panels** — all 6 sensors updating every 60 seconds
- **Compliance score ring** — overall percentage score
- **Historical trend charts** — switchable between temperature, air, dust, noise
- **Alert log** — real-time breach event feed
- **Generate Report button** — one-click PDF generation

### Viewing on Mobile

The dashboard is fully responsive. Open the same URL on any phone connected to the lab WiFi:

```
http://192.168.0.XX:5000
```

---

## 📄 PDF Report Generator

Each report covers a configurable period (default 7 days) and includes:

- Overall compliance score (0–100%)
- Reporting period and total readings count
- Sensor-by-sensor breakdown (average, min, max, compliance %)
- Complete threshold breach event log
- Plain English recommendations

### Report Output Location

```
smartfactory/reports/SmartFactory_Report_YYYY-MM-DD_HH-MM.pdf
```

---

## 🔗 Connecting Real Pi Data to Dashboard

When the Raspberry Pi is running, update `js/sensors.js` to fetch live data instead of simulating:

```javascript
// Replace the setInterval(updateSensors, 5000) simulation with:
async function fetchLiveData() {
  const res  = await fetch('http://192.168.0.XX:5000/api/readings/latest');
  const data = await res.json();
  updateCard('temp',   data.temperature,         data.temperature.toFixed(1),  '°C');
  updateCard('hum',    data.humidity,             data.humidity.toFixed(1),     '%');
  updateCard('air',    data.air_quality_voltage,  data.air_quality_voltage.toFixed(2), 'V');
  updateCard('noise',  data.noise_voltage,        data.noise_voltage.toFixed(3),'V');
  updateCard('dust',   data.pm25,                 data.pm25.toString(),         'μg/m³');
  updateCard('energy', data.energy_watts / 1000,  (data.energy_watts/1000).toFixed(1), 'kW');
}
setInterval(fetchLiveData, 60000);
fetchLiveData();
```

Update `js/modal.js` to trigger real PDF generation:

```javascript
function showReportModal() {
  fetch('http://192.168.0.XX:5000/api/generate-report', { method: 'POST' })
    .then(res => res.blob())
    .then(blob => {
      const a    = document.createElement('a');
      a.href     = URL.createObjectURL(blob);
      a.download = 'SmartFactory_Report.pdf';
      a.click();
    });
}
```

---

## 🛠️ Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `SSL certificate verify failed` on pip install | Pi clock wrong | Run `sudo timedatectl set-ntp true` or use `--trusted-host` flag |
| `No such file or directory: /dev/ttyAMA0` | Bluetooth using UART | Add `dtoverlay=disable-bt` to `/boot/config.txt` and reboot |
| `Remote I/O error` on ADS1115 | Loose SDA/SCL wires | Re-seat wires on Pi Pin 3 and Pin 5 |
| `DHT library works` but no readings | Warm-up period | Wait 30 seconds after boot before reading DHT22 |
| VNC `Timed out` | Wrong network | Ensure laptop is on lab WiFi, not phone hotspot |
| Green LED not working on RGB module | Hardware fault | Replace RGB LED module — red and blue channels confirmed working |
| PMS5003 read timeout | UART conflict | Confirm Bluetooth disabled, use `/dev/serial0` not `/dev/ttyAMA0` |

---

## 📸 Screenshots

### Live Dashboard
![SmartFactory Dashboard](screenshots/dashboard.png)

### Threshold Breach Alert
![Breach Alert](screenshots/breach_alert.png)

### PDF Compliance Report
![PDF Report](screenshots/pdf_report.png)

### Physical Prototype
![Hardware Setup](screenshots/hardware.png)

> Add your screenshots to a `screenshots/` folder and they will appear here automatically.

---

## 🙏 Acknowledgements

- **Barry** — project supervisor, Griffith College Dublin
- **Griffith College Dublin** — laboratory facilities and equipment
- **Raspberry Pi Foundation** — hardware platform and documentation
- **Adafruit** — CircuitPython sensor libraries
- **ReportLab** — PDF generation library
- **Chart.js** — dashboard data visualisation

---

## 📚 References

1. World Economic Forum — *Building smarter climate reporting for SMEs*, 2026
2. Sage / ICC / PwC — *Path for growth: Making sustainability reporting work for SMEs*, 2023
3. Tandfonline — *Challenges and opportunities in sustainability reporting for SMEs*, 2024
4. Thomson Reuters — *Addressing the key challenges for SMEs in sustainability reporting*, 2025
5. Seagate — *IoT environmental monitoring: The shift to sustainability*, 2023

---

*SmartFactory Micro-Monitor — Griffith College Dublin — BSc (Hons) Computing — 2026*  
*"Build the bridge between the factory floor and the compliance report."*
