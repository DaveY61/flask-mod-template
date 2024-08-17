import os
import sys
import subprocess

# Get the current working directory name
project_folder_name = os.path.basename(os.getcwd())

# .env file content with comments for grouping, dynamically filled project folder name
env_content = f"""
# Project Configuration
VS_PROJECT_FOLDER_NAME={project_folder_name}

# GitHub Configuration
GitHub_SECRET=your_github_secret_here

# Database Configuration
USER_DATABASE_FILENAME=users.db
USER_DATABASE_DIRECTORY=./app_data/users

# Logging Configuration
LOG_FILE_DIRECTORY=./app_logs
LOG_RETENTION_DAYS=7

# Email Configuration
EMAIL_FAIL_DIRECTORY=./app_data/email
EMAIL_FROM_ADDRESS=your_email_here
EMAIL_ENABLE_ERROR=1
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username_here
SMTP_PASSWORD=your_smtp_password_here
ADMIN_ERROR_ROUTING=admin_email_here
"""

def create_directories():
    directories = []
    for line in env_content.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.endswith("_DIRECTORY"):
            directories.append(value.strip())

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def create_virtual_environment():
    subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    print("Virtual environment 'venv' created")

def install_requirements():
    if os.name == 'nt':
        pip_executable = os.path.join("venv", "Scripts", "pip.exe")
    else:
        pip_executable = os.path.join("venv", "bin", "pip")

    subprocess.check_call([pip_executable, "install", "-r", "requirements.txt"])
    print("Requirements installed")

def main():
    if os.path.exists(".env"):
        print("Install already was performed")
        sys.exit(0)
    
    create_virtual_environment()
    install_requirements()
    create_directories()

    with open(".env", "w") as f:
        f.write(env_content.strip())
    print(".env file created")

if __name__ == "__main__":
    main()
