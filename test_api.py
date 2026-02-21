"""
Unit tests for Traceability Tag Print API
"""

import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestHealthCheck(unittest.TestCase):
    """Test cases for health check endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("app", data)
        self.assertEqual(data["app"], "Traceability Tag Print API")
    
    def test_health_check_response_structure(self):
        """Test that health check response has correct structure"""
        response = self.client.get("/")
        self.assertTrue(isinstance(response.json(), dict))
        self.assertIn("status", response.json())


class TestAPIStructure(unittest.TestCase):
    """Test cases for API structure and routes"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_api_is_running(self):
        """Test that the API is running"""
        response = self.client.get("/")
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404"""
        response = self.client.get("/invalid-endpoint")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
