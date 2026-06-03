/* ================================================================
   SmartFactory Micro-Monitor — Charts Module
   File: js/charts.js

   Purpose:
   Manages the historical trend chart using Chart.js.
   Handles initial chart rendering and tab switching between
   different sensor datasets (temperature, air, dust, noise).

   Dependencies:
   - Chart.js (loaded via CDN in index.html before this file)

   Elements used:
   - #trendChart   → <canvas> element in the chart panel
   - .chart-tab    → tab buttons for switching datasets
   ================================================================ */


/* ── CHART DATASET DEFINITIONS ─────────────────────────────────
   Each key matches a chart tab button's data attribute.
   Simulated hourly readings for the current day (07:00 to 17:00).

   When connected to the real Raspberry Pi:
   Replace these arrays with data fetched from the Flask API.
   Example: fetch('/api/readings?sensor=temp&hours=12')
   ─────────────────────────────────────────────────────────── */
const chartDatasets = {

  /* DHT22 Temperature sensor — readings in Celsius */
  temp: {
    label: 'Temperature (°C)',
    data:  [20.1, 20.4, 21.0, 21.2, 21.4, 21.8, 22.1, 21.9, 21.6, 21.4, 21.4],
    color: '#00e5a0',
    min: 16,
    max: 30
  },

  /* MQ-135 Air Quality sensor — analog voltage via ADS1115 ADC */
  air: {
    label: 'Air Quality (V)',
    data:  [0.85, 0.90, 0.95, 1.10, 1.24, 1.30, 1.18, 1.05, 0.98, 0.92, 1.24],
    color: '#f59e0b',
    min: 0,
    max: 3
  },

  /* PMS5003 Dust sensor — PM2.5 particulate matter in μg/m³ */
  dust: {
    label: 'PM2.5 (μg/m³)',
    data:  [3, 4, 4, 5, 6, 5, 5, 4, 4, 5, 5],
    color: '#3b82f6',
    min: 0,
    max: 35
  },

  /* KY-037 Sound sensor — analog voltage via ADS1115 ADC */
  noise: {
    label: 'Noise Level (V)',
    data:  [0.15, 0.16, 0.21, 0.16, 0.15, 0.15, 0.16, 0.15, 0.15, 0.15, 0.153],
    color: '#a78bfa',
    min: 0,
    max: 1
  }
};

/* Time labels for the X axis — one per hour */
const chartLabels = [
  '07:00', '08:00', '09:00', '10:00', '11:00', '12:00',
  '13:00', '14:00', '15:00', '16:00', '17:00'
];

/* Track the currently active chart key and Chart.js instance */
let currentChartKey = 'temp';
let chartInstance;


/**
 * buildChart
 * Destroys any existing chart and renders a new one for the given
 * sensor key using Chart.js line chart configuration.
 *
 * @param {string} key - One of: 'temp', 'air', 'dust', 'noise'
 */
function buildChart(key) {
  const dataset = chartDatasets[key];

  // Destroy existing chart instance to prevent canvas memory leak
  if (chartInstance) {
    chartInstance.destroy();
  }

  const ctx = document.getElementById('trendChart').getContext('2d');

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartLabels,
      datasets: [{
        label: dataset.label,
        data: dataset.data,
        borderColor: dataset.color,
        backgroundColor: dataset.color + '18', /* 10% opacity fill */
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: dataset.color,
        fill: true,
        tension: 0.4 /* Smooth curved line */
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,

      plugins: {
        legend: {
          display: false /* Hide legend — label is shown in tab */
        },
        tooltip: {
          /* Match dashboard dark theme styling */
          backgroundColor: '#111827',
          borderColor: '#1e2d45',
          borderWidth: 1,
          titleColor: '#94a3b8',
          bodyColor: '#e2e8f0',
          titleFont: { family: 'Share Tech Mono', size: 11 },
          bodyFont:  { family: 'Share Tech Mono', size: 12 }
        }
      },

      scales: {
        x: {
          grid:  { color: '#1e2d45' },
          ticks: { color: '#4b6080', font: { family: 'Share Tech Mono', size: 10 } }
        },
        y: {
          grid:  { color: '#1e2d45' },
          ticks: { color: '#4b6080', font: { family: 'Share Tech Mono', size: 10 } },
          min: dataset.min,
          max: dataset.max
        }
      }
    }
  });
}


/**
 * switchChart
 * Called by the chart tab onclick handlers in index.html.
 * Updates the active tab styling and re-renders the chart.
 *
 * @param {string} key       - Sensor key ('temp', 'air', 'dust', 'noise')
 * @param {Element} clickedBtn - The tab button element that was clicked
 */
function switchChart(key, clickedBtn) {
  currentChartKey = key;

  // Remove active class from all tabs
  document.querySelectorAll('.chart-tab').forEach(tab => {
    tab.classList.remove('active');
  });

  // Add active class to the clicked tab
  clickedBtn.classList.add('active');

  // Rebuild chart with new dataset
  buildChart(key);
}


/**
 * appendChartDataPoint
 * Adds a new data point to the current chart and removes the oldest
 * one to maintain a rolling window. Called by sensors.js when
 * new simulated readings are generated.
 *
 * @param {string} key   - Sensor key
 * @param {number} value - New reading value
 */
function appendChartDataPoint(key, value) {
  // Add new value and remove oldest (rolling window)
  chartDatasets[key].data.push(value);
  chartDatasets[key].data.shift();

  // Only re-render if this sensor is currently displayed
  if (currentChartKey === key) {
    buildChart(key);
  }
}


// Build the default chart (temperature) on page load
buildChart('temp');
