# Numeric Converter - cs1060-hw2-base

A web-based application that converts numbers between different formats including:
- English text (e.g., "one hundred twenty-three")
- Binary
- Octal
- Decimal
- Hexadecimal
- Base64

## Setup

1. Install the required dependencies. We recommend following the best Python practice of a virtual environment. (This assumes Python3.)
```bash
python3 -m venv "hw2-env"
. hw2-env/bin/activate
pip3 install -r requirements.txt
```

2. Run the application:
```bash
python api/index.py
```

3. Open your web browser and navigate to `http://localhost:5000`

## Usage

1. Enter your input value in the text box
2. Select the input format from the dropdown menu
3. Select the desired output format from the second dropdown menu
4. Click "Convert" to see the result

## Examples

- Convert decimal to binary: Input "42" with input type "decimal" and output type "binary"
- Convert text to decimal: Input "forty two" with input type "text" and output type "decimal"
- Convert hexadecimal to text: Input "2a" with input type "hexadecimal" and output type "text"

# Deploying
The application should deploy to [Vercel](https://vercel.com?utm_source=github&utm_medium=readme&utm_campaign=vercel-examples) 
out of the box.

Just Add New... > Project, import the Git repository, and off you go.
Note that Vercel's Hobby plan means your private repository needs to be
in your personal GitHub account, not the organizational account.

## County Data API

### Endpoint

- URL: `/county_data`
- Method: `POST`
- Content-Type: `application/json`

### Required JSON body

- `zip`: 5-digit ZIP code (string)
- `measure_name`: One of the following strings:
  - Violent crime rate
  - Unemployment
  - Children in poverty
  - Diabetic screening
  - Mammography screening
  - Preventable hospital stays
  - Uninsured
  - Sexually transmitted infections
  - Physical inactivity
  - Adult obesity
  - Premature Death
  - Daily fine particulate matter

### Special behavior

- If the request JSON includes `{"coffee":"teapot"}`, the API returns HTTP 418.

### Responses

- 200: JSON array of matching county records for the given `zip` and `measure_name`
- 400: Bad request (missing/invalid `zip` or `measure_name`, or non-JSON)
- 404: Not found (no matching data)
- 418: I'm a teapot (when `coffee=teapot` is supplied)

### Examples

Successful query:

```bash
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d '{"zip":"02138","measure_name":"Adult obesity"}' \
  http://localhost:5000/county_data | jq
```

Missing fields (400):

```bash
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d '{"zip":"02138"}' \
  http://localhost:5000/county_data
```

Teapot (418):

```bash
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d '{"coffee":"teapot","zip":"02138","measure_name":"Adult obesity"}' \
  http://localhost:5000/county_data
```
