from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from num2words import num2words
from text2digits import text2digits
import base64
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

def text_to_number(text):
    """Convert English text number to integer"""
    # Remove any non-alphanumeric characters and convert to lowercase
    text = re.sub(r'[^a-zA-Z\s-]', '', text.lower())
    
    # Special case for zero
    if text in ['zero', 'nil']:
        return 0
    
    # Dictionary for special number words
    number_words = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    
    if text in number_words:
        return number_words[text]
    
    raise ValueError("Unable to convert text to number")

def number_to_text(number):
    """Convert integer to English text"""
    try:
        return num2words(number)
    except:
        raise ValueError("Unable to convert number to text")

def base64_to_number(b64_str):
    """Convert base64 to integer"""
    try:
        # Decode base64 to bytes, then convert bytes to integer
        decoded_bytes = base64.b64decode(b64_str)
        return int.from_bytes(decoded_bytes, byteorder='big')
    except:
        raise ValueError("Invalid base64 input")

def number_to_base64(number):
    """Convert integer to base64"""
    try:
        # Convert integer to bytes, then encode to base64
        byte_count = (number.bit_length() + 7) // 8
        number_bytes = number.to_bytes(byte_count, byteorder='big')
        return base64.b64encode(number_bytes).decode('utf-8')
    except:
        raise ValueError("Unable to convert to base64")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        input_value = data['input']
        input_type = data['inputType']
        output_type = data['outputType']
        
        # Convert input to integer based on input type
        if input_type == 'text':
            number = text_to_number(input_value)
        elif input_type == 'binary':
            number = int(input_value, 2)
        elif input_type == 'octal':
            number = int(input_value, 8)
        elif input_type == 'decimal':
            number = int(input_value)
        elif input_type == 'hexadecimal':
            number = int(input_value, 16)
        elif input_type == 'base64':
            number = base64_to_number(input_value)
        else:
            raise ValueError("Invalid input type")
            
        # Convert integer to output type
        if output_type == 'text':
            result = number_to_text(number)
        elif output_type == 'binary':
            result = bin(number)[2:]  # Remove '0b' prefix
        elif output_type == 'octal':
            result = oct(number)[2:]  # Remove '0o' prefix
        elif output_type == 'decimal':
            result = str(number)
        elif output_type == 'hexadecimal':
            result = hex(number)[2:]  # Remove '0x' prefix
        elif output_type == 'base64':
            result = number_to_base64(number)
        else:
            raise ValueError("Invalid output type")
            
        return jsonify({'result': result, 'error': None})
    except Exception as e:
        return jsonify({'result': None, 'error': str(e)})

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
              ON zc.county_code = chr.county_code
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
