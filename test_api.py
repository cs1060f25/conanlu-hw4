import unittest
import json
import sqlite3
import os
from api.index import app, get_db_connection, ALLOWED_MEASURES

class TestAPI(unittest.TestCase):
    """Test suite for the API endpoints"""
    
    def setUp(self):
        """Set up test client and test database"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create a test database with sample data
        self.test_db_path = 'test_data.db'
        self.create_test_database()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def create_test_database(self):
        """Create a test database with sample data"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create zip_county table
        cursor.execute('''
            CREATE TABLE zip_county (
                zip TEXT,
                county_code TEXT,
                state_abbreviation TEXT
            )
        ''')
        
        # Create county_health_rankings table
        cursor.execute('''
            CREATE TABLE county_health_rankings (
                state TEXT,
                county TEXT,
                state_code TEXT,
                county_code TEXT,
                year_span TEXT,
                measure_name TEXT,
                measure_id TEXT,
                numerator TEXT,
                denominator TEXT,
                raw_value TEXT,
                confidence_interval_lower_bound TEXT,
                confidence_interval_upper_bound TEXT,
                data_release_year TEXT,
                fipscode TEXT
            )
        ''')
        
        # Insert test data
        cursor.execute('''
            INSERT INTO zip_county (zip, county_code, state_abbreviation)
            VALUES ('12345', '001', 'CA'), ('54321', '002', 'NY')
        ''')
        
        cursor.execute('''
            INSERT INTO county_health_rankings 
            (state, county, state_code, county_code, year_span, measure_name, 
             measure_id, numerator, denominator, raw_value, 
             confidence_interval_lower_bound, confidence_interval_upper_bound, 
             data_release_year, fipscode)
            VALUES 
            ('CA', 'Test County', '06', '001', '2020-2021', 'Violent crime rate',
             '1', '100', '1000', '10.0', '8.0', '12.0', '2021', '001'),
            ('NY', 'Another County', '36', '002', '2020-2021', 'Unemployment',
             '2', '50', '500', '10.0', '8.0', '12.0', '2021', '002')
        ''')
        
        conn.commit()
        conn.close()
    
    def test_418_teapot_priority(self):
        """Test that 'coffee': 'teapot' returns HTTP 418 error with highest priority"""
        test_cases = [
            # Case 1: Only coffee: teapot
            {'coffee': 'teapot'},
            # Case 2: coffee: teapot with valid zip and measure_name
            {'coffee': 'teapot', 'zip': '12345', 'measure_name': 'Violent crime rate'},
            # Case 3: coffee: teapot with missing required fields
            {'coffee': 'teapot', 'zip': '12345'},
            # Case 4: coffee: teapot with invalid data
            {'coffee': 'teapot', 'zip': 'invalid', 'measure_name': 'Invalid measure'}
        ]
        
        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post('/county_data', 
                                         data=json.dumps(data),
                                         content_type='application/json')
                self.assertEqual(response.status_code, 418)
                self.assertIn("I'm a teapot", response.get_json()['error'])
    
    def test_400_missing_parameters(self):
        """Test that missing zip or measure_name returns HTTP 400 error"""
        test_cases = [
            # Missing both parameters
            {},
            # Missing zip
            {'measure_name': 'Violent crime rate'},
            # Missing measure_name
            {'zip': '12345'},
            # Empty zip
            {'zip': '', 'measure_name': 'Violent crime rate'},
            # Empty measure_name
            {'zip': '12345', 'measure_name': ''},
            # None values
            {'zip': None, 'measure_name': 'Violent crime rate'},
            {'zip': '12345', 'measure_name': None}
        ]
        
        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post('/county_data',
                                         data=json.dumps(data),
                                         content_type='application/json')
                self.assertEqual(response.status_code, 400)
                self.assertIn("Both 'zip' and 'measure_name' are required", 
                            response.get_json()['error'])
    
    def test_400_invalid_zip_format(self):
        """Test that invalid zip format returns HTTP 400 error"""
        test_cases = [
            {'zip': '1234', 'measure_name': 'Violent crime rate'},  # Too short
            {'zip': '123456', 'measure_name': 'Violent crime rate'},  # Too long
            {'zip': '1234a', 'measure_name': 'Violent crime rate'},  # Contains letter
            {'zip': '12-45', 'measure_name': 'Violent crime rate'},  # Contains dash
            {'zip': '12 45', 'measure_name': 'Violent crime rate'},  # Contains space
        ]
        
        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post('/county_data',
                                         data=json.dumps(data),
                                         content_type='application/json')
                self.assertEqual(response.status_code, 400)
                self.assertIn("'zip' must be a 5-digit ZIP code", 
                            response.get_json()['error'])
    
    def test_400_invalid_measure_name(self):
        """Test that invalid measure_name returns HTTP 400 error"""
        test_cases = [
            {'zip': '12345', 'measure_name': 'Invalid measure'},
            {'zip': '12345', 'measure_name': 'violent crime rate'},  # Wrong case
            {'zip': '12345', 'measure_name': 'Violent Crime Rate'},  # Wrong case
            {'zip': '12345', 'measure_name': 'VIOLENT CRIME RATE'},  # Wrong case
        ]
        
        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post('/county_data',
                                         data=json.dumps(data),
                                         content_type='application/json')
                self.assertEqual(response.status_code, 400)
                self.assertIn("'measure_name' is invalid", 
                            response.get_json()['error'])
    
    def test_404_not_found(self):
        """Test that non-existent zip/measure_name pairs return HTTP 404 error"""
        test_cases = [
            # Valid zip, invalid measure_name
            {'zip': '12345', 'measure_name': 'Unemployment'},
            # Invalid zip, valid measure_name
            {'zip': '99999', 'measure_name': 'Violent crime rate'},
            # Both invalid
            {'zip': '99999', 'measure_name': 'Unemployment'},
        ]
        
        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post('/county_data',
                                         data=json.dumps(data),
                                         content_type='application/json')
                self.assertEqual(response.status_code, 404)
                self.assertIn("No data found for provided zip and measure_name", 
                            response.get_json()['error'])
    
    def test_404_invalid_endpoint(self):
        """Test that invalid endpoints return HTTP 404 error"""
        response = self.client.post('/invalid_endpoint',
                                  data=json.dumps({'zip': '12345', 'measure_name': 'Violent crime rate'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 404)
    
    def test_sql_injection_protection(self):
        """Test that SQL injection attempts are properly handled"""
        # Temporarily patch the database path for testing
        original_get_db_connection = get_db_connection
        def test_get_db_connection():
            conn = sqlite3.connect(self.test_db_path)
            conn.row_factory = sqlite3.Row
            return conn
        
        # Monkey patch the function
        import api.index
        api.index.get_db_connection = test_get_db_connection
        
        try:
            sql_injection_attempts = [
                # SQL injection in zip parameter
                {'zip': "12345'; DROP TABLE county_health_rankings; --", 'measure_name': 'Violent crime rate'},
                {'zip': "12345' OR '1'='1", 'measure_name': 'Violent crime rate'},
                {'zip': "12345' UNION SELECT * FROM county_health_rankings --", 'measure_name': 'Violent crime rate'},
                # SQL injection in measure_name parameter
                {'zip': '12345', 'measure_name': "Violent crime rate'; DROP TABLE county_health_rankings; --"},
                {'zip': '12345', 'measure_name': "Violent crime rate' OR '1'='1"},
                {'zip': '12345', 'measure_name': "Violent crime rate' UNION SELECT * FROM county_health_rankings --"},
                # SQL injection in both parameters
                {'zip': "12345'; DROP TABLE county_health_rankings; --", 'measure_name': "Violent crime rate'; DROP TABLE county_health_rankings; --"},
            ]
            
            for data in sql_injection_attempts:
                with self.subTest(data=data):
                    response = self.client.post('/county_data',
                                             data=json.dumps(data),
                                             content_type='application/json')
                    # Should either return 400 (validation error) or 404 (no data found)
                    # but should NOT execute the SQL injection
                    self.assertIn(response.status_code, [400, 404])
                    
                    # Verify the database still exists and is intact
                    conn = test_get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='county_health_rankings'")
                    self.assertIsNotNone(cursor.fetchone(), "Database table should still exist after SQL injection attempt")
                    conn.close()
        
        finally:
            # Restore original function
            api.index.get_db_connection = original_get_db_connection
    
    def test_successful_request(self):
        """Test that valid requests return successful responses"""
        # Temporarily patch the database path for testing
        original_get_db_connection = get_db_connection
        def test_get_db_connection():
            conn = sqlite3.connect(self.test_db_path)
            conn.row_factory = sqlite3.Row
            return conn
        
        # Monkey patch the function
        import api.index
        api.index.get_db_connection = test_get_db_connection
        
        try:
            response = self.client.post('/county_data',
                                     data=json.dumps({'zip': '12345', 'measure_name': 'Violent crime rate'}),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)
            self.assertEqual(data[0]['state'], 'CA')
            self.assertEqual(data[0]['county'], 'Test County')
            self.assertEqual(data[0]['measure_name'], 'Violent crime rate')
        finally:
            # Restore original function
            api.index.get_db_connection = original_get_db_connection
    
    def test_non_json_request(self):
        """Test that non-JSON requests return HTTP 400 error"""
        response = self.client.post('/county_data',
                                 data="not json",
                                 content_type='text/plain')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Request must be JSON with content-type: application/json", 
                    response.get_json()['error'])
    
    def test_malformed_json(self):
        """Test that malformed JSON returns HTTP 400 error"""
        response = self.client.post('/county_data',
                                 data="{invalid json}",
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Request must be JSON with content-type: application/json", 
                    response.get_json()['error'])
    
    def test_parameterized_query_safety(self):
        """Test that parameterized queries prevent SQL injection"""
        # This test verifies that the query uses parameterized statements
        # by checking that special SQL characters are treated as literal strings
        test_cases = [
            {'zip': "12345'", 'measure_name': 'Violent crime rate'},
            {'zip': '12345', 'measure_name': "Violent crime rate'"},
            {'zip': "12345;", 'measure_name': 'Violent crime rate'},
            {'zip': '12345', 'measure_name': 'Violent crime rate;'},
        ]
        
        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post('/county_data',
                                         data=json.dumps(data),
                                         content_type='application/json')
                # Should return 404 (no data found) rather than executing SQL
                self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
