
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
from flask import Flask, request
from app.services.log_service import init_logger, setup_logger, HeaderFileHandler, EmailHandler, RequestFormatter
from unittest.mock import patch, MagicMock
import tempfile
import logging
from freezegun import freeze_time
from datetime import datetime, timedelta
import shutil

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

    with app.app_context():
        setup_logger(app)

    yield app

    # Cleanup after tests
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
        if isinstance(handler, logging.FileHandler):
            handler.close()
    shutil.rmtree(temp_dir, ignore_errors=True)

    # Clean up any other temporary directories created during tests
    for root, dirs, files in os.walk(tempfile.gettempdir(), topdown=False):
        for name in dirs:
            if name.startswith('pytest-of-'):
                try:
                    shutil.rmtree(os.path.join(root, name), ignore_errors=True)
                except Exception as e:
                    print(f"Failed to remove directory {name}: {e}")

def test_setup_logger(app):
    with app.app_context():
        handlers = setup_logger(app)
        assert any(isinstance(h, HeaderFileHandler) for h in handlers)
        assert app.logger.level == logging.DEBUG

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

def test_log_format(app):
    with app.app_context():
        setup_logger(app)
        with patch.object(app.logger.handlers[0], 'emit') as mock_emit:
            app.logger.info("Test log message")
            record = mock_emit.call_args[0][0]
            assert 'Test log message' in record.getMessage()
            assert record.levelname == 'INFO'

@patch('smtplib.SMTP')
def test_email_error_log(mock_smtp, app):
    app.config['LOG_EMAIL_ENABLE'] = True
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    with app.app_context():
        handlers = setup_logger(app)
        email_handler = next((h for h in handlers if isinstance(h, EmailHandler)), None)
        assert email_handler is not None
        
        with patch.object(EmailHandler, 'send_email') as mock_send_email:
            app.logger.error("Test error message")
            mock_send_email.assert_called_once()

def test_console_logging_in_debug_mode(app):
    app.debug = True
    with app.app_context():
        handlers = setup_logger(app)
        handler_types = [type(h) for h in handlers]
        assert HeaderFileHandler in handler_types
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

def test_multiple_setup_logger_calls(app):
    with app.app_context():
        initial_handlers = setup_logger(app)
        second_call_handlers = setup_logger(app)
        assert len(second_call_handlers) == len(initial_handlers)
        assert set(type(h) for h in second_call_handlers) == set(type(h) for h in initial_handlers)

def test_email_handler_creation(app):
    app.config['LOG_EMAIL_ENABLE'] = True
    with app.app_context():
        handlers = setup_logger(app)
        email_handlers = [h for h in handlers if isinstance(h, EmailHandler)]
        assert len(email_handlers) == 1

@patch('smtplib.SMTP')
def test_log_levels(mock_smtp, app):
    app.config['LOG_EMAIL_ENABLE'] = True
    app.config['LOG_FILE_LEVEL'] = 'DEBUG'  # Temporarily set to DEBUG for this test
    with app.app_context():
        setup_logger(app)
        with patch.object(app.logger.handlers[0], 'emit') as mock_file_emit, \
             patch.object(EmailHandler, 'send_email') as mock_send_email:
            
            app.logger.debug("Debug message")
            app.logger.info("Info message")
            app.logger.warning("Warning message")
            app.logger.error("Error message")
            app.logger.critical("Critical message")
            
            assert mock_file_emit.call_count == 5  # Debug messages are logged for this test
            log_levels = [mock_file_emit.call_args_list[i][0][0].levelname for i in range(5)]
            assert log_levels == ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            
            assert mock_send_email.call_count == 2  # Called for ERROR and CRITICAL

@patch('flask_login.utils._get_user')
def test_request_formatter(mock_get_user, app):
    mock_get_user.return_value = MagicMock(is_authenticated=False)
    with app.app_context():
        setup_logger(app)
        formatter = RequestFormatter('%(url)s - %(remote_addr)s - %(user_id)s - %(user_email)s - %(message)s')
        with app.test_request_context('/test', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            record = logging.LogRecord(
                name='test', level=logging.INFO, pathname='', lineno=0,
                msg='Test message', args=(), exc_info=None
            )
            formatted = formatter.format(record)
            assert 'http://localhost/test - 127.0.0.1 - N/A - N/A - Test message' in formatted

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

def test_request_formatter_without_context(app):
    with app.app_context():
        formatter = RequestFormatter('%(url)s - %(remote_addr)s - %(user_id)s - %(user_email)s - %(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='Test message', args=(), exc_info=None
        )
        formatted = formatter.format(record)
        assert 'None - None - N/A - N/A - Test message' in formatted

def test_email_handler_configuration(app):
    app.config['LOG_EMAIL_ENABLE'] = True
    with app.app_context():
        handlers = setup_logger(app)
        email_handler = next((h for h in handlers if isinstance(h, EmailHandler)), None)
        assert email_handler is not None
        assert email_handler.level == logging.ERROR
        assert email_handler.config['SMTP_SERVER'] == app.config['SMTP_SERVER']
        assert email_handler.config['SMTP_PORT'] == app.config['SMTP_PORT']
        assert email_handler.config['SMTP_USERNAME'] == app.config['SMTP_USERNAME']
        assert email_handler.config['SMTP_PASSWORD'] == app.config['SMTP_PASSWORD']

def test_console_logging_in_non_debug_mode(app):
    app.debug = False
    with app.app_context():
        handlers = setup_logger(app)
        console_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
        assert len(console_handlers) == 0

def test_init_logger(app):
    with app.app_context():
        init_logger(app)
        assert os.path.isabs(app.config['LOG_FILE_DIRECTORY'])
        assert any(isinstance(h, HeaderFileHandler) for h in app.logger.handlers)

def test_comprehensive_log_handling(app):
    log_dir = app.config['LOG_FILE_DIRECTORY']
    file_handler = next((h for h in app.logger.handlers if isinstance(h, HeaderFileHandler)), None)
    assert file_handler is not None

    # 1. Header is added to a new file
    with freeze_time("2023-01-01 10:00:00"):
        app.logger.info("First log entry")
        log_file = file_handler.baseFilename  # Use the actual file path from the handler
        assert os.path.exists(log_file), f"Log file not found: {log_file}"
        with open(log_file, 'r') as f:
            content = f.read()
            assert content.startswith("Timestamp\tLog Level\tModule\tMessage\t")
            assert "First log entry" in content

    # 2. Header is added only once for a file even if the app stops and restarts
    with freeze_time("2023-01-01 12:00:00"):
        file_handler.close()
        setup_logger(app)  # Simulate restart
        app.logger.info("Second log entry")
        with open(log_file, 'r') as f:
            content = f.read()
            assert content.count("Timestamp\tLog Level\tModule\tMessage\t") == 1
            assert "Second log entry" in content

    # 3. A new log is started when the date rolls over (while app is running)
    with freeze_time("2023-01-02 00:00:01"):
        app.logger.info("New day log entry")
        new_log_file = os.path.join(log_dir, "app_2023-01-02.log")
        assert os.path.exists(new_log_file)
        with open(new_log_file, 'r') as f:
            content = f.read()
            assert "New day log entry" in content

    # 4. A new log is started when the app stops and restarts on the next day
    with freeze_time("2023-01-03 10:00:00"):
        file_handler.close()
        setup_logger(app)  # Simulate restart
        app.logger.info("Next day restart entry")
        next_day_log_file = os.path.join(log_dir, "app_2023-01-03.log")
        assert os.path.exists(next_day_log_file)
        with open(next_day_log_file, 'r') as f:
            content = f.read()
            assert "Next day restart entry" in content

    # 5. The existing log is appended when the app stops and starts on the same day
    with freeze_time("2023-01-03 14:00:00"):
        file_handler.close()
        setup_logger(app)  # Simulate restart
        app.logger.info("Same day restart entry")
        with open(next_day_log_file, 'r') as f:
            content = f.read()
            assert "Next day restart entry" in content
            assert "Same day restart entry" in content

    # 6 & 7. Old log clearing on app start and date rollover
    # First, create some old log files
    old_dates = [datetime(2023, 1, 3) - timedelta(days=i) for i in range(1, 10)]
    for date in old_dates:
        with open(os.path.join(log_dir, f"app_{date.strftime('%Y-%m-%d')}.log"), 'w') as f:
            f.write("Old log content")

    # Simulate app restart (should trigger old log clearing)
    with freeze_time("2023-01-04 00:00:01"):
        file_handler.close()
        setup_logger(app)
        app.logger.info("Trigger old log clearing")

        # Check that only 7 old files + 1 new file exist
        log_files = sorted(os.listdir(log_dir))
        assert len(log_files) == 8, f"Expected 8 log files, found {len(log_files)}: {log_files}"
        assert log_files[0] == 'app_2022-12-28.log'  # Oldest retained log
        assert log_files[-1] == 'app_2023-01-04.log'  # Newest log (current day)

    # Simulate date rollover while app is running
    with freeze_time("2023-01-05 00:00:01"):
        app.logger.info("Trigger rollover and old log clearing")

        # Check that oldest log is removed and new log is created
        log_files = sorted(os.listdir(log_dir))
        assert len(log_files) == 8, f"Expected 8 log files, found {len(log_files)}: {log_files}"
        assert log_files[0] == 'app_2022-12-29.log'  # New oldest retained log
        assert log_files[-1] == 'app_2023-01-05.log'  # Newest log

    # Final check
    log_files = sorted(os.listdir(log_dir))
    assert len(log_files) == 8, f"Expected 8 log files at the end, found {len(log_files)}: {log_files}"
    assert (datetime.now().date() - datetime.strptime(log_files[0].split('_')[1].split('.')[0], "%Y-%m-%d").date()).days == 7