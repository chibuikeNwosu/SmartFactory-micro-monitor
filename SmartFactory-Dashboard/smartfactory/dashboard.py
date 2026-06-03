# ================================================================
# SmartFactory Micro-Monitor — Flask Web Dashboard Server
# File: dashboard.py
#
# Purpose:
# Serves the web dashboard and provides API endpoints that the
# browser uses to fetch live sensor data and trigger reports.
#
# Routes:
#   GET  /                          → Serves the dashboard HTML
#   GET  /api/readings/latest       → Returns latest sensor reading
#   GET  /api/readings/history      → Returns last N readings
#   GET  /api/alerts                → Returns recent breach events
#   POST /api/generate-report       → Generates and returns PDF
#
# Usage:
#   python dashboard.py
#   Then open: http://192.168.0.XX:5000
# ================================================================

from flask import Flask, jsonify, send_file, request
from database import get_latest_reading
from report_generator import generate_report
import sqlite3
import os
from datetime import datetime, timedelta

# ── FLASK APP SETUP ──────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder='.',       # Serve CSS/JS from project root
    template_folder='.'      # Serve HTML from project root
)

# Database path — same as database.py
DB_PATH = os.path.join(os.path.dirname(__file__), 'smartfactory.db')


# ── HELPER FUNCTIONS ─────────────────────────────────────────────

def get_db_connection():
    """Opens a SQLite database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── HTML DASHBOARD ROUTE ─────────────────────────────────────────

@app.route('/')
def index():
    """
    Serves the main dashboard HTML file.
    Accessible from any device on the same WiFi network at:
    http://192.168.0.XX:5000
    """
    return send_file('index.html')


# ── API ROUTES ───────────────────────────────────────────────────

@app.route('/api/readings/latest', methods=['GET'])
def api_latest_reading():
    """
    Returns the most recent sensor reading as JSON.

    Used by js/sensors.js to update the dashboard cards
    when connected to a real Raspberry Pi.

    Example response:
    {
        "timestamp": "2026-06-02 11:30:00",
        "temperature": 21.4,
        "humidity": 58.2,
        "air_quality_voltage": 1.24,
        "noise_voltage": 0.153,
        "pm1": 3.0,
        "pm25": 5.0,
        "pm10": 7.0,
        "energy_watts": 2400.0
    }
    """
    reading = get_latest_reading()

    if not reading:
        return jsonify({
            'error': 'No readings found in database',
            'message': 'Make sure sensor_manager.py is running'
        }), 404

    return jsonify(reading)


@app.route('/api/readings/history', methods=['GET'])
def api_readings_history():
    """
    Returns the last N sensor readings for chart display.

    Query parameters:
        hours (int): How many hours of history to return. Default 12.
        limit (int): Maximum number of readings. Default 100.

    Used by js/charts.js to populate historical trend charts.
    """
    hours = request.args.get('hours', 12, type=int)
    limit = request.args.get('limit', 100, type=int)

    since = datetime.now() - timedelta(hours=hours)
    since_str = since.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT timestamp, temperature, humidity,
               air_quality_voltage, noise_voltage,
               pm25, energy_watts
        FROM readings
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
        LIMIT ?
    ''', (since_str, limit))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        'count':    len(rows),
        'hours':    hours,
        'readings': rows
    })


@app.route('/api/alerts', methods=['GET'])
def api_alerts():
    """
    Returns recent threshold breach events for the alert log.

    Query parameters:
        limit (int): Maximum number of events. Default 20.

    Used by js/alerts.js to populate the alert log panel.
    """
    limit = request.args.get('limit', 20, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if breach_events table exists
    cursor.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='breach_events'
    ''')

    if not cursor.fetchone():
        conn.close()
        return jsonify({'alerts': [], 'count': 0})

    cursor.execute('''
        SELECT * FROM breach_events
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        'count':  len(rows),
        'alerts': rows
    })


@app.route('/api/compliance-score', methods=['GET'])
def api_compliance_score():
    """
    Returns the overall compliance score for the past 7 days.

    Used by the compliance banner to update the score ring.
    """
    try:
        from report_generator import (
            get_readings_for_period,
            calculate_sensor_stats,
            calculate_overall_score
        )
        readings = get_readings_for_period(days=7)
        stats    = calculate_sensor_stats(readings)
        score    = calculate_overall_score(stats)

        if score >= 80:
            status = 'COMPLIANT'
        elif score >= 60:
            status = 'AT RISK'
        else:
            status = 'NON-COMPLIANT'

        return jsonify({
            'score':  score,
            'status': status
        })

    except Exception as e:
        return jsonify({'score': 0, 'status': 'UNKNOWN', 'error': str(e)})


@app.route('/api/generate-report', methods=['POST'])
def api_generate_report():
    """
    Triggers PDF report generation and returns the file for download.

    Called by js/modal.js when the Generate Report button is clicked.
    The browser receives the PDF as a file download.

    Request body (optional JSON):
        { "days": 7 }
    """
    try:
        data = request.get_json(silent=True) or {}
        days = data.get('days', 7)

        # Generate the PDF report
        report_path = generate_report(days=days)

        if not report_path or not os.path.exists(report_path):
            return jsonify({'error': 'Report generation failed'}), 500

        # Send the PDF file as a download
        return send_file(
            report_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=os.path.basename(report_path)
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def api_status():
    """
    Returns system status information.
    Useful for checking if the Flask server is running correctly.
    """
    reading = get_latest_reading()

    return jsonify({
        'status':       'running',
        'timestamp':    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'has_readings': reading is not None,
        'latest_reading_time': reading['timestamp'] if reading else None
    })


# ── SERVE STATIC FILES ───────────────────────────────────────────

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serves CSS files from the css/ folder."""
    return send_file(os.path.join('css', filename))


@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serves JavaScript files from the js/ folder."""
    return send_file(os.path.join('js', filename))


# ── START THE SERVER ─────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  SmartFactory Micro-Monitor")
    print("  Web Dashboard Server")
    print("=" * 50)
    print("\nStarting Flask server...")
    print("Dashboard available at:")
    print("  http://localhost:5000")
    print("  http://192.168.0.XX:5000  (replace XX with Pi IP)")
    print("\nPress CTRL+C to stop\n")

    # host='0.0.0.0' makes it accessible from any device on the network
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False   # Set to True during development only
    )