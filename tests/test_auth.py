import sys
import os
import uuid
os.environ["TESTING"] = "1"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Har run ke liye unique username
TEST_USERNAME = f"test_{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = "test123456"

def test_register_success():
    response = client.post("/auth/register", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == TEST_USERNAME
    assert "password" not in data["data"]

def test_register_duplicate():
    response = client.post("/auth/register", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert "already taken" in data["error"]["message"]

def test_register_short_password():
    response = client.post("/auth/register", json={
        "username": "newuser",
        "password": "123"
    })
    assert response.status_code == 422

def test_login_success():
    response = client.post("/auth/login", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

def test_login_wrong_password():
    response = client.post("/auth/login", json={
        "username": TEST_USERNAME,
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_refresh_token():
    login_res = client.post("/auth/login", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    refresh_token = login_res.json()["data"]["refresh_token"]
    response = client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

def test_refresh_invalid_token():
    response = client.post("/auth/refresh", json={
        "refresh_token": "invalid.token.here"
    })
    assert response.status_code == 401