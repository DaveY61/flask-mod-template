
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
import logging
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from freezegun import freeze_time
from flask import Flask
from app.services.log_service import init_logger, setup_logger, HeaderFileHandler, EmailHandler, RequestFormatter

def patch_get_current_date(frozen_datetime):
    return lambda self: frozen_datetime.date()

@pytest.fixture
def app():
    app = Flask(__name__)
    temp_dir = tempfile.mkdtemp()
    app.config.update({
        'TESTING': True,
        'LOG_FILE_DIRECTORY': temp_dir,
        'LOG_RETENTION_DAYS': 7,
        'LOG_EMAIL_ENABLE': False,
        'ADMIN_USER_LIST': ['admin@example.com'],
        'EMAIL_FROM_ADDRESS': 'test@example.com',
        'SMTP_SERVER': 'smtp.example.com',
        'SMTP_PORT': 587,
        'SMTP_USERNAME': 'test_user',
        'SMTP_PASSWORD': 'test_password',
        'LOG_FILE_LEVEL': 'INFO',
        'SERVER_NAME': 'localhost',
        'APPLICATION_ROOT': '/',
        'PREFERRED_URL_SCHEME': 'http'
    })
    yield app

    # Cleanup
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
        if isinstance(handler, logging.FileHandler):
            handler.close()
    shutil.rmtree(temp_dir, ignore_errors=True)

# Setup and Initialization Tests

def test_init_logger(app):
    with app.app_context():
        init_logger(app)
        assert os.path.isabs(app.config['LOG_FILE_DIRECTORY'])
        assert any(isinstance(h, HeaderFileHandler) for h in app.logger.handlers)

def test_setup_logger(app):
    with app.app_context():
        handlers = setup_logger(app)
        assert any(isinstance(h, HeaderFileHandler) for h in handlers)
        assert app.logger.level == logging.DEBUG

def test_multiple_setup_logger_calls(app):
    with app.app_context():
        initial_handlers = setup_logger(app)
        second_call_handlers = setup_logger(app)
        assert len(second_call_handlers) == len(initial_handlers)
        assert set(type(h) for h in second_call_handlers) == set(type(h) for h in initial_handlers)

# Formatter Tests

def test_request_formatter_without_context(app):
    with app.app_context():
        formatter = RequestFormatter('%(url)s - %(remote_addr)s - %(user_id)s - %(user_email)s - %(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='Test message', args=(), exc_info=None
        )
        formatted = formatter.format(record)
        assert 'None - None - N/A - N/A - Test message' in formatted

@patch('flask_login.utils._get_user')
def test_request_formatter_with_context(mock_get_user, app):
    mock_user = MagicMock(is_authenticated=True, id='123', email='test@example.com')
    mock_get_user.return_value = mock_user
    with app.app_context():
        formatter = RequestFormatter('%(url)s - %(remote_addr)s - %(user_id)s - %(user_email)s - %(message)s')
        with app.test_request_context('/test', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            record = logging.LogRecord(
                name='test', level=logging.INFO, pathname='', lineno=0,
                msg='Test message', args=(), exc_info=None
            )
            formatted = formatter.format(record)
            assert 'http://localhost/test - 127.0.0.1 - 123 - test@example.com - Test message' in formatted

# File Handling Tests

def test_log_file_creation(app):
    with app.app_context():
        setup_logger(app)
        file_handler = next((h for h in app.logger.handlers if isinstance(h, HeaderFileHandler)), None)
        assert file_handler is not None
        log_file_path = file_handler.baseFilename
        
        app.logger.info("Test log message")
        
        assert os.path.exists(log_file_path)
        with open(log_file_path, 'r') as f:
            content = f.read()
        assert "Test log message" in content

def test_log_file_rollover(app):
    with freeze_time("2023-01-01 23:59:59") as frozen_time:
        with app.app_context():
            with patch.object(HeaderFileHandler, 'get_current_date', new=patch_get_current_date(frozen_time())):
                setup_logger(app)
                app.logger.info("Day 1 log")

                day1_log = os.path.join(app.config['LOG_FILE_DIRECTORY'], "app_2023-01-01.log")
                assert os.path.exists(day1_log)

                # Move time to just after midnight
                frozen_time.move_to("2023-01-02 00:00:01")

                # Update the patched get_current_date method
                HeaderFileHandler.get_current_date = patch_get_current_date(frozen_time())

                app.logger.info("Day 2 log")
                day2_log = os.path.join(app.config['LOG_FILE_DIRECTORY'], "app_2023-01-02.log")
                assert os.path.exists(day2_log)

# Log Level Tests

def test_log_levels(app):
    app.config['LOG_FILE_LEVEL'] = 'DEBUG'
    with app.app_context():
        setup_logger(app)
        with patch.object(app.logger.handlers[0], 'emit') as mock_emit:
            app.logger.debug("Debug message")
            app.logger.info("Info message")
            app.logger.warning("Warning message")
            app.logger.error("Error message")
            app.logger.critical("Critical message")
            
            assert mock_emit.call_count == 5
            log_levels = [mock_emit.call_args_list[i][0][0].levelname for i in range(5)]
            assert log_levels == ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

# Email Handler Tests

@patch('smtplib.SMTP')
def test_email_handler_creation(mock_smtp, app):
    app.config['LOG_EMAIL_ENABLE'] = True
    with app.app_context():
        handlers = setup_logger(app)
        email_handlers = [h for h in handlers if isinstance(h, EmailHandler)]
        assert len(email_handlers) == 1
        email_handler = email_handlers[0]
        assert email_handler.level == logging.ERROR
        assert email_handler.config['SMTP_SERVER'] == app.config['SMTP_SERVER']
        assert email_handler.config['SMTP_PORT'] == app.config['SMTP_PORT']

@patch('smtplib.SMTP')
def test_email_error_log(mock_smtp, app):
    app.config['LOG_EMAIL_ENABLE'] = True
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    with app.app_context():
        setup_logger(app)
        with patch.object(EmailHandler, 'send_email') as mock_send_email:
            app.logger.error("Test error message")
            mock_send_email.assert_called_once()

@patch('smtplib.SMTP')
def test_email_handler_log_levels(mock_smtp, app):
    app.config['LOG_EMAIL_ENABLE'] = True
    app.config['LOG_EMAIL_LEVEL'] = 'ERROR'
    with app.app_context():
        setup_logger(app)
        with patch.object(EmailHandler, 'send_email') as mock_send_email:
            app.logger.warning("This shouldn't trigger an email")
            app.logger.error("This should trigger an email")
            app.logger.critical("This should also trigger an email")
            
            assert mock_send_email.call_count == 2
            call_args = mock_send_email.call_args_list
            assert "This should trigger an email" in str(call_args[0])
            assert "This should also trigger an email" in str(call_args[1])
            
# Comprehensive Test

def test_comprehensive_log_handling(app):
    with freeze_time("2023-01-01 23:59:59") as frozen_time:
        log_dir = app.config['LOG_FILE_DIRECTORY']
        
        with app.app_context():
            with patch.object(HeaderFileHandler, 'get_current_date', new=patch_get_current_date(frozen_time())):
                setup_logger(app)
                
                # Test log creation and content
                app.logger.info("First log entry")
                log_file = os.path.join(log_dir, "app_2023-01-01.log")
                assert os.path.exists(log_file)
                with open(log_file, 'r') as f:
                    content = f.read()
                    assert content.startswith("Timestamp\tLog Level\tModule\tMessage\t")
                    assert "First log entry" in content
                
                # Test log rollover
                frozen_time.move_to("2023-01-02 00:00:01")
                
                # Update the patched get_current_date method
                HeaderFileHandler.get_current_date = patch_get_current_date(frozen_time())
                
                app.logger.info("New day log entry")
                new_log_file = os.path.join(log_dir, "app_2023-01-02.log")
                assert os.path.exists(new_log_file)
            
            # Test old log clearing
            old_dates = [datetime(2023, 1, 1) - timedelta(days=i) for i in range(1, 10)]
            for date in old_dates:
                with open(os.path.join(log_dir, f"app_{date.strftime('%Y-%m-%d')}.log"), 'w') as f:
                    f.write("Old log content")
            
            print("Log files before cleanup:", sorted(os.listdir(log_dir)))
            
            frozen_time.move_to("2023-01-08 00:00:01")
            HeaderFileHandler.get_current_date = patch_get_current_date(frozen_time())
            setup_logger(app)  # This should trigger old log clearing
            
            log_files = sorted(os.listdir(log_dir))
            print("Log files after cleanup:", log_files)
            
            assert len(log_files) == 8  # 7 old files + 1 new file
            print(f"Oldest file: {log_files[0]}")
            print(f"Newest file: {log_files[-1]}")
            
            assert log_files[0] == 'app_2022-12-27.log'  # Oldest file
            assert log_files[-1] == 'app_2023-01-08.log'  # Newest file

def test_midnight_rollover(app):
    with freeze_time("2023-01-01 23:59:59") as frozen_time:
        with app.app_context():
            with patch.object(HeaderFileHandler, 'get_current_date', new=patch_get_current_date(frozen_time())):
                setup_logger(app)
                app.logger.info("Just before midnight")
                
                day1_log = os.path.join(app.config['LOG_FILE_DIRECTORY'], "app_2023-01-01.log")
                assert os.path.exists(day1_log)
                
                # Move time to exactly midnight
                frozen_time.move_to("2023-01-02 00:00:00")
                HeaderFileHandler.get_current_date = patch_get_current_date(frozen_time())
                app.logger.info("Exactly at midnight")
                
                # Move time to just after midnight
                frozen_time.move_to("2023-01-02 00:00:01")
                HeaderFileHandler.get_current_date = patch_get_current_date(frozen_time())
                app.logger.info("Just after midnight")
                
                day2_log = os.path.join(app.config['LOG_FILE_DIRECTORY'], "app_2023-01-02.log")
                assert os.path.exists(day2_log)
            
            # Check contents of both logs
            with open(day1_log, 'r') as f:
                content = f.read()
                assert "Just before midnight" in content
                assert "Exactly at midnight" not in content
            
            with open(day2_log, 'r') as f:
                content = f.read()
                assert "Exactly at midnight" in content
                assert "Just after midnight" in content