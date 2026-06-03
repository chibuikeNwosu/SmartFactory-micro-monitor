# SmartFactory Micro-Monitor 🏭

**Environmental Compliance Station for SME Manufacturers**  
Griffith College Dublin — BSc (Hons) Computing — 2026

---

## Team

| Name | Role |
|------|------|
| Chibuike Chinedu Nwosu | Lead Developer / Hardware |
| Prosper Munachimso Obiezue | Software / Integration |
| Michelle Eberiere Otomewo | Testing / Documentation |

**Supervisor:** Barry

---

## What is SmartFactory?

SmartFactory is a Raspberry Pi-powered physical device that sits on the factory floor and automatically collects, monitors, and reports environmental compliance data for small and medium-sized manufacturers (SMEs).

It bridges the gap between the factory floor and the compliance report — automatically.

**Hardware cost: ~€80. Enterprise alternatives: €15,000/year.**

---

## Project Structure

```
smartfactory-micro-monitor/
│
├── index.html          ← Main dashboard HTML
│
├── css/
│   └── style.css       ← All dashboard styles
│
├── js/
│   ├── clock.js        ← Real-time clock updater
│   ├── charts.js       ← Chart.js historical trend charts
│   ├── sensors.js      ← Sensor simulation / live data updates
│   ├── alerts.js       ← Alert log management
│   └── modal.js        ← Report modal open/close
│
└── README.md           ← This file
```

---

## Sensors Used

| Sensor | Measures | Interface |
|--------|----------|-----------|
| DHT22 | Temperature & Humidity | GPIO Digital |
| MQ-135 | Air Quality / VOCs | ADS1115 ADC (I2C) |
| KY-037 | Noise Level | ADS1115 ADC (I2C) |
| PMS5003 | Dust PM1.0 / PM2.5 / PM10 | UART Serial |
| SCT-013 | Energy Consumption | ADS1115 ADC (I2C) |

**Actuators:** RGB LED (status indicator), Buzzer (threshold alerts), Relay Module (auto power cut-off)

---

## Hardware

- **Core:** Raspberry Pi 3B
- **OS:** Raspberry Pi OS (Debian Trixie 64-bit)
- **ADC:** ADS1115 16-bit I2C Analog-to-Digital Converter
- **Access:** RealVNC (desktop), PuTTY SSH (terminal)

---

## Software Stack

| Component | Technology |
|-----------|------------|
| Sensor polling | Python + RPi.GPIO + smbus2 |
| Database | SQLite |
| Web dashboard | Flask + Chart.js |
| PDF reports | ReportLab |
| Version control | Git + GitHub |

---

## Live Demo

The dashboard demo is hosted on GitHub Pages:  
**https://chibuikenwosu.github.io/SmartFactory-micro-monitor**

> **Note:** The live GitHub Pages version uses simulated sensor data.  
> When connected to the Raspberry Pi on the local network, replace  
> the simulation in `js/sensors.js` with real API calls to Flask.

---

## Connecting to Real Pi Data

When the Raspberry Pi is running, update `js/sensors.js`:

```javascript
// Replace simulateSensorReading() with:
fetch('http://192.168.0.XX:5000/api/readings/latest')
  .then(res => res.json())
  .then(data => updateAllCards(data));
```

And update `js/modal.js` to trigger real PDF generation:

```javascript
fetch('http://192.168.0.XX:5000/api/generate-report', { method: 'POST' })
  .then(res => res.blob())
  .then(blob => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'SmartFactory_Report.pdf';
    a.click();
  });
```

---

## Running Locally

No server needed. Just open `index.html` in any browser:

```bash
# Option 1 - Double click index.html in file explorer
# Option 2 - From terminal:
open index.html          # Mac
start index.html         # Windows
xdg-open index.html      # Linux
```

---

## License

Academic project — Griffith College Dublin 2026
