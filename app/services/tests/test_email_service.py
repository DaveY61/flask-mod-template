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
import tempfile

@pytest.fixture(scope="function")
def email_service():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {
            'EMAIL_FROM_ADDRESS': 'test@example.com',
            'SMTP_SERVER': 'smtp.example.com',
            'SMTP_PORT': 587,
            'SMTP_USERNAME': 'test_user',
            'SMTP_PASSWORD': 'test_password',
            'EMAIL_FAIL_DIRECTORY': temp_dir
        }
        yield EmailService(config)

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

    assert mock_smtp_instance.sendmail.call_count == 2

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

@patch('smtplib.SMTP')
def test_send_email_with_cc_bcc(mock_smtp, email_service):
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value = mock_smtp_instance

    email_service.send_email(
        to=['recipient@example.com'],
        subject='Test Subject',
        body='Test Body',
        cc=['cc@example.com'],
        bcc=['bcc@example.com']
    )

    mock_smtp_instance.sendmail.assert_called_once()
    call_args = mock_smtp_instance.sendmail.call_args[0]
    assert call_args[0] == 'test@example.com'
    assert set(call_args[1]) == {'recipient@example.com', 'cc@example.com', 'bcc@example.com'}

@patch('smtplib.SMTP')
def test_send_email_with_attachment(mock_smtp, email_service):
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value = mock_smtp_instance

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write('Test attachment content')
        temp_file_path = temp_file.name

    email_service.send_email(
        to=['recipient@example.com'],
        subject='Test Subject',
        body='Test Body',
        attachments=[temp_file_path]
    )

    mock_smtp_instance.sendmail.assert_called_once()
    call_args = mock_smtp_instance.sendmail.call_args[0]
    assert 'Content-Disposition: attachment;' in call_args[2]
    assert os.path.basename(temp_file_path) in call_args[2]

    os.unlink(temp_file_path)

@patch('smtplib.SMTP')
def test_send_html_email(mock_smtp, email_service):
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value = mock_smtp_instance

    html_content = '<html><body><h1>Test HTML Email</h1></body></html>'
    email_service.send_email(
        to=['recipient@example.com'],
        subject='Test HTML Subject',
        body=html_content,
        html=True
    )

    mock_smtp_instance.sendmail.assert_called_once()
    call_args = mock_smtp_instance.sendmail.call_args[0]
    assert 'Content-Type: text/html' in call_args[2]
    assert html_content in call_args[2]