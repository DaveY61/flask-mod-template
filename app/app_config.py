import os
import binascii
import json

class Config:
    # Set debug mode 
    #  - use .env setting, but default to 'False' for Production (if not defined in the .env)
    #  - use 'app.run(debug=True)' in the 'run_local.py' for Development
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

    # Generate a random secret key and convert it to a hexadecimal string
    SECRET_KEY = binascii.hexlify(os.urandom(32)).decode()

    #----------------------------------------------------------------------------
    # Config for pytest packages
    VS_PROJECT_FOLDER_NAME = os.environ.get('VS_PROJECT_FOLDER_NAME')

    #----------------------------------------------------------------------------
    # Config the Log, Email, and User Authentication Services

    # User Database Settings
    USER_DATABASE_FILENAME = os.environ.get('USER_DATABASE_FILENAME') or 'users.db'
    USER_DATABASE_DIRECTORY = os.environ.get('USER_DATABASE_DIRECTORY') or './app_data/users'
    USER_DATABASE_PATH = os.path.join(USER_DATABASE_DIRECTORY, USER_DATABASE_FILENAME)

    # Admin User List (email addess)
    ADMIN_USER_LIST = os.environ.get('ADMIN_USER_LIST', '').split(',')

    # Log Settings
    LOG_FILE_DIRECTORY = os.environ.get('LOG_FILE_DIRECTORY') or './app_logs'
    LOG_FILE_LEVEL = os.environ.get('LOG_FILE_LEVEL') or 'INFO'
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 30))
    LOG_EMAIL_ENABLE = os.environ.get('LOG_EMAIL_ENABLE', '0').lower() in ('1', 'true', 'yes', 'on')
    LOG_EMAIL_LEVEL = os.environ.get('LOG_EMAIL_LEVEL') or 'ERROR'
    # Log email is sent to the Admin User List (above)

    # Email Settings
    EMAIL_FAIL_DIRECTORY = os.environ.get('EMAIL_FAIL_DIRECTORY') or './app_data/email'
    EMAIL_FROM_ADDRESS = os.environ.get('EMAIL_FROM_ADDRESS')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

    # User Authentication reCAPTCHA
    ENABLE_REGISTRATION_CAPTCHA = False
    RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
    RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')

    #----------------------------------------------------------------------------
    # Module Configuration from "mod_config.cnf"
    MOD_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'mod_config.cnf')

    @staticmethod
    def load_module_config(MOD_CONFIG_PATH):
        if os.path.exists(MOD_CONFIG_PATH):
            with open(MOD_CONFIG_PATH, 'r') as f:
                config = json.load(f)
                # Only return the config if it's in the new format (list of dicts)
                if isinstance(config, list) and all(isinstance(item, dict) for item in config):
                    return config
        return []  # Return an empty list if the file doesn't exist or is in the old format

    MODULE_LIST = load_module_config(MOD_CONFIG_PATH)
    
    # Define the GUI config path to part of the Config class
    GUI_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'gui_config.cnf')

    # Define the Role config path as part of the Config class
    ROLE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'role_config.cnf')

    # Define the User config path
    USER_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'user_config.cnf')

#----------------------------------------------------------------------------
# Integrate GUI Config attributes from "gui_config.cnf"
# Must be done AFTER the class has been defined
with open(Config.GUI_CONFIG_PATH, 'r') as f:
    gui_config = json.load(f)

for key, value in gui_config.items():
    setattr(Config, key, value)

#----------------------------------------------------------------------------
# Integrate Role Config attributes from "role_config.cnf"
# Must be done AFTER the class has been defined
if os.path.exists(Config.ROLE_CONFIG_PATH):
    with open(Config.ROLE_CONFIG_PATH, 'r') as f:
        role_config = json.load(f)
    setattr(Config, 'ROLE_LIST', role_config)
else:
    setattr(Config, 'ROLE_LIST', [])

#----------------------------------------------------------------------------
# Integrate User Config attributes from "user_config.cnf"
# Must be done AFTER the class has been defined
if os.path.exists(Config.USER_CONFIG_PATH):
    with open(Config.USER_CONFIG_PATH, 'r') as f:
        user_config = json.load(f)
    for key, value in user_config.items():
        setattr(Config, key, value)
else:
    # Set default values if the file doesn't exist
    setattr(Config, 'DISABLE_SELF_REGISTRATION', False)
    setattr(Config, 'REQUIRE_LOGIN_FOR_SITE_ACCESS', False)