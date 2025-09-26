# API Test Suite

This test suite comprehensively tests the API endpoints to ensure proper error handling, input validation, and security measures.

## Test Coverage

### 1. HTTP 418 "I'm a teapot" Error (Highest Priority)
- ✅ Tests that `"coffee": "teapot"` in POST data returns HTTP 418
- ✅ Verifies this error takes priority over all other validation
- ✅ Tests with various combinations of valid/invalid data

### 2. HTTP 400 Bad Request Errors
- ✅ Missing `zip` parameter
- ✅ Missing `measure_name` parameter  
- ✅ Missing both parameters
- ✅ Empty string values
- ✅ None values
- ✅ Invalid ZIP code format (not 5 digits)
- ✅ Invalid `measure_name` (not in allowed list)
- ✅ Non-JSON requests
- ✅ Malformed JSON

### 3. HTTP 404 Not Found Errors
- ✅ Valid ZIP with invalid `measure_name`
- ✅ Invalid ZIP with valid `measure_name`
- ✅ Both invalid
- ✅ Invalid endpoints

### 4. SQL Injection Protection
- ✅ Tests various SQL injection attempts in `zip` parameter
- ✅ Tests various SQL injection attempts in `measure_name` parameter
- ✅ Verifies database integrity after injection attempts
- ✅ Confirms parameterized queries prevent execution

### 5. Input Validation
- ✅ ZIP code format validation (exactly 5 digits)
- ✅ `measure_name` validation against allowed list
- ✅ Case sensitivity validation
- ✅ Special character handling

## Running the Tests

### Prerequisites
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
python run_tests.py
```

### Run with unittest directly
```bash
python -m unittest test_api.py -v
```

### Run with pytest (if installed)
```bash
pytest test_api.py -v
```

## Test Structure

The test suite uses Python's built-in `unittest` framework and includes:

- **TestAPI class**: Main test class containing all test methods
- **setUp/tearDown**: Creates and cleans up test database
- **Individual test methods**: Each testing a specific aspect
- **Sub-tests**: Multiple test cases within each method for comprehensive coverage

## Security Features Tested

1. **Parameterized Queries**: All database queries use parameterized statements to prevent SQL injection
2. **Input Sanitization**: All inputs are validated before database queries
3. **Error Handling**: Proper error responses without exposing internal details
4. **Type Validation**: Strict validation of input types and formats

## Test Database

The test suite creates a temporary SQLite database with sample data to test against, ensuring:
- Tests don't affect production data
- Consistent test environment
- Easy cleanup after tests

## Expected Results

All tests should pass, demonstrating that:
- The API properly handles all error conditions
- SQL injection attacks are prevented
- Input validation works correctly
- Error codes are returned as expected
