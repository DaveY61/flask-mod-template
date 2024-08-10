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
from flask import Flask, redirect, url_for, request
from flask_login import LoginManager, current_user
from werkzeug.security import check_password_hash
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
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ADMIN_USER_LIST': ['admin@example.com'],
        'PROJECT_NAME': 'Test Project',
        'EMAIL_FROM_ADDRESS': "pytest@gmail.com",
        'SMTP_SERVER': 'localhost',
        'SMTP_PORT': 1025,
        'SMTP_USERNAME': 'test',
        'SMTP_PASSWORD': 'test',
        'EMAIL_FAIL_DIRECTORY': tempfile.mkdtemp(),
        'DISABLE_SELF_REGISTRATION': False,
        'REQUIRE_LOGIN_FOR_SITE_ACCESS': False,
        'SERVER_NAME': 'localhost',
        'APPLICATION_ROOT': '/', 
        'PREFERRED_URL_SCHEME': 'http',
        'ROLE_LIST': None
    })
    
    app.template_folder = os.path.join(project_path, 'app', 'templates')
    app.register_blueprint(auth_blueprint)
    
    # Register admin blueprint
    from app.services.admin_setup import blueprint as admin_blueprint
    app.register_blueprint(admin_blueprint)

    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return get_user(user_id)
    
    @app.route('/')
    def home():
        return 'Home Page'
    
    @app.before_request
    def require_login():
        if app.config.get('REQUIRE_LOGIN_FOR_SITE_ACCESS', False):
            if not current_user.is_authenticated:
                if request.endpoint and request.endpoint != 'auth.login' and not request.path.startswith('/static'):
                    return redirect(url_for('auth.login', next=request.url))
                
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

def test_disable_self_registration(client, app):
    with app.app_context():
        app.config['DISABLE_SELF_REGISTRATION'] = True
        response = client.get('/register')
        assert response.status_code == 404

def test_require_login_for_site_access(client, app):
    with app.app_context():
        app.config['REQUIRE_LOGIN_FOR_SITE_ACCESS'] = True
        
        # Try accessing the home page without logging in
        response = client.get('/', base_url='http://localhost')
        assert response.status_code == 302
        assert '/login' in response.location

        # Create a user
        user = add_user('test_id', 'testuser', 'test@example.com', 'password', is_active=True)
        
        # Log in using the client
        with client:
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password'
            }, follow_redirects=True)
            assert current_user.is_authenticated

            # Now try accessing the home page again
            response = client.get('/', base_url='http://localhost')
            assert response.status_code == 200  # Should now be able to access the page

@patch('app.services.auth_service.EmailService.send_email')
def test_add_user_setup(mock_send_email, client, app, db):
    with app.app_context():
        # Create admin user
        admin_user = add_user('admin_id', 'admin', 'admin@example.com', 'adminpassword', is_active=True, is_admin=True)
        
        with client:
            # Login as admin
            client.post('/login', data={'email': 'admin@example.com', 'password': 'adminpassword'})
            
            # Add new user
            response = client.post('/setup/users', data={
                'action': 'add_user',
                'new_username': 'newuser',
                'new_email': 'newuser@example.com',
                'new_role': 'test_role'
            })
            assert response.status_code == 200
        
        # Check if user was added
        new_user = get_user_by_email('newuser@example.com')
        assert new_user is not None
        assert new_user.username == 'newuser'
        assert new_user.is_active == False
        assert new_user.user_role == 'test_role'

        # Check if email was sent
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        assert call_args[0] == ['newuser@example.com']
        assert 'Activate your Test Project Account' in call_args[1]
        assert '/create_password/' in call_args[2]

def test_create_password(client, app, db):
    with app.app_context():
        # Add a new inactive user
        user = add_user('new_user_id', 'newuser', 'newuser@example.com', 'temppassword', is_active=False)
        token = generate_token(user.id, 'activation', expiration=None)

        # Test valid token
        response = client.post(f'/create_password/{token}', data={
            'password': 'newpassword',
            'confirm': 'newpassword'
        })
        assert response.status_code == 302
        assert response.location.endswith('/login')

        # Check if user is now active and password is updated
        updated_user = get_user('new_user_id')
        assert updated_user.is_active == True
        assert check_password_hash(updated_user.password, 'newpassword')

        # Test invalid token
        response = client.post('/create_password/invalid_token', data={
            'password': 'newpassword',
            'confirm': 'newpassword'
        })
        assert response.status_code == 404

        # Test already used token
        response = client.post(f'/create_password/{token}', data={
            'password': 'anotherpassword',
            'confirm': 'anotherpassword'
        })
        assert response.status_code == 404

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