#----------------------------------------------------------------------------
# Define "Project" Search Path
#----------------------------------------------------------------------------
import os
import sys

# Determine the path for this project (based on the project name)
vs_project_name = os.environ.get('VS_PROJECT_FOLDER_NAME').lower()
abs_path = os.path.abspath(__file__).lower()
project_path = abs_path.split(vs_project_name)[0] + vs_project_name

# Add the project path to sys.path
sys.path.insert(0, project_path)

#----------------------------------------------------------------------------
# Begin Test Code
#----------------------------------------------------------------------------
import pytest
from app.services.auth_service_db import (
    setup_database, init_db, add_user, get_user, get_user_by_email,
    update_user, delete_user, generate_token, get_token, delete_token,
    update_user_role, update_user_activation, update_user_password
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope='module')
def db():
    config = {
        'USER_DATABASE_PATH': ':memory:'
    }
    setup_database(config)
    init_db()
    return sessionmaker(bind=create_engine('sqlite:///:memory:'))()

def test_add_user(db):
    user = add_user('test_id', 'testuser', 'test@example.com', 'password')
    assert user.id == 'test_id'
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.check_password('password')

def test_get_user(db):
    add_user('get_id', 'getuser', 'get@example.com', 'password')
    user = get_user('get_id')
    assert user.username == 'getuser'

def test_get_user_by_email(db):
    add_user('email_id', 'emailuser', 'email@example.com', 'password')
    user = get_user_by_email('email@example.com')
    assert user.id == 'email_id'

def test_update_user(db):
    user = add_user('update_id', 'updateuser', 'update@example.com', 'password')
    user.username = 'updateduser'
    update_user(user)
    updated_user = get_user('update_id')
    assert updated_user.username == 'updateduser'

def test_delete_user(db):
    add_user('delete_id', 'deleteuser', 'delete@example.com', 'password')
    delete_user('delete_id')
    assert get_user('delete_id') is None

def test_generate_and_get_token(db):
    add_user('token_id', 'tokenuser', 'token@example.com', 'password')
    token = generate_token('token_id', 'activation')
    token_data = get_token(token, 'activation')
    assert token_data.user_id == 'token_id'

def test_delete_token(db):
    add_user('deltoken_id', 'deltokenuser', 'deltoken@example.com', 'password')
    token = generate_token('deltoken_id', 'activation')
    delete_token(token)
    assert get_token(token, 'activation') is None

def test_update_user_role(db):
    add_user('role_id', 'roleuser', 'role@example.com', 'password')
    update_user_role('role_id', 'admin')
    user = get_user('role_id')
    assert user.user_role == 'admin'

def test_update_user_activation(db):
    add_user('activate_id', 'activateuser', 'activate@example.com', 'password', is_active=False)
    update_user_activation('activate_id')
    user = get_user('activate_id')
    assert user.is_active == True

def test_update_user_password(db):
    add_user('password_id', 'passworduser', 'password@example.com', 'oldpassword')
    update_user_password('password_id', 'newpassword')
    user = get_user('password_id')
    assert user.check_password('newpassword')