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

def test_email_service_success():
    email_service = EmailService(Config)
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

def test_email_service_fail():
    # Cause a failed email by an invalid smtp server
    Config.SMTP_SERVER = "xxxx"
    email_service = EmailService(Config)
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
    test_email_service_success()
    #test_email_service_fail()
