#----------------------------------------------------------------------------
# Define "Project" Search Path
#----------------------------------------------------------------------------
import os
import sys
from dotenv import load_dotenv

# Determine the path for this project (based on the project name)
load_dotenv()
vs_project_name = os.environ.get('VS_PROJECT_FOLDER_NAME').lower()
abs_path = os.path.abspath(__file__).lower()
project_path = abs_path.split(vs_project_name)[0] + vs_project_name

# Add the project path to sys.path
sys.path.insert(0, project_path)

#----------------------------------------------------------------------------
# Begin Test Code
#----------------------------------------------------------------------------
import pytest
from datetime import datetime

from app import create_app
from services.auth_service import init_db, get_db

# Define user credentials to test "Register"
reg_username = "testuser"
reg_email = "reg_test@example.com"
reg_password = "password123"

# Define user credentials to test "Activate" and other endpoints
username = "testuser"
email = "test@example.com"
password = "password123"

@pytest.fixture(scope='module', autouse=True)
def setup_client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_register(setup_client):
    client = setup_client

    # First registration attempt
    response = client.post('/register', data={
        "username": reg_username,
        "email": reg_email,
        "password": reg_password
    })
    assert response.status_code == 201

    # Second registration attempt with the same email should fail
    response = client.post('/register', data={
        "username": reg_username,
        "email": reg_email,
        "password": reg_password
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_activate(setup_client):
    client = setup_client

    # Register a new user
    response = client.post('/register', data={
        "username": username,
        "email": email,
        "password": password
    })
    assert response.status_code == 201

    # Retrieve the activation token from the database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT token, expires_at FROM tokens WHERE token_type='activation'")
    token, expires_at = cursor.fetchone()
    conn.close()

    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)

    assert expires_at > datetime.now(), "Activation token has expired"

    # Activate the user
    response = client.get(f'/activate/{token}')
    assert response.status_code == 200, f"Failed to activate with token: {response.data.decode('utf-8')}"
    data = response.get_json()
    assert 'message' in data

def test_login(setup_client):
    client = setup_client
    response = client.post('/login', data={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_forgot_password(setup_client):
    client = setup_client
    response = client.post('/forgot_password', data={
        "email": email
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_remove_account(setup_client):
    client = setup_client
    response = client.post('/remove_account', data={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

if __name__ == "__main__":
    pytest.main()
