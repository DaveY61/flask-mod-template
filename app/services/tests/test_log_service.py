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
from app.services.log_service import LogService

def test_log_service(config):
    # Define the log service
    log_service = LogService(config)

    # Create sample log entries (one for each type)
    log_service.log('INFO', 'This is an info message')
    log_service.log('WARNING', 'This is a warning message')
    log_service.log('ERROR', 'This is an error message')

    # Log entry with a "User ID"
    log_service.log('INFO', 'This message has a user id included', 'FRED')

    # Clean old logs
    log_service.clean_old_logs()

if __name__ == "__main__":
    # Create the Flask app with the specified template folder
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(Config)

    test_log_service(app.config)
