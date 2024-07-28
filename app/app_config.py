import os
import binascii
from app.gui_config import GUIConfig
from app.mod_config import MODULE_LIST

class Config:
    # Set debug mode
    DEBUG = False

    # Generate a random secret key and convert it to a hexadecimal string
    SECRET_KEY = binascii.hexlify(os.urandom(32)).decode()

    #----------------------------------------------------------------------------
    # Config for pytest packages
    VS_PROJECT_FOLDER_NAME = os.environ.get('VS_PROJECT_FOLDER_NAME')

    #----------------------------------------------------------------------------
    # Config the Log, Email, and Authentication Seervices

    # Log Settings
    LOG_FILE_DIRECTORY = os.environ.get('LOG_FILE_DIRECTORY') or './app_logs'
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 30))
    
    # Email Settings
    EMAIL_FAIL_DIRECTORY = os.environ.get('EMAIL_FAIL_DIRECTORY') or './app_data/email'
    EMAIL_FROM_ADDRESS = os.environ.get('EMAIL_FROM_ADDRESS')
    EMAIL_ENABLE_ERROR = (os.environ.get('EMAIL_ENABLE_ERROR') == '1')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    ADMIN_USER_LIST = os.environ.get('ADMIN_USER_LIST', '').split(',')

    # User Database Settings
    USER_DATABASE_FILENAME = os.environ.get('USER_DATABASE_FILENAME') or 'users.db'
    USER_DATABASE_DIRECTORY = os.environ.get('USER_DATABASE_DIRECTORY') or './app_data/users'
    USER_DATABASE_PATH = os.path.join(USER_DATABASE_DIRECTORY, USER_DATABASE_FILENAME)

    #----------------------------------------------------------------------------
    # Module Configuration from "mod_config.py"
    MODULE_LIST = MODULE_LIST

#----------------------------------------------------------------------------
# Integrate GUIConfig attributes from "gui_config.py"
for key, value in vars(GUIConfig).items():
    if not key.startswith('__'):
        setattr(Config, key, value)