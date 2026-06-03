# ================================================================
# SmartFactory Micro-Monitor — PDF Report Generator
# File: report_generator.py
#
# Purpose:
# Generates a professionally formatted weekly PDF compliance
# report from sensor data stored in the SQLite database.
#
# The report includes:
#   - Cover page with compliance score
#   - Executive summary in plain English
#   - Sensor-by-sensor compliance breakdown
#   - Threshold breach event log
#   - Recommendations section
#
# Usage:
#   python report_generator.py
#   (also callable from Flask via: from report_generator import generate_report)
#
# Dependencies:
#   pip install reportlab
# ================================================================

import sqlite3
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF


# ── CONFIGURATION ────────────────────────────────────────────────

# Database file path — same as used by database.py
DB_PATH = os.path.join(os.path.dirname(__file__), 'smartfactory.db')

# Output folder for generated reports
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')

# Compliance thresholds — must match threshold_engine.py
THRESHOLDS = {
    'temperature': {
        'label':    'Temperature',
        'unit':     '°C',
        'good_min': 16.0,
        'good_max': 26.0,
        'warn_max': 30.0,
        'warn_min': 12.0,
    },
    'humidity': {
        'label':    'Humidity',
        'unit':     '%',
        'good_min': 30.0,
        'good_max': 70.0,
        'warn_max': 85.0,
        'warn_min': 15.0,
    },
    'air_quality': {
        'label':    'Air Quality',
        'unit':     'V',
        'warn':     1.0,
        'bad':      2.0,
    },
    'noise': {
        'label':    'Noise Level',
        'unit':     'V',
        'warn':     0.18,
        'bad':      0.25,
    },
    'pm25': {
        'label':    'Dust PM2.5',
        'unit':     'μg/m³',
        'warn':     12.0,
        'bad':      35.0,
    },
    'energy': {
        'label':    'Energy',
        'unit':     'kW',
        'warn':     4.0,
        'bad':      5.5,
    },
}

# Brand colours
COLOUR_GREEN  = colors.HexColor('#00A878')
COLOUR_AMBER  = colors.HexColor('#E8A020')
COLOUR_RED    = colors.HexColor('#D94040')
COLOUR_DARK   = colors.HexColor('#0F1520')
COLOUR_MID    = colors.HexColor('#2A3A55')
COLOUR_LIGHT  = colors.HexColor('#E8F0F8')
COLOUR_WHITE  = colors.white
COLOUR_BORDER = colors.HexColor('#C8D8E8')


# ── DATABASE HELPERS ─────────────────────────────────────────────

def get_readings_for_period(days=7):
    """
    Fetches all sensor readings from the past N days.

    Args:
        days (int): Number of days to look back. Default 7.

    Returns:
        list of dict: Each dict is one reading row.
    """
    since = datetime.now() - timedelta(days=days)
    since_str = since.strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT *
        FROM readings
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
    ''', (since_str,))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_breach_events(days=7):
    """
    Fetches all threshold breach events from the past N days.

    Args:
        days (int): Number of days to look back.

    Returns:
        list of dict: Each dict is one breach event row.
    """
    since = datetime.now() - timedelta(days=days)
    since_str = since.strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Only fetch if breach_events table exists
    cursor.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='breach_events'
    ''')

    if not cursor.fetchone():
        conn.close()
        return []

    cursor.execute('''
        SELECT *
        FROM breach_events
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT 50
    ''', (since_str,))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ── STATISTICS CALCULATOR ────────────────────────────────────────

def calculate_sensor_stats(readings, days=7):
    """
    Calculates average, min, max, and compliance percentage
    for each sensor over the reporting period.

    Args:
        readings (list): List of reading dicts from get_readings_for_period()
        days (int): Period length for display purposes

    Returns:
        dict: Statistics per sensor key
    """
    if not readings:
        return {}

    stats = {}

    sensor_columns = {
        'temperature': 'temperature',
        'humidity':    'humidity',
        'air_quality': 'air_quality_voltage',
        'noise':       'noise_voltage',
        'pm25':        'pm25',
        'energy':      'energy_watts',
    }

    for key, col in sensor_columns.items():
        values = [r[col] for r in readings if r.get(col) is not None]

        if not values:
            stats[key] = {
                'avg': None, 'min': None, 'max': None,
                'compliance_pct': None, 'status': 'unknown'
            }
            continue

        avg = sum(values) / len(values)
        minimum = min(values)
        maximum = max(values)
        t = THRESHOLDS[key]

        # Count compliant readings
        compliant = 0
        for v in values:
            if 'good_min' in t:
                # Range-based threshold
                if t['good_min'] <= v <= t['good_max']:
                    compliant += 1
            else:
                # Upper-limit threshold
                if v < t['warn']:
                    compliant += 1

        compliance_pct = (compliant / len(values)) * 100 if values else 0

        # Determine overall status for this sensor
        if 'good_min' in t:
            if t['good_min'] <= avg <= t['good_max']:
                status = 'good'
            elif t['warn_min'] <= avg <= t['warn_max']:
                status = 'warn'
            else:
                status = 'bad'
        else:
            if avg < t['warn']:
                status = 'good'
            elif avg < t['bad']:
                status = 'warn'
            else:
                status = 'bad'

        stats[key] = {
            'avg':            round(avg, 2),
            'min':            round(minimum, 2),
            'max':            round(maximum, 2),
            'compliance_pct': round(compliance_pct, 1),
            'status':         status,
            'count':          len(values),
        }

    return stats


def calculate_overall_score(stats):
    """
    Calculates an overall compliance score (0-100) based on
    the average compliance percentage across all sensors.

    Args:
        stats (dict): Output of calculate_sensor_stats()

    Returns:
        float: Overall compliance score 0-100
    """
    percentages = [
        s['compliance_pct']
        for s in stats.values()
        if s.get('compliance_pct') is not None
    ]
    if not percentages:
        return 0
    return round(sum(percentages) / len(percentages), 1)


# ── REPORT STYLES ────────────────────────────────────────────────

def build_styles():
    """
    Creates and returns all paragraph styles used in the report.

    Returns:
        dict: Named ParagraphStyle objects
    """
    base = getSampleStyleSheet()

    styles = {
        'title': ParagraphStyle(
            'title',
            fontName='Helvetica-Bold',
            fontSize=28,
            textColor=COLOUR_WHITE,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        'subtitle': ParagraphStyle(
            'subtitle',
            fontName='Helvetica',
            fontSize=13,
            textColor=COLOUR_LIGHT,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        'chapter': ParagraphStyle(
            'chapter',
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=COLOUR_DARK,
            spaceBefore=16,
            spaceAfter=8,
        ),
        'body': ParagraphStyle(
            'body',
            fontName='Helvetica',
            fontSize=10,
            textColor=COLOUR_DARK,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leading=15,
        ),
        'small': ParagraphStyle(
            'small',
            fontName='Helvetica',
            fontSize=9,
            textColor=COLOUR_MID,
            spaceAfter=4,
        ),
        'good': ParagraphStyle(
            'good',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=COLOUR_GREEN,
        ),
        'warn': ParagraphStyle(
            'warn',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=COLOUR_AMBER,
        ),
        'bad': ParagraphStyle(
            'bad',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=COLOUR_RED,
        ),
    }
    return styles


# ── COVER PAGE BUILDER ───────────────────────────────────────────

def build_cover_page(story, styles, score, period_start, period_end, total_readings):
    """
    Builds the cover page of the report.

    Args:
        story (list): ReportLab story list to append elements to
        styles (dict): Styles from build_styles()
        score (float): Overall compliance score 0-100
        period_start (str): Start date string
        period_end (str): End date string
        total_readings (int): Total number of readings in period
    """
    # Dark header block using a table with background colour
    header_data = [[
        Paragraph('SmartFactory Micro-Monitor', styles['title']),
    ]]
    header_table = Table(header_data, colWidths=[170 * mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOUR_DARK),
        ('TOPPADDING',    (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)

    # Subtitle block
    subtitle_data = [[
        Paragraph('Environmental Compliance Report', styles['subtitle']),
    ]]
    subtitle_table = Table(subtitle_data, colWidths=[170 * mm])
    subtitle_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), COLOUR_MID),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    story.append(subtitle_table)
    story.append(Spacer(1, 20))

    # Score colour logic
    if score >= 80:
        score_colour = COLOUR_GREEN
        score_label  = 'COMPLIANT'
    elif score >= 60:
        score_colour = COLOUR_AMBER
        score_label  = 'AT RISK'
    else:
        score_colour = COLOUR_RED
        score_label  = 'NON-COMPLIANT'

    # Compliance score box
    score_style = ParagraphStyle(
        'score_num',
        fontName='Helvetica-Bold',
        fontSize=52,
        textColor=score_colour,
        alignment=TA_CENTER,
    )
    label_style = ParagraphStyle(
        'score_label',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=score_colour,
        alignment=TA_CENTER,
    )

    score_data = [
        [Paragraph(f'{score}%', score_style)],
        [Paragraph('Overall compliance score', styles['small'])],
        [Paragraph(score_label, label_style)],
    ]
    score_table = Table(score_data, colWidths=[170 * mm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), COLOUR_LIGHT),
        ('TOPPADDING',    (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('BOX',           (0, 0), (-1, -1), 1, COLOUR_BORDER),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 20))

    # Report metadata table
    meta_data = [
        ['Report period',    f'{period_start}  →  {period_end}'],
        ['Generated',        datetime.now().strftime('%d %B %Y at %H:%M')],
        ['Total readings',   str(total_readings)],
        ['Monitoring device', 'SmartFactory Micro-Monitor — Raspberry Pi 3B'],
        ['Prepared by',      'SmartFactory automated reporting system'],
    ]
    meta_table = Table(meta_data, colWidths=[55 * mm, 115 * mm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',      (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',     (0, 0), (0, -1), COLOUR_MID),
        ('TEXTCOLOR',     (1, 0), (1, -1), COLOUR_DARK),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [COLOUR_WHITE, COLOUR_LIGHT]),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOUR_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, COLOUR_BORDER),
    ]))
    story.append(meta_table)
    story.append(PageBreak())


# ── SENSOR STATS TABLE BUILDER ───────────────────────────────────

def build_sensor_table(story, styles, stats):
    """
    Builds the sensor-by-sensor compliance breakdown table.

    Args:
        story (list): ReportLab story list
        styles (dict): Paragraph styles
        stats (dict): Sensor statistics from calculate_sensor_stats()
    """
    story.append(Paragraph('Sensor compliance breakdown', styles['chapter']))
    story.append(Paragraph(
        'The table below shows the average reading, minimum, maximum, and '
        'compliance percentage for each sensor over the reporting period. '
        'A sensor is considered compliant for a given reading when its value '
        'falls within the acceptable range defined in the threshold configuration.',
        styles['body']
    ))
    story.append(Spacer(1, 8))

    # Table header
    header = [
        Paragraph('<b>Sensor</b>', styles['body']),
        Paragraph('<b>Average</b>', styles['body']),
        Paragraph('<b>Min</b>', styles['body']),
        Paragraph('<b>Max</b>', styles['body']),
        Paragraph('<b>Compliance</b>', styles['body']),
        Paragraph('<b>Status</b>', styles['body']),
    ]

    table_data = [header]

    for key, s in stats.items():
        t = THRESHOLDS[key]
        unit = t['unit']

        if s.get('avg') is None:
            row = [
                Paragraph(t['label'], styles['body']),
                Paragraph('No data', styles['small']),
                Paragraph('—', styles['small']),
                Paragraph('—', styles['small']),
                Paragraph('—', styles['small']),
                Paragraph('—', styles['small']),
            ]
        else:
            # Choose status style
            status_style = styles.get(s['status'], styles['body'])
            status_labels = {'good': 'COMPLIANT', 'warn': 'AT RISK', 'bad': 'BREACH'}
            status_text = status_labels.get(s['status'], 'UNKNOWN')

            row = [
                Paragraph(t['label'], styles['body']),
                Paragraph(f"{s['avg']} {unit}", styles['body']),
                Paragraph(f"{s['min']} {unit}", styles['small']),
                Paragraph(f"{s['max']} {unit}", styles['small']),
                Paragraph(f"{s['compliance_pct']}%", styles['body']),
                Paragraph(status_text, status_style),
            ]
        table_data.append(row)

    col_widths = [38 * mm, 28 * mm, 24 * mm, 24 * mm, 28 * mm, 28 * mm]
    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOUR_DARK),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  COLOUR_WHITE),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOUR_WHITE, COLOUR_LIGHT]),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOUR_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, COLOUR_BORDER),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 16))


# ── BREACH LOG BUILDER ───────────────────────────────────────────

def build_breach_log(story, styles, breaches):
    """
    Builds the threshold breach event log section.

    Args:
        story (list): ReportLab story list
        styles (dict): Paragraph styles
        breaches (list): Breach event dicts from get_breach_events()
    """
    story.append(Paragraph('Threshold breach log', styles['chapter']))

    if not breaches:
        story.append(Paragraph(
            'No threshold breaches were recorded during this reporting period. '
            'All sensor readings remained within acceptable compliance limits.',
            styles['body']
        ))
        return

    story.append(Paragraph(
        f'{len(breaches)} threshold breach event(s) were recorded during this '
        f'reporting period. Each event is listed below with its timestamp, '
        f'affected sensor, recorded value, and applicable threshold.',
        styles['body']
    ))
    story.append(Spacer(1, 8))

    header = [
        Paragraph('<b>Timestamp</b>', styles['body']),
        Paragraph('<b>Sensor</b>', styles['body']),
        Paragraph('<b>Reading</b>', styles['body']),
        Paragraph('<b>Threshold</b>', styles['body']),
        Paragraph('<b>Severity</b>', styles['body']),
    ]

    table_data = [header]

    for b in breaches:
        severity_style = styles['warn'] if b.get('severity') == 'warn' else styles['bad']
        severity_text  = 'MODERATE' if b.get('severity') == 'warn' else 'CRITICAL'

        ts = b.get('timestamp', 'unknown')
        try:
            dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            ts = dt.strftime('%d/%m/%Y %H:%M')
        except Exception:
            pass

        row = [
            Paragraph(ts, styles['small']),
            Paragraph(b.get('sensor', '—'), styles['body']),
            Paragraph(str(b.get('value', '—')), styles['body']),
            Paragraph(str(b.get('threshold', '—')), styles['body']),
            Paragraph(severity_text, severity_style),
        ]
        table_data.append(row)

    col_widths = [38 * mm, 34 * mm, 30 * mm, 30 * mm, 28 * mm]
    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  COLOUR_DARK),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  COLOUR_WHITE),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOUR_WHITE, COLOUR_LIGHT]),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOUR_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, COLOUR_BORDER),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 16))


# ── RECOMMENDATIONS BUILDER ──────────────────────────────────────

def build_recommendations(story, styles, stats):
    """
    Generates plain-English recommendations based on sensor status.

    Args:
        story (list): ReportLab story list
        styles (dict): Paragraph styles
        stats (dict): Sensor statistics
    """
    story.append(Paragraph('Recommendations', styles['chapter']))

    recommendations = []

    for key, s in stats.items():
        if s.get('status') == 'bad':
            t = THRESHOLDS[key]
            recommendations.append(
                f"<b>{t['label']}</b> readings averaged {s['avg']} {t['unit']} "
                f"during this period, which exceeds the critical threshold. "
                f"Immediate investigation is recommended before the next client audit."
            )
        elif s.get('status') == 'warn':
            t = THRESHOLDS[key]
            recommendations.append(
                f"<b>{t['label']}</b> readings averaged {s['avg']} {t['unit']} "
                f"during this period, approaching the compliance threshold. "
                f"Preventive action is advised."
            )

    if not recommendations:
        story.append(Paragraph(
            'All sensors reported within acceptable compliance limits during this period. '
            'No corrective action is required. Continue regular monitoring and maintain '
            'current factory floor conditions to preserve compliance status.',
            styles['body']
        ))
    else:
        for rec in recommendations:
            story.append(Paragraph(f'• {rec}', styles['body']))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width='100%', thickness=0.5, color=COLOUR_BORDER))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        'This report was generated automatically by the SmartFactory Micro-Monitor system. '
        'Readings are provided as environmental monitoring estimates and should be reviewed '
        'alongside any formal audit processes required by your client agreements.',
        styles['small']
    ))


# ── MAIN REPORT GENERATOR ────────────────────────────────────────

def generate_report(days=7, output_path=None):
    """
    Main function — generates the complete PDF compliance report.

    Args:
        days (int): Number of days to cover in the report. Default 7.
        output_path (str): Optional custom output file path.
                           If None, saves to reports/ folder with timestamp.

    Returns:
        str: Path to the generated PDF file, or None on failure.
    """
    print(f"\nSmartFactory — Generating {days}-day compliance report...")

    # ── Fetch data ──────────────────────────────────────────────
    readings = get_readings_for_period(days)
    breaches = get_breach_events(days)

    if not readings:
        print("WARNING: No readings found in database for this period.")
        print("         The report will be generated with no data.")
        print("         Make sure sensor_manager.py has been running.")

    # ── Calculate statistics ────────────────────────────────────
    stats = calculate_sensor_stats(readings, days)
    score = calculate_overall_score(stats)

    # ── Period dates ────────────────────────────────────────────
    period_end   = datetime.now().strftime('%d %B %Y')
    period_start = (datetime.now() - timedelta(days=days)).strftime('%d %B %Y')

    # ── Output file path ────────────────────────────────────────
    if output_path is None:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename  = f'SmartFactory_Report_{timestamp}.pdf'
        output_path = os.path.join(REPORTS_DIR, filename)

    # ── Build PDF ───────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title='SmartFactory Compliance Report',
        author='SmartFactory Micro-Monitor',
    )

    styles = build_styles()
    story  = []

    # Cover page
    build_cover_page(
        story, styles, score,
        period_start, period_end,
        len(readings)
    )

    # Executive summary
    story.append(Paragraph('Executive summary', styles['chapter']))

    summary_text = (
        f"This report covers environmental monitoring data collected between "
        f"{period_start} and {period_end}, comprising {len(readings)} sensor readings "
        f"across {days} days of continuous monitoring. "
    )
    if score >= 80:
        summary_text += (
            f"The factory achieved an overall compliance score of {score}%, "
            f"indicating that environmental conditions were within acceptable limits "
            f"for the majority of the reporting period."
        )
    elif score >= 60:
        summary_text += (
            f"The factory achieved an overall compliance score of {score}%. "
            f"While conditions were generally acceptable, some sensors reported "
            f"elevated readings that may require attention before the next audit."
        )
    else:
        summary_text += (
            f"The factory achieved an overall compliance score of {score}%, "
            f"which is below the recommended threshold. Immediate review of "
            f"factory floor conditions is strongly advised."
        )

    story.append(Paragraph(summary_text, styles['body']))
    story.append(Spacer(1, 8))

    if breaches:
        story.append(Paragraph(
            f"{len(breaches)} threshold breach event(s) were recorded during this period. "
            f"See the breach log on the following page for full details.",
            styles['body']
        ))

    story.append(Spacer(1, 12))

    # Sensor breakdown table
    build_sensor_table(story, styles, stats)

    # Breach log
    build_breach_log(story, styles, breaches)

    # Recommendations
    build_recommendations(story, styles, stats)

    # Build the PDF
    doc.build(story)

    print(f"Report generated successfully:")
    print(f"  File: {output_path}")
    print(f"  Score: {score}%")
    print(f"  Readings: {len(readings)}")
    print(f"  Breaches: {len(breaches)}")

    return output_path


# ── RUN DIRECTLY ─────────────────────────────────────────────────

if __name__ == '__main__':
    path = generate_report(days=7)
    if path:
        print(f"\nDone! Open the report at:\n  {path}")
    else:
        print("\nReport generation failed. Check the error messages above.")