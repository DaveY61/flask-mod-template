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
import csv
from datetime import datetime, timedelta
from app.services.log_service import LogService
from unittest.mock import patch, MagicMock

@pytest.fixture
def log_service():
    config = {
        'LOG_FILE_DIRECTORY': './test_logs',
        'LOG_RETENTION_DAYS': 7,
        'EMAIL_ENABLE_ERROR': False,
        'ADMIN_USER_LIST': ['admin@example.com']
    }
    return LogService(config)

def test_log_creation(log_service):
    log_service.log('INFO', 'Test info message')
    log_service.log('WARNING', 'Test warning message')
    log_service.log('ERROR', 'Test error message')

    log_file_path = log_service.get_log_file_path()
    assert os.path.exists(log_file_path)

    with open(log_file_path, 'r') as log_file:
        csv_reader = csv.DictReader(log_file)
        logs = list(csv_reader)

    assert len(logs) == 3
    assert logs[0]['type'] == 'INFO'
    assert logs[1]['type'] == 'WARNING'
    assert logs[2]['type'] == 'ERROR'

def test_log_with_user_id(log_service):
    log_service.log('INFO', 'Test message with user ID', user_id='TEST_USER')

    log_file_path = log_service.get_log_file_path()
    with open(log_file_path, 'r') as log_file:
        csv_reader = csv.DictReader(log_file)
        logs = list(csv_reader)

    assert logs[-1]['user_id'] == 'TEST_USER'

def test_clean_old_logs(log_service):
    # Create an old log file
    old_date = datetime.now() - timedelta(days=log_service.retention_days + 2)
    old_log_file = f"log_{old_date.strftime('%Y-%m-%d')}.csv"
    old_log_path = os.path.join(log_service.log_file_directory, old_log_file)
    
    os.makedirs(os.path.dirname(old_log_path), exist_ok=True)
    with open(old_log_path, 'w') as f:
        f.write('date,time,type,message,user_id,function,line,file\n')
        f.write('2023-01-01,00:00:00,INFO,Old log,,,,,\n')

    # Set the file's modification time to the old date
    old_time = old_date.timestamp()
    os.utime(old_log_path, (old_time, old_time))

    assert os.path.exists(old_log_path)

    # Run the clean_old_logs method
    log_service.clean_old_logs()

    # Check if the old log file has been removed
    assert not os.path.exists(old_log_path)

def test_get_log_file_path(log_service):
    log_file_path = log_service.get_log_file_path()
    assert log_file_path.startswith(log_service.log_file_directory)
    assert log_file_path.endswith('.csv')
    assert datetime.now().strftime('%Y-%m-%d') in log_file_path

def test_error_log_email(log_service):
    # Configure log_service to enable error emails
    log_service.enable_error_email = True
    
    # Mock the EmailService
    mock_email_service = MagicMock()
    log_service.email_service = mock_email_service

    # Log an error message
    log_service.log('ERROR', 'Test error message for email')

    # Check if send_email was called
    mock_email_service.send_email.assert_called_once()

    # Check the arguments of the send_email call
    call_args = mock_email_service.send_email.call_args
    assert call_args is not None
    args, kwargs = call_args

    # Check that the email is sent to admin emails
    assert args[0] == log_service.admin_emails

    # Check that the email subject contains "Error Log Notification"
    assert 'Error Log Notification' in args[1]

    # Check that the email body contains the error message
    assert 'Test error message for email' in args[2]

def teardown_module(module):
    # Clean up test log files
    test_log_dir = './test_logs'
    if os.path.exists(test_log_dir):
        for file in os.listdir(test_log_dir):
            os.remove(os.path.join(test_log_dir, file))
        os.rmdir(test_log_dir)