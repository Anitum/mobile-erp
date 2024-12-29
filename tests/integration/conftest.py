import pytest
import os
import shutil
from app import create_app, db

@pytest.fixture(autouse=True)
def setup_test_environment(app):
    """Setup test environment before each test"""
    # Create test upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    yield
    
    # Cleanup after tests
    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)

@pytest.fixture
def test_password():
    return 'test-password123'

@pytest.fixture
def test_email():
    return 'test@example.com'