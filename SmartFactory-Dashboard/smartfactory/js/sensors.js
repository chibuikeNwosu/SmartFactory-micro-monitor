/* ================================================================
   SmartFactory Micro-Monitor — Sensor Simulation Module
   File: js/sensors.js

   Purpose:
   Simulates live sensor readings by updating the dashboard cards
   every 5 seconds with slightly varied values.

   When the Raspberry Pi is connected:
   Replace the simulateSensorReading() function with a fetch()
   call to the Flask API endpoint, for example:

     fetch('http://<PI_IP>:5000/api/readings/latest')
       .then(res => res.json())
       .then(data => updateAllCards(data));

   Sensors simulated:
   - DHT22     → Temperature (°C) and Humidity (%)
   - MQ-135    → Air Quality (Voltage via ADS1115)
   - KY-037    → Noise Level (Voltage via ADS1115)
   - PMS5003   → Dust PM2.5 (μg/m³)
   - SCT-013   → Energy Consumption (kW)
   ================================================================ */


/* ── SENSOR THRESHOLDS ──────────────────────────────────────────
   Defines the good/warn/bad boundaries for each sensor.
   These match the threshold_engine.py values on the Pi.

   To change compliance thresholds, update these values.
   ─────────────────────────────────────────────────────────── */
const THRESHOLDS = {
  temp:   { warnMin: 16, warnMax: 26, badMin: 10, badMax: 32 },
  hum:    { warnMin: 30, warnMax: 70, badMin: 10, badMax: 90 },
  air:    { warn: 1.0,  bad: 2.0  },   /* Voltage thresholds */
  noise:  { warn: 0.18, bad: 0.25 },   /* Voltage thresholds */
  dust:   { warn: 12,   bad: 35   },   /* μg/m³ thresholds   */
  energy: { warn: 4.0,  bad: 5.5  }    /* kW thresholds       */
};

/* Track total readings count for the stats banner */
let totalReadings = 47;


/* ── HELPER FUNCTIONS ───────────────────────────────────────── */

/**
 * randomVariation
 * Returns a value slightly varied from the base, simulating
 * the natural fluctuation of a real physical sensor.
 *
 * @param {number} base  - Base reading value
 * @param {number} range - Maximum variation (±range/2)
 * @returns {number}
 */
function randomVariation(base, range) {
  return Math.round((base + (Math.random() - 0.5) * range) * 1000) / 1000;
}


/**
 * getStatus
 * Determines the status string ('good', 'warn', 'bad') for a
 * given sensor value based on its configured thresholds.
 *
 * @param {string} sensor - Sensor key (matches THRESHOLDS keys)
 * @param {number} value  - Current reading value
 * @returns {string} 'good' | 'warn' | 'bad'
 */
function getStatus(sensor, value) {
  const t = THRESHOLDS[sensor];

  /* Range-based thresholds (temperature, humidity) */
  if (t.warnMin !== undefined) {
    if (value < t.badMin || value > t.badMax) return 'bad';
    if (value < t.warnMin || value > t.warnMax) return 'warn';
    return 'good';
  }

  /* Upper-limit thresholds (air, noise, dust, energy) */
  if (value >= t.bad)  return 'bad';
  if (value >= t.warn) return 'warn';
  return 'good';
}


/**
 * getStatusLabel
 * Returns a human-readable status label for a sensor + status combo.
 *
 * @param {string} sensor - Sensor key
 * @param {string} status - 'good' | 'warn' | 'bad'
 * @returns {string}
 */
function getStatusLabel(sensor, status) {
  const labels = {
    temp:   { good: 'NORMAL',   warn: 'WARM',     bad: 'CRITICAL'  },
    hum:    { good: 'NORMAL',   warn: 'HIGH',      bad: 'CRITICAL'  },
    air:    { good: 'GOOD',     warn: 'MODERATE',  bad: 'POOR'      },
    noise:  { good: 'QUIET',    warn: 'MODERATE',  bad: 'LOUD'      },
    dust:   { good: 'GOOD',     warn: 'MODERATE',  bad: 'POOR'      },
    energy: { good: 'NORMAL',   warn: 'ELEVATED',  bad: 'HIGH'      }
  };
  return labels[sensor][status];
}


/**
 * getBarPercent
 * Calculates what percentage fill the progress bar should show
 * based on the sensor value relative to its scale.
 *
 * @param {string} sensor - Sensor key
 * @param {number} value  - Current reading value
 * @returns {number} 0–100
 */
function getBarPercent(sensor, value) {
  const scales = {
    temp:   { min: 10, max: 35  },
    hum:    { min: 0,  max: 100 },
    air:    { min: 0,  max: 3   },
    noise:  { min: 0,  max: 1   },
    dust:   { min: 0,  max: 35  },
    energy: { min: 0,  max: 6   }
  };
  const s = scales[sensor];
  return Math.min(100, Math.max(0, ((value - s.min) / (s.max - s.min)) * 100));
}


/* ── CARD UPDATE FUNCTION ───────────────────────────────────────

/**
 * updateCard
 * Updates a single sensor card's value, status badge,
 * coloured top bar, and progress bar fill.
 *
 * @param {string} sensor      - Sensor key (e.g. 'temp')
 * @param {number} value       - New reading value
 * @param {string} displayVal  - Formatted display string (e.g. '21.4')
 * @param {string} unit        - Unit string (e.g. '°C')
 */
function updateCard(sensor, value, displayVal, unit) {
  const status = getStatus(sensor, value);
  const label  = getStatusLabel(sensor, status);
  const barPct = getBarPercent(sensor, value);

  /* Update the card container class for the coloured top bar */
  const card = document.getElementById('card-' + sensor);
  if (card) {
    card.className = 'sensor-card ' + status;
  }

  /* Update the reading value display */
  const valEl = document.getElementById('val-' + sensor);
  if (valEl) {
    valEl.innerHTML = displayVal + '<span class="unit">' + unit + '</span>';
  }

  /* Update the status badge text and class */
  const statusEl = document.getElementById('status-' + sensor);
  if (statusEl) {
    statusEl.className = 'card-status ' + status;
    statusEl.textContent = label;
  }

  /* Update the progress bar fill width */
  const barEl = document.getElementById('bar-' + sensor);
  if (barEl) {
    barEl.style.width = barPct.toFixed(1) + '%';
  }

  return status;
}


/* ── MAIN SENSOR UPDATE FUNCTION ────────────────────────────────

/**
 * updateSensors
 * Generates new simulated readings for all sensors and updates
 * the dashboard. Called every 5 seconds by setInterval.
 *
 * NOTE: When Pi is connected, replace the randomVariation()
 * calls with data fetched from the Flask API.
 */
function updateSensors() {

  /* Generate slightly varied readings from base values */
  const temp   = randomVariation(21.4, 0.4);
  const hum    = randomVariation(58.2, 1.0);
  const air    = randomVariation(1.24, 0.10);
  const noise  = randomVariation(0.153, 0.015);
  const dust   = Math.max(1, Math.round(randomVariation(5, 1)));
  const energy = randomVariation(2.4, 0.2);

  /* Update each sensor card */
  updateCard('temp',   temp,              temp.toFixed(1),  '°C');
  updateCard('hum',    hum,               hum.toFixed(1),   '%');
  const airStatus = updateCard('air',    air,    air.toFixed(2),   'V');
  updateCard('noise',  noise,             noise.toFixed(3), 'V');
  updateCard('dust',   dust,              dust.toString(),  'μg/m³');
  updateCard('energy', energy,            energy.toFixed(1),'kW');

  /* Update rolling chart data for current sensor */
  appendChartDataPoint('temp',  temp);
  appendChartDataPoint('air',   air);
  appendChartDataPoint('dust',  dust);
  appendChartDataPoint('noise', noise);

  /* Increment and display reading count */
  totalReadings++;
  const readingsEl = document.getElementById('stat-readings');
  if (readingsEl) {
    readingsEl.textContent = totalReadings;
  }

  /* Trigger alert if air quality is poor */
  if (airStatus === 'bad') {
    addAlert('bad', 'CRITICAL: Air quality reading ' + air.toFixed(2) + 'V exceeded danger threshold (2.0V)');
  } else if (airStatus === 'warn' && Math.random() < 0.2) {
    /* Only log moderate warnings occasionally to avoid flooding */
    addAlert('warn', 'Air quality elevated — ' + air.toFixed(2) + 'V approaching limit (1.0V threshold)');
  }
}


/* Start the sensor update loop — runs every 5 seconds */
setInterval(updateSensors, 5000);
