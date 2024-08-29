import os
import sys
import subprocess
import shutil

# Get the current working directory name
project_folder_name = os.path.basename(os.getcwd())

# .env file content with comments for grouping, dynamically filled project folder name
env_content = f"""
# Project Configuration
VS_PROJECT_FOLDER_NAME={project_folder_name}

# Flask Debug Control (use 'False' for Production, 'True' for Development)
FLASK_DEBUG=False

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
ADMIN_USER_LIST=admin1@example.com,admin2@example.com

# User Self-Registration reCAPTCHA
RECAPTCHA_SITE_KEY=your_captcha_site_key
RECAPTCHA_SECRET_KEY=your_captcha_secret_key
"""

def confirm_new_install():
    if os.path.exists(".env"):
        print("Install already was performed")
        sys.exit(0)

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
        python_executable = os.path.join("venv", "Scripts", "python.exe")
        pip_executable = os.path.join("venv", "Scripts", "pip.exe")
    else:
        python_executable = os.path.join("venv", "bin", "python")
        pip_executable = os.path.join("venv", "bin", "pip")

    # Update pip first, quietly
    print("Updating pip...")
    try:
        subprocess.check_call([python_executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
        print("Pip updated successfully.")
    except subprocess.CalledProcessError:
        print("Failed to update pip. Continuing with package installation...")

    requirements_file = "fmt_requirements.txt"
    
    # Read and display package names from requirements file
    with open(requirements_file, 'r') as f:
        packages = [line.strip().split('==')[0] for line in f if line.strip() and not line.startswith('#')]

    print("Installing packages:")
    for package in packages:
        print(f"  - {package}")
        try:
            subprocess.check_call([pip_executable, "install", "--quiet", package])
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}. Continuing with next package...")

    print("Requirements installation completed.")

def rename_example_files():
    for root, dirs, files in os.walk('.', topdown=False):
        # Rename files
        for file in files:
            if file.endswith('.example'):
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, file[:-8])  # Remove '.example'
                shutil.move(old_path, new_path)
                print(f"Renamed file: {old_path} to {new_path}")
        
        # Rename directories
        for dir in dirs:
            if dir.endswith('.example'):
                old_path = os.path.join(root, dir)
                new_path = os.path.join(root, dir[:-8])  # Remove '.example'
                shutil.move(old_path, new_path)
                print(f"Renamed directory: {old_path} to {new_path}")

def update_gitignore():
    gitignore_path = '.gitignore'
    if not os.path.exists(gitignore_path):
        print(".gitignore file not found")
        return

    with open(gitignore_path, 'r') as file:
        lines = file.readlines()

    start_index = None
    end_index = None
    for i, line in enumerate(lines):
        if line.find("Ignore specific template files") > 0:
            start_index = i
        elif start_index is not None:
            end_index = i+1

    if start_index is not None and end_index is not None:
        del lines[start_index:end_index]

    with open(gitignore_path, 'w') as file:
        file.writelines(lines)

    print("Updated .gitignore file")


def write_env_template():
    with open(".env", "w") as f:
        f.write(env_content.strip())
    print(".env file created")

def print_env_reminder():
    reminder = """
╔════════════════════════════════════════════════════════════════════════════╗
║                             IMPORTANT REMINDER                             ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Modify the following keys in the .env file:                               ║
║                                                                            ║
║  - FLASK_DEBUG          - Optional, set to 'True' for local development    ║
║  - GitHub_SECRET        - Optional, if using GitHub push trigger           ║
║  - EMAIL_FROM_ADDRESS   - matches your SMTP account                        ║
║  - SMTP_SERVER          - ie smtp.gmail.com                                ║
║  - SMTP_USERNAME        - Required, SMTP email for user registration       ║
║  - SMTP_PASSWORD        - Required, SMTP email for user registration       ║
║  - ADMIN_USER_LIST      - Required, intial Admin login, Admin Setup        ║
║  - RECAPTCHA_SITE_KEY   - Optional, if reCAPTCHA used for registraion      ║
║  - RECAPTCHA_SECRET_KEY - Optional, if reCAPTCHA used for registraion      ║
║                                                                            ║
║  These values are crucial for the proper functioning of your application.  ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(reminder)

def main():
    # Check and exit if already performed
    confirm_new_install()

    # Run the other update steps to prepare the application
    create_virtual_environment()
    install_requirements()
    create_directories()
    rename_example_files()
    update_gitignore()

    # Create a template .env file
    write_env_template()
    print_env_reminder()

if __name__ == "__main__":
    main()
