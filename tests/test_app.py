"""
Test suite for the High School Management System API

Tests all endpoints and functionality including:
- Root redirect
- Getting activities
- Signing up for activities
- Unregistering from activities
- Error handling and validation
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent / "src"))
from src.app import app

# Create a test client
client = TestClient(app)


class TestRootEndpoint:
    """Test the root endpoint redirect"""
    
    def test_root_redirect(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_all_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains expected activities
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data
        
    def test_activity_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check one activity has required fields
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        
    def test_activity_participants_is_list(self):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student(self):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]
        
    def test_signup_already_enrolled(self):
        """Test that a student cannot sign up twice"""
        # First signup
        response1 = client.post(
            "/activities/Programming Class/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Try to signup again - should fail
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        
    def test_signup_nonexistent_activity(self):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_signup_response_format(self):
        """Test the response format of a successful signup"""
        response = client.post(
            "/activities/Gym Class/signup",
            params={"email": "newgym@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert "newgym@mergington.edu" in data["message"]
        assert "Gym Class" in data["message"]


class TestUnregisterEndpoint:
    """Test the DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_enrolled_student(self):
        """Test unregistering an enrolled student"""
        # First sign up
        client.post(
            "/activities/Soccer Club/signup",
            params={"email": "soccer@mergington.edu"}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Soccer Club/signup",
            params={"email": "soccer@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
    def test_unregister_not_enrolled(self):
        """Test that unregistering a non-enrolled student fails"""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
        
    def test_unregister_nonexistent_activity(self):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Fake Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_unregister_response_format(self):
        """Test the response format of a successful unregister"""
        # First sign up
        client.post(
            "/activities/Theater Club/signup",
            params={"email": "theater@mergington.edu"}
        )
        
        # Then unregister and check format
        response = client.delete(
            "/activities/Theater Club/signup",
            params={"email": "theater@mergington.edu"}
        )
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        assert "theater@mergington.edu" in data["message"]
        assert "Theater Club" in data["message"]


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_signup_and_verify_in_activity(self):
        """Test that after signup, student appears in activity participants"""
        email = "integration@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Debate Team/signup",
            params={"email": email}
        )
        
        # Get activities and verify student is in participants
        response = client.get("/activities")
        activity = response.json()["Debate Team"]
        assert email in activity["participants"]
        
    def test_unregister_and_verify_removal(self):
        """Test that after unregistration, student is removed from activity"""
        email = "removal@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Science Club/signup",
            params={"email": email}
        )
        
        # Unregister
        client.delete(
            "/activities/Science Club/signup",
            params={"email": email}
        )
        
        # Get activities and verify student is removed
        response = client.get("/activities")
        activity = response.json()["Science Club"]
        assert email not in activity["participants"]