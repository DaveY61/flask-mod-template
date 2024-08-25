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
from app.services.log_service import setup_logger, init_app, HeaderFileHandler, EmailHandler, RequestFormatter
from unittest.mock import patch, MagicMock
import tempfile
import logging
import os
import time

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update({
        'LOG_FILE_DIRECTORY': tempfile.mkdtemp(),
        'LOG_RETENTION_DAYS': 7,
        'EMAIL_ENABLE_ERROR': False,
        'ADMIN_USER_LIST': ['admin@example.com'],
        'EMAIL_FROM_ADDRESS': 'test@example.com',
        'SMTP_SERVER': 'smtp.example.com',
        'SMTP_PORT': 587,
        'SMTP_USERNAME': 'test_user',
        'SMTP_PASSWORD': 'test_password'
    })
    return app

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
    app.config['EMAIL_ENABLE_ERROR'] = True
    app.config['ADMIN_USER_LIST'] = ['admin@example.com']
    app.config['EMAIL_FROM_ADDRESS'] = 'test@example.com'
    app.config['SMTP_SERVER'] = 'smtp.example.com'
    app.config['SMTP_PORT'] = 587
    app.config['SMTP_USERNAME'] = 'test_user'
    app.config['SMTP_PASSWORD'] = 'test_password'

    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    with app.app_context():
        handlers = setup_logger(app)
        email_handler = next((h for h in handlers if isinstance(h, EmailHandler)), None)
        assert email_handler is not None, "EmailHandler not found in logger handlers"
        
        with patch.object(EmailHandler, 'send_email') as mock_send_email:
            app.logger.error("Test error message")
            mock_send_email.assert_called_once()

    mock_smtp.assert_not_called()

def test_add_user_info_to_request(app):
    init_app(app)
    with app.test_request_context('/'):
        for func in app.before_request_funcs[None]:
            func()
        assert hasattr(request, 'user_id')
        assert hasattr(request, 'user_email')
        assert request.user_id == 'N/A'
        assert request.user_email == 'N/A'

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
    app.config['EMAIL_ENABLE_ERROR'] = True
    with app.app_context():
        handlers = setup_logger(app)
        email_handlers = [h for h in handlers if isinstance(h, EmailHandler)]
        assert len(email_handlers) == 1

@patch('smtplib.SMTP')
def test_log_levels(mock_smtp, app):
    app.config['EMAIL_ENABLE_ERROR'] = True
    with app.app_context():
        setup_logger(app)
        with patch.object(app.logger.handlers[0], 'emit') as mock_file_emit, \
             patch.object(EmailHandler, 'send_email') as mock_send_email:
            
            app.logger.debug("Debug message")
            app.logger.info("Info message")
            app.logger.warning("Warning message")
            app.logger.error("Error message")
            app.logger.critical("Critical message")
            
            assert mock_file_emit.call_count == 5
            log_levels = [mock_file_emit.call_args_list[i][0][0].levelname for i in range(5)]
            assert log_levels == ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            
            assert mock_send_email.call_count == 2  # Called for ERROR and CRITICAL

def test_request_formatter(app):
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