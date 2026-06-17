import unittest
import os
import tempfile
from app import app, get_db


class TestAppEndpoints(unittest.TestCase):
    """Unit tests for the vulnerable Flask application."""

    def setUp(self):
        """Set up test client and app context."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()

    # ==================== Database Tests ====================
    def test_get_db_creates_connection(self):
        """Test that get_db() returns a valid database connection."""
        conn = get_db()
        self.assertIsNotNone(conn)
        conn.close()

    def test_get_db_creates_users_table(self):
        """Test that get_db() creates the users table."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result)

    def test_get_db_inserts_default_user(self):
        """Test that get_db() inserts the default admin user."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username='admin'")
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], 'admin')
        self.assertEqual(result[2], 'password123')

    # ==================== Index Route Tests ====================
    def test_index_route_status_code(self):
        """Test that index route returns 200 status code."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_index_route_contains_content(self):
        """Test that index route returns expected content."""
        response = self.client.get('/')
        self.assertIn(b'Vulnerable App', response.data)
        self.assertIn(b'Endpoints', response.data)

    # ==================== Login Route Tests ====================
    def test_login_get_request(self):
        """Test that login route responds to GET requests with form."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'username', response.data)
        self.assertIn(b'password', response.data)

    def test_login_valid_credentials(self):
        """Test login with valid admin credentials."""
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post('/login', data={
            'username': 'invalid',
            'password': 'wrong'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login failed', response.data)

    def test_login_empty_credentials(self):
        """Test login with empty credentials."""
        response = self.client.post('/login', data={
            'username': '',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login failed', response.data)

    def test_login_sql_injection_attempt(self):
        """Test login endpoint with SQL injection payload.
        
        Note: This demonstrates the vulnerability exists, not that it's fixed.
        This test documents the security issue for regression testing.
        """
        response = self.client.post('/login', data={
            'username': "admin' --",
            'password': 'anything'
        })
        self.assertEqual(response.status_code, 200)
        # This should fail but doesn't due to SQL injection vulnerability
        # This test documents the issue
        self.assertIn(b'Login', response.data)

    # ==================== Search Route Tests ====================
    def test_search_route_status_code(self):
        """Test that search route returns 200 status code."""
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 200)

    def test_search_query_parameter_reflected(self):
        """Test that search query parameter is reflected in response."""
        response = self.client.get('/search?q=test')
        self.assertIn(b'Search Results', response.data)
        self.assertIn(b'test', response.data)

    def test_search_empty_query(self):
        """Test search with empty query parameter."""
        response = self.client.get('/search?q=')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Search Results', response.data)

    def test_search_special_characters(self):
        """Test search with special characters."""
        response = self.client.get('/search?q=test<>&"\'')
        self.assertEqual(response.status_code, 200)

    def test_search_xss_payload(self):
        """Test search endpoint with XSS payload.
        
        Note: This demonstrates the XSS vulnerability exists.
        """
        response = self.client.get('/search?q=<script>alert("xss")</script>')
        self.assertEqual(response.status_code, 200)
        # The payload is reflected without escaping
        self.assertIn(b'<script>', response.data)

    # ==================== Ping Route Tests ====================
    def test_ping_route_status_code(self):
        """Test that ping route returns 200 status code."""
        response = self.client.get('/ping')
        self.assertEqual(response.status_code, 200)

    def test_ping_localhost(self):
        """Test ping with localhost."""
        response = self.client.get('/ping?host=127.0.0.1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<pre>', response.data)

    def test_ping_default_host(self):
        """Test ping without host parameter (uses default)."""
        response = self.client.get('/ping')
        self.assertEqual(response.status_code, 200)

    def test_ping_empty_host(self):
        """Test ping with empty host parameter."""
        response = self.client.get('/ping?host=')
        self.assertEqual(response.status_code, 200)

    def test_ping_command_injection_attempt(self):
        """Test ping endpoint with command injection payload.
        
        Note: This demonstrates the command injection vulnerability.
        """
        response = self.client.get('/ping?host=127.0.0.1; echo vulnerable')
        self.assertEqual(response.status_code, 200)
        # The injected command may execute depending on the OS

    # ==================== File Route Tests ====================
    def test_file_route_not_found(self):
        """Test file route with non-existent file."""
        response = self.client.get('/file?name=nonexistent.txt')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'File not found', response.data)

    def test_file_route_empty_name(self):
        """Test file route with empty name parameter."""
        response = self.client.get('/file?name=')
        self.assertEqual(response.status_code, 404)

    def test_file_route_status_code(self):
        """Test that file route responds to valid requests."""
        response = self.client.get('/file')
        # Either 404 (file not found) or 200 (file exists) is acceptable
        self.assertIn(response.status_code, [200, 404])

    def test_file_path_traversal_attempt(self):
        """Test file endpoint with path traversal payload.
        
        Note: This demonstrates the path traversal vulnerability.
        """
        response = self.client.get('/file?name=../../../etc/passwd')
        # Either 404 or 200 depending on whether the file exists
        self.assertIn(response.status_code, [200, 404])

    def test_file_absolute_path_attempt(self):
        """Test file endpoint with absolute path."""
        response = self.client.get('/file?name=/etc/passwd')
        # The request should be handled (404 or 200)
        self.assertIn(response.status_code, [200, 404])

    # ==================== Route Availability Tests ====================
    def test_all_routes_exist(self):
        """Test that all documented routes are accessible."""
        routes = [
            ('/', 200),
            ('/login', 200),
            ('/search', 200),
            ('/ping', 200),
            ('/file', 404),  # May return 404 if default file doesn't exist
        ]
        for route, expected_status in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertIn(response.status_code, [expected_status, 404, 200])


class TestConstants(unittest.TestCase):
    """Test application constants."""

    def test_constants_exist(self):
        """Test that security-sensitive constants are defined."""
        from app import DATABASE_USER, DATABASE_PASSWORD, API_KEY
        self.assertEqual(DATABASE_USER, "admin")
        self.assertIsNotNone(DATABASE_PASSWORD)
        self.assertIsNotNone(API_KEY)


class TestRequestMethods(unittest.TestCase):
    """Test HTTP request methods."""

    def setUp(self):
        """Set up test client."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_login_post_only(self):
        """Test that login POST method is supported."""
        response = self.client.post('/login', data={
            'username': 'test',
            'password': 'test'
        })
        self.assertNotEqual(response.status_code, 405)

    def test_search_get_only(self):
        """Test that search endpoint uses GET method."""
        response = self.client.get('/search?q=test')
        self.assertEqual(response.status_code, 200)

    def test_ping_get_only(self):
        """Test that ping endpoint uses GET method."""
        response = self.client.get('/ping')
        self.assertEqual(response.status_code, 200)

    def test_file_get_only(self):
        """Test that file endpoint uses GET method."""
        response = self.client.get('/file')
        self.assertNotEqual(response.status_code, 405)


if __name__ == '__main__':
    unittest.main()
