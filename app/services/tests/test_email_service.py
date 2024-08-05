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
from app.app_config import Config
from app.services.email_service import EmailService

def test_email_service_success(config):
    email_service = EmailService(config)
    email_service.send_email(
        to=["test@example.com"],
        subject="Test Email",
        body="This is a test email.",
        html=None,
        attachments=[],
        cc=[],
        bcc=[]
    )
    email_service.check_and_resend_failed_emails()

def test_email_service_fail(config):
    # Cause a failed email by an invalid smtp server
    config['SMTP_SERVER'] = "xxxx"
    email_service = EmailService(config)
    email_service.send_email(
        to=["test@example.com"],
        subject="Test Email",
        body="This is a test email.",
        html=None,
        attachments=[],
        cc=[],
        bcc=[]
    )

if __name__ == "__main__":
    # Create the Flask app with the specified template folder
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(Config)

    # Toggle "test_success" to False to test a failed email
    test_success = True
    if ( test_success ):
        test_email_service_success(app.config)
    else:
        test_email_service_fail(app.config)
