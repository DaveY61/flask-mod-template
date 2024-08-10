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
from flask import Flask
from flask_login import LoginManager, login_user, current_user
from app.services.auth_service import blueprint as auth_blueprint
from app.services.auth_service_db import add_user, get_user_by_email, update_user_activation, setup_database, init_db, get_base, generate_token, get_user
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile

@pytest.fixture(scope='function')
def db():
    config = {
        'USER_DATABASE_PATH': ':memory:'
    }
    setup_database(config)
    init_db()

    Base, User, Token, DefaultRole = get_base()
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def app(db):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['ADMIN_USER_LIST'] = ['admin@example.com']
    app.config['PROJECT_NAME'] = 'Test Project'
    app.config['EMAIL_FROM_ADDRESS'] = "pytest@gmail.com"
    app.config['SMTP_SERVER'] = 'localhost'
    app.config['SMTP_PORT'] = 1025
    app.config['SMTP_USERNAME'] = 'test'
    app.config['SMTP_PASSWORD'] = 'test'
    app.config['EMAIL_FAIL_DIRECTORY'] = tempfile.mkdtemp()
    app.config['DISABLE_SELF_REGISTRATION'] = False
    app.template_folder = os.path.join(project_path, 'app', 'templates')
    app.register_blueprint(auth_blueprint)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return get_user(user_id)
    
    @app.route('/')
    def home():
        return 'Home Page'
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_smtp(monkeypatch):
    class MockSMTP:
        def __init__(self, *args, **kwargs):
            pass
        def starttls(self):
            pass
        def login(self, *args, **kwargs):
            pass
        def send_message(self, *args, **kwargs):
            pass
        def quit(self):
            pass
    monkeypatch.setattr('smtplib.SMTP', MockSMTP)

@patch('app.services.auth_service.EmailService.send_email')
def test_register(mock_send_email, client, app, db):
    with app.app_context():
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        assert response.status_code == 201
        user = get_user_by_email('test@example.com')
        assert user is not None
        assert user.username == 'testuser'
        assert not user.is_active
        mock_send_email.assert_called_once()

def test_activate_account(client, app, db):
    with app.app_context():
        user = add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=False)
        token = generate_token(user.id, 'activation')
        response = client.get(f'/activate/{token}')
        assert response.status_code == 200
        updated_user = get_user_by_email('test@example.com')
        assert updated_user.is_active

def test_login(client, app, db):
    with app.app_context():
        add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=True)
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        assert response.status_code == 302  # Redirect after successful login

def test_logout(client, app, db):
    with app.app_context():
        user = add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=True)
        with client:
            with client.session_transaction() as session:
                session['_user_id'] = user.id
            response = client.get('/logout')
            assert response.status_code == 302  # Redirect after logout
            with client.session_transaction() as session:
                assert '_user_id' not in session

@patch('app.services.auth_service.EmailService.send_email')
def test_forgot_password(mock_send_email, mock_smtp, client, app, db):
    with app.app_context():
        add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=True)
        response = client.post('/forgot', data={
            'email': 'test@example.com'
        })
        assert response.status_code == 200
        mock_send_email.assert_called_once()

def test_reset_password(client, app, db):
    with app.app_context():
        user = add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=True)
        token = generate_token(user.id, 'reset')
        response = client.post(f'/reset_password/{token}', data={
            'password': 'newpassword'
        })
        assert response.status_code == 200
        updated_user = get_user_by_email('test@example.com')
        assert updated_user.check_password('newpassword')

def test_delete_account(client, app, db):
    with app.app_context():
        user = add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=True)
        with client:
            with client.session_transaction() as session:
                session['_user_id'] = user.id  # Use '_user_id' instead of 'user_id'
            response = client.post('/delete')
            assert response.status_code == 200
            deleted_user = get_user_by_email('test@example.com')
            assert deleted_user is None

@patch('app.services.auth_service.EmailService.send_email')
def test_register_with_default_role(mock_send_email, client, app, db):
    with app.app_context():
        app.config['ROLE_LIST'] = [{'name': 'default_role', 'modules': []}]
        with patch('app.services.auth_service.get_default_role', return_value='default_role'):
            response = client.post('/register', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'testpassword'
            })
            assert response.status_code == 201
            user = get_user_by_email('test@example.com')
            assert user is not None
            assert user.user_role == 'default_role'
            mock_send_email.assert_called_once()

def test_login_updates_admin_status(client, app, db):
    with app.app_context():
        user = add_user('test_id', 'adminuser', 'admin@example.com', 'testpassword', is_active=True, is_admin=False)
        update_user_activation(user.id)
        response = client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'testpassword'
        })
        assert response.status_code == 302  # Redirect after successful login
        updated_user = get_user_by_email('admin@example.com')
        assert updated_user.is_admin == True

def test_register_duplicate_email(client, app, db):
    with app.app_context():
        add_user('test_id', 'testuser', 'test@example.com', 'testpassword')
        response = client.post('/register', data={
            'username': 'testuser2',
            'email': 'test@example.com',
            'password': 'testpassword2'
        })
        assert response.status_code == 400  # Bad request for duplicate email

def test_login_inactive_user(client, app, db):
    with app.app_context():
        add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=False)
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        assert response.status_code == 400  # Bad request for inactive user

def test_reset_password_expired_token(client, app, db):
    with app.app_context():
        user = add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=True)
        token = generate_token(user.id, 'reset')
        
        # Simulate token expiration
        with patch('app.services.auth_service.get_token', return_value=None):
            response = client.post(f'/reset_password/{token}', data={
                'password': 'newpassword'
            })
            assert response.status_code == 400  # Bad request for expired token

def test_user_allowed_modules(client, app, db):
    with app.app_context():
        app.config['ROLE_LIST'] = [{'name': 'test_role', 'modules': ['module1', 'module2']}]
        app.config['MODULE_LIST'] = [
            {'name': 'module1', 'enabled': True},
            {'name': 'module2', 'enabled': True},
            {'name': 'module3', 'enabled': True}
        ]
        user = add_user('test_id', 'testuser', 'test@example.com', 'testpassword', is_active=True, user_role='test_role')
        with client:
            with client.session_transaction() as session:
                session['user_id'] = user.id
            allowed_modules = user.get_allowed_modules()
            assert set(allowed_modules) == {'module1', 'module2'}