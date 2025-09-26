from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import re

app = Flask(__name__)

ALLOWED_MEASURES = {
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter",
}

def get_db_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'data.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/county_data', methods=['POST'])
def county_data():
    # Ensure JSON content type and payload
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request must be JSON with content-type: application/json"}), 400

    # Special 418 case supersedes all other behavior
    if data.get('coffee') == 'teapot':
        return jsonify({"error": "I'm a teapot"}), 418

    zip_code = data.get('zip')
    measure_name = data.get('measure_name')

    # Validate required inputs
    if not zip_code or not measure_name:
        return jsonify({"error": "Both 'zip' and 'measure_name' are required"}), 400

    # Validate zip format (5 digits)
    if not re.fullmatch(r"\d{5}", str(zip_code)):
        return jsonify({"error": "'zip' must be a 5-digit ZIP code"}), 400

    # Validate measure_name against allowed list
    if measure_name not in ALLOWED_MEASURES:
        return jsonify({"error": "'measure_name' is invalid"}), 400

    # Perform parameterized query joining zip_county and county_health_rankings
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = (
            """
            SELECT
                chr.state,
                chr.county,
                chr.state_code,
                chr.county_code,
                chr.year_span,
                chr.measure_name,
                chr.measure_id,
                chr.numerator,
                chr.denominator,
                chr.raw_value,
                chr.confidence_interval_lower_bound,
                chr.confidence_interval_upper_bound,
                chr.data_release_year,
                chr.fipscode
            FROM county_health_rankings AS chr
            JOIN zip_county AS zc
              ON TRIM(zc.county_code) = TRIM(chr.fipscode)
             AND zc.state_abbreviation = chr.state
            WHERE zc.zip = ? AND chr.measure_name = ?
            """
        )
        cursor.execute(query, (zip_code, measure_name))
        rows = cursor.fetchall()

    if not rows:
        return jsonify({"error": "No data found for provided zip and measure_name"}), 404

    results = []
    for row in rows:
        results.append({
            "state": row["state"],
            "county": row["county"],
            "state_code": row["state_code"],
            "county_code": row["county_code"],
            "year_span": row["year_span"],
            "measure_name": row["measure_name"],
            "measure_id": row["measure_id"],
            "numerator": row["numerator"],
            "denominator": row["denominator"],
            "raw_value": row["raw_value"],
            "confidence_interval_lower_bound": row["confidence_interval_lower_bound"],
            "confidence_interval_upper_bound": row["confidence_interval_upper_bound"],
            "data_release_year": row["data_release_year"],
            "fipscode": row["fipscode"],
        })

    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True)
