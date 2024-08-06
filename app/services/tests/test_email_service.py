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
from app.services.email_service import EmailService
from unittest.mock import patch, MagicMock
import email

@pytest.fixture(scope="function")  # Change scope to "function"
def email_service():
    config = {
        'EMAIL_FROM_ADDRESS': 'test@example.com',
        'SMTP_SERVER': 'smtp.example.com',
        'SMTP_PORT': 587,
        'SMTP_USERNAME': 'test_user',
        'SMTP_PASSWORD': 'test_password',
        'EMAIL_FAIL_DIRECTORY': './test_failed_emails'
    }
    
    # Clean up the directory before the test
    if os.path.exists(config['EMAIL_FAIL_DIRECTORY']):
        for file in os.listdir(config['EMAIL_FAIL_DIRECTORY']):
            os.remove(os.path.join(config['EMAIL_FAIL_DIRECTORY'], file))
    else:
        os.makedirs(config['EMAIL_FAIL_DIRECTORY'])
    
    yield EmailService(config)
    
    # Clean up after the test
    for file in os.listdir(config['EMAIL_FAIL_DIRECTORY']):
        os.remove(os.path.join(config['EMAIL_FAIL_DIRECTORY'], file))
    os.rmdir(config['EMAIL_FAIL_DIRECTORY'])

@patch('smtplib.SMTP')
def test_send_email_success(mock_smtp, email_service):
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value = mock_smtp_instance

    email_service.send_email(
        to=['recipient@example.com'],
        subject='Test Subject',
        body='Test Body'
    )

    mock_smtp_instance.sendmail.assert_called_once()
    assert mock_smtp_instance.sendmail.call_args[0][0] == 'test@example.com'
    assert mock_smtp_instance.sendmail.call_args[0][1] == ['recipient@example.com']

@patch('smtplib.SMTP')
def test_send_email_failure(mock_smtp, email_service):
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.sendmail.side_effect = Exception('SMTP Error')
    mock_smtp.return_value = mock_smtp_instance

    with pytest.raises(Exception):
        email_service.send_email(
            to=['recipient@example.com'],
            subject='Test Subject',
            body='Test Body'
        )

    failed_emails = os.listdir(email_service.config['EMAIL_FAIL_DIRECTORY'])
    assert len(failed_emails) == 1
    assert failed_emails[0].startswith('failed_')

@patch('smtplib.SMTP')
def test_check_and_resend_failed_emails(mock_smtp, email_service):
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value = mock_smtp_instance

    # Create two mock failed email files
    failed_email_path1 = os.path.join(email_service.config['EMAIL_FAIL_DIRECTORY'], 'failed_test1.eml')
    failed_email_path2 = os.path.join(email_service.config['EMAIL_FAIL_DIRECTORY'], 'failed_test2.eml')
    
    with open(failed_email_path1, 'w') as f:
        f.write('To: recipient1@example.com\nSubject: Test1\n\nTest Body 1')
    with open(failed_email_path2, 'w') as f:
        f.write('To: recipient2@example.com\nSubject: Test2\n\nTest Body 2')

    # Reset the mock before calling check_and_resend_failed_emails
    mock_smtp_instance.sendmail.reset_mock()

    email_service.check_and_resend_failed_emails()

    assert mock_smtp_instance.sendmail.call_count == 2, f"Expected 2 calls, but got {mock_smtp_instance.sendmail.call_count}"

    calls = mock_smtp_instance.sendmail.call_args_list
    assert len(calls) == 2

    # Check first call
    assert calls[0][0][0] == 'test@example.com'  # From address
    assert calls[0][0][1] == ['recipient1@example.com']  # To address
    assert 'Subject: Test1' in calls[0][0][2]  # Email content
    assert 'Test Body 1' in calls[0][0][2]  # Email content

    # Check second call
    assert calls[1][0][0] == 'test@example.com'  # From address
    assert calls[1][0][1] == ['recipient2@example.com']  # To address
    assert 'Subject: Test2' in calls[1][0][2]  # Email content
    assert 'Test Body 2' in calls[1][0][2]  # Email content

    # Check if the failed email files were removed
    assert not os.path.exists(failed_email_path1)
    assert not os.path.exists(failed_email_path2)