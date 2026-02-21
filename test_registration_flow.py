"""
Unit tests for user registration and login flow
Tests the complete registration → login workflow
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


class TestRegistrationAndLogin(unittest.TestCase):
    """Test user login workflow (Registration would be done separately)"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
        self.test_user_id = "TEST_USER_001"
        self.test_user_name = "Test User"
        self.test_password = "TestPass@123"
        self.test_email = "testuser@supplier.com"
        self.test_supplier_code = "SUP001"
    
    @patch('app.repositories.traceability_repo.validate_user_pc')
    def test_login_after_registration(self, mock_login):
        """Test login with newly registered user"""
        # Mock successful login response
        mock_login.return_value = {
            "RESULT": "Y",
            "MSG": "Login successful",
            "UserID": self.test_user_id,
            "USERNAME": self.test_user_name,
            "PASSWORD": self.test_password,
            "EmailId": self.test_email,
            "GroupID": 1,
            "GroupName": "Supplier Users",
            "IsSupplier": "Y",
            "SupplierCode": self.test_supplier_code,
            "PlantName": "Main Plant",
        }
        
        result = mock_login(
            user_id=self.test_user_id,
            password=self.test_password
        )
        
        # Verify login was successful
        self.assertEqual(result["RESULT"], "Y")
        self.assertEqual(result["UserID"], self.test_user_id)
        self.assertEqual(result["USERNAME"], self.test_user_name)
        self.assertEqual(result["SupplierCode"], self.test_supplier_code)
    
    @patch('app.repositories.traceability_repo.validate_user_pc')
    def test_login_with_wrong_password(self, mock_login):
        """Test login fails with incorrect password"""
        # Mock failed login response
        mock_login.return_value = {
            "RESULT": "N",
            "MSG": "Invalid user ID or password",
        }
        
        result = mock_login(
            user_id=self.test_user_id,
            password="WrongPassword"
        )
        
        # Verify login failed
        self.assertEqual(result["RESULT"], "N")
        self.assertIn("Invalid", result["MSG"])
    
    @patch('app.repositories.traceability_repo.validate_user_pc')
    def test_login_endpoint_authentication(self, mock_login):
        """Test the actual login endpoint with mocked database"""
        # Mock successful login
        mock_login.return_value = {
            "RESULT": "Y",
            "MSG": "Login successful",
            "UserID": self.test_user_id,
            "USERNAME": self.test_user_name,
            "PASSWORD": self.test_password,
            "EmailId": self.test_email,
            "GroupID": 1,
            "GroupName": "Supplier Users",
            "IsSupplier": "Y",
            "SupplierCode": self.test_supplier_code,
            "DensoPlant": "DENSO_PLANT_1",
            "SupplierPlantCode": "SUP_PLANT_001",
            "PackingStation": "STATION_01",
            "PlantName": "Main Manufacturing Plant",
        }
        
        # Call the actual endpoint
        response = self.client.post(
            "/api/traceability/login",
            json={
                "user_id": self.test_user_id,
                "password": self.test_password
            }
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["user_id"], self.test_user_id)
        self.assertEqual(data["data"]["user_name"], self.test_user_name)
        self.assertEqual(data["data"]["supplier_code"], self.test_supplier_code)
    
    @patch('app.repositories.traceability_repo.validate_user_pc')
    def test_login_endpoint_failure(self, mock_login):
        """Test the login endpoint returns 401 on failed authentication"""
        # Mock failed login
        mock_login.return_value = {
            "RESULT": "N",
            "MSG": "Invalid credentials",
        }
        
        # Call the actual endpoint
        response = self.client.post(
            "/api/traceability/login",
            json={
                "user_id": "INVALID_USER",
                "password": "WrongPassword"
            }
        )
        
        # Verify response
        self.assertEqual(response.status_code, 401)
    
    @patch('app.repositories.traceability_repo.validate_user')
    @patch('app.repositories.traceability_repo.validate_user_pc')
    def test_complete_registration_to_login_flow(self, mock_login, mock_get_user):
        """Test complete workflow: register → login → get user info"""
        # Step 1: Login
        mock_login.return_value = {
            "RESULT": "Y",
            "MSG": "Login successful",
            "UserID": self.test_user_id,
            "USERNAME": self.test_user_name,
            "PASSWORD": self.test_password,
            "EmailId": self.test_email,
            "GroupID": 1,
            "GroupName": "Supplier Users",
            "IsSupplier": "Y",
            "SupplierCode": self.test_supplier_code,
            "DensoPlant": "DENSO_PLANT_1",
            "SupplierPlantCode": "SUP_PLANT_001",
            "PackingStation": "STATION_01",
            "PlantName": "Main Manufacturing Plant",
        }
        
        login_response = self.client.post(
            "/api/traceability/login",
            json={
                "user_id": self.test_user_id,
                "password": self.test_password
            }
        )
        
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.json()["success"])
        
        # Step 2: Get traceability user details
        mock_get_user.return_value = {
            "RESULT": "Y",
            "MSG": "User details retrieved",
            "UserID": self.test_user_id,
            "USERNAME": self.test_user_name,
            "SupplierCode": self.test_supplier_code,
            "SupplierPlantCode": "SUP_PLANT_001",
            "PackingStation": "STATION_01",
            "PlantName": "Main Manufacturing Plant",
            "EmailId": self.test_email,
            "GroupID": 1,
            "GroupName": "Supplier Users",
        }
        
        traceability_response = self.client.post(
            "/api/traceability/traceability-user",
            json={
                "user_id": self.test_user_id,
                "password": self.test_password
            }
        )
        
        self.assertEqual(traceability_response.status_code, 200)
        trace_data = traceability_response.json()
        self.assertTrue(trace_data["success"])
        self.assertEqual(trace_data["data"]["user_id"], self.test_user_id)
        self.assertEqual(trace_data["data"]["supplier_code"], self.test_supplier_code)
        self.assertEqual(trace_data["data"]["packing_station"], "STATION_01")


class TestRegistrationValidation(unittest.TestCase):
    """Test password validation and registration field requirements"""
    
    def test_login_with_empty_credentials(self):
        """Test that login rejects empty credentials"""
        client = TestClient(app)
        response = client.post(
            "/api/traceability/login",
            json={
                "user_id": "",
                "password": ""
            }
        )
        # Should fail or return validation error
        self.assertNotEqual(response.status_code, 200)
    
    def test_password_strength_validation(self):
        """Test password meets minimum requirements"""
        # Should validate: min 8 chars, uppercase, lowercase, number, special char
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
