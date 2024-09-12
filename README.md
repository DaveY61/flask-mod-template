# Flask Modular Template

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Make Local Repository](#make-local-repository)
  - [Establish Admin User](#establish-admin-user)
  - [Review Admin Setup](#review-admin-setup)
  - [Updating Your Project](#updating-your-project)
- [GUI Customization](#gui-customization)
- [Adding New Modules](#adding-new-modules)
- [Enabling Modules and Managing Access](#enabling-modules-and-managing-access)
- [Role-Based Access Control](#role-based-access-control)
- [User Management](#user-management)
  - [User Registration: reCAPTCHA](#user-registration-recaptcha)
  - [End User License Agreement (EULA)](#end-user-license-agreement-eula)
- [Email Setup](#email-setup)
- [Error Handling and Logging](#error-handling-and-logging)
  - [Log Configuration in .env](#log-configuration-in-env)
  - [Log Viewer for Admin Users](#log-viewer-for-admin-users)
  - [Using app.logger in Modules](#using-applogger-in-modules)
  - [Debug Logging](#debug-logging)
- [FMT Testing](#fmt-testing)
- [License](#license)
- [Deployment](#deployment)

## Overview

Flask Modular Template is a scalable and modular Python Flask application template. It provides a structured foundation for building web applications with easily extendable modules, user authentication, role-based access control, an admin setup interface, and an admin application log viewer.

## Features

- Modular architecture for easy scaling and maintenance
- Dynamic module discovery and activation without application restart
- User authentication system (register, login, password reset)
- Role-based access control with dynamic module permissions
- Admin setup interface for GUI configuration, module management, role management, user management, and email configuration
- Sample modules (Pie Chart, CSV Upload, Games) demonstrating integration
- Responsive design using Bootstrap 5
- Customizable styling through admin interface
- Sidebar navigation for admin pages and new modules
- User management includes: require login for site access, disable self-registration, and enable reCAPTCHA for registration
- Direct user addition by administrators with automatic activation email
- Customizable End User License Agreement (EULA) with optional acknowledgment requirement
- Improved error logging and Log Viewer for admin users

## Technologies Used

- Python 3.7+
- Flask 3.0.3
- Flask-Login 0.6.3
- Flask-WTF 1.2.1
- SQLAlchemy 1.4.46
- Bootstrap 5.3.3
- Font Awesome 6.6.0
- jQuery 3.7.1
- Chart.js (for Pie Chart module)

## Getting Started

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Make Local Repository

1. Use 'Fork' or 'Use this template' to create your repository on GitHub.

   **Fork**
   ``` 
   A fork is a copy of an existing repository that allows you to make changes 
   without affecting the original project.
   
   Usage: Ideal for contributing to an existing project or experimenting with changes.
   ```

   **Use this template**
   ```
   A template repository is used to create a new repository with the same directory
   structure and files as the original, but without the commit history.
   
   Usage: Ideal for creating new projects with a predefined structure.
   ```

2. Clone your repository to your local PC:
   ```
   git clone https://github.com/yourusername/flask-mod-template.git
   cd flask-mod-template
   ```
3. Run the `fmt_install.py` script:
   ```
   python fmt_install.py
   ```
   This script will:
   - Create a virtual environment
   - Install required packages
   - Create necessary directories
   - Rename example files (removing .example extensions)
   - Update .gitignore
   - Create a .env file
   - Create a `fmt_version.txt` file to track the in-use template version

4. Update the `.env` file with your specific configuration values, paying special attention to the email-related variables which are crucial for user registration and password reset functionality.

### Establish Admin User

1. Add your email to the `ADMIN_USER_LIST` in the `.env` file.
2. Run the local server:
   ```
   python run_local.py
   ```
3. Open your web browser and navigate to `http://localhost:5000`.
4. Click on "Sign up" and use your email address (from `.env`) with the password "admin".
5. You will be redirected to the Create Password page. Set your new admin password.

**Note:** If you initially created your account without using the admin password, you can still use "admin" as the password during login to activate your Admin account. This feature allows you to gain admin access even if you started registration without using the special password.

### Review Admin Setup

After logging in as an admin, you can access the Admin Setup page. Here are the options provided:

- [GUI Setup](#gui-customization): Customize the application's appearance
- [Module Setup](#enabling-modules-and-managing-access): Manage and configure modules
- [Role Setup](#role-based-access-control): Define and manage user roles
- [User Setup](#user-management): Manage users and their permissions
- [Email Setup](#email-setup): Configure email settings for the application

Refer to the linked sections in this document for more details on each setup area.

### Updating Your Project

To update your project to the latest template version, you can use the `fmt_update.py` script. This script automates the update process and helps you manage potential conflicts. Here's how to use it:

1. Ensure you have committed or stashed any local changes.
2. Run the update script:
   ```
   python fmt_update.py
   ```
3. The script will guide you through the following steps:
   - Check for any existing worktrees and offer to remove them
   - Determine your current version
   - Fetch available versions from the GitHub repository
   - Allow you to select the version to update to
   - Attempt to your project from the selected template version

The `fmt_update.py` script works by:
- Creating a temporary branch with the selected update version
- Attempting to merge this branch with your main branch
- Handling merge conflicts if they occur
- Updating the `fmt_version.txt` file to reflect the new version

Key features of the update process:
- **Logging**: The script creates a log file named `fmt_update_log.txt` in the project root directory. This log file contains detailed information about the update process, including any errors or warnings encountered.
- **Backups**: Before applying changes, the script creates backups of modified files. These backups are stored in a version-specific directory within `fmt_update_backups/` in your project root. For example, if you're updating to version 1.2.3, backups will be in `fmt_update_backups/1.2.3/`.
- **Incremental Updates**: The script processes all versions between your current version and the selected target version, ensuring that all incremental changes are applied.
- **Conflict Resolution**: If merge conflicts occur, the script will notify you and provide instructions on how to resolve them manually.

After running the script:
1. Review the `fmt_update_log.txt` file for any important messages or warnings.
2. Check the `fmt_update_backups/` directory if you need to reference or restore any previous file versions.
3. If conflicts occurred, resolve them manually in your project files.
4. Test your application thoroughly to ensure the update didn't introduce any issues.
5. Commit the changes to your repository.

This update method allows you to keep your local customizations while still benefiting from the latest improvements and features of the Flask Modular Template.

## GUI Customization

Administrators can customize various aspects of the application's GUI:

- Company Name
- Body Color
- Project Name
- Project Name Color
- Project Icon
- Account Icon

To customize these elements:

1. Log in as an admin and navigate to the Admin Setup page.
2. Click on "GUI Setup" in the sidebar.
3. Modify the fields as desired:
   - For colors, you can use the color picker or enter a color name/hex code.
   - For icons, you can upload new PNG images to replace the current icons.
4. Click "Update Config" to save your changes.

Note: Icon images should be in PNG format and appropriately sized for best results.

## Adding New Modules

1. Create a new folder in `app/modules/` for your module (e.g., `app/modules/new_module/`).

2. Create a Python file for your module (e.g., `new_module.py`) with the following structure:

   ```python
   from flask import Blueprint, render_template

   blueprint = Blueprint('new_module', __name__, 
                         static_folder='static', 
                         static_url_path='/new_module/static',
                         template_folder='templates')

   @blueprint.route('/new_module_route')
   def new_module_view():
       return render_template('pages/new_module.html')
   ```

3. Create necessary templates in `app/modules/new_module/templates/pages/`.

4. Add any static files (CSS, JS) in `app/modules/new_module/static/`.

5. The module will be automatically discovered by the application. You don't need to manually update any configuration files or restart the application.

6. Follow the structure of the example modules provided in the `flask_mod_template` file set to ensure compatibility with the admin setup interface.

## Enabling Modules and Managing Access

1. Log in with an admin account (email listed in `ADMIN_USER_LIST` in `.env`).

2. Click on the account icon in the top-right corner and select "Admin Setup".

3. In the Admin Setup page, you can:
   - Modify GUI settings (Company Name, Body Color, Project Name, Project Name Color)
   - Enable/disable modules
   - Change the order of modules in the navigation menu
   - Modify module menu names
   - Manage roles and their associated modules
   - Assign roles to users
   - Configure email settings

4. To enable a new module:
   - Go to the "Module Setup" page
   - Find your new module in the list
   - Check the checkbox next to the module name
   - Click "Update Config" to apply changes

5. To control access for specific users:
   - Go to the "Role Setup" page
   - Create a new role or edit an existing one
   - Select the modules that should be accessible for this role
   - Go to the "User Setup" page
   - Assign the appropriate role to each user

6. The changes will take effect immediately for GUI settings, role assignments, and module enabling/disabling. No application restart is required.

## Role-Based Access Control

1. Roles are defined in the "Role Setup" page of the Admin Setup interface.

2. Each role can be associated with one or more modules.

3. Users are assigned roles in the "User Setup" page.

4. When a user logs in, they will only see and have access to the modules associated with their role.

5. The application now uses a proxy system for modules, which automatically handles access control. You don't need to use `@login_required` or `@module_access_required` decorators in your module code.

6. To set a default role for new users:
   - In the "Role Setup" page, use the "Default" checkbox next to the role you want to set as default.
   - Only one role can be set as default at a time.
   - New users will be automatically assigned this role upon registration or when added by an admin.
   - If no default role is set, new users will have no role assigned.

## User Management

1. In the Admin Setup, go to the "User Setup" page.

2. Here you can:
   - View all registered users
   - Assign or change user roles
   - Delete users
   - Add new users directly
   - Configure user access options

3. To add a new user:
   - Fill in the username and email in the "Add New User" section
   - Select a role (optional)
   - Click "Add User"
   - The new user will receive an activation email to set their password

4. User access options:
   - Require Login for Site Access: When enabled, makes the entire site (except login and registration pages) accessible only to logged-in users
   - Disable Self Registration: When enabled, prevents new users from registering themselves
   - Enable reCAPTCHA for Self Registration (see details in next section)
   - Enable/disable End User License Agreement (EULA)
   - Require EULA acknowledgment for new users and password resets

5. All changes in user management take effect immediately after saving.

### User Registration: reCAPTCHA

To enable reCAPTCHA on the user self-registration form:

1. In the Admin Setup, go to the "User Setup" page.
2. In the "Access Options" section, you'll see an option to "Enable Registration Captcha".
3. Before enabling this option, you need to set up reCAPTCHA for your site:
   - Click on the "reCAPTCHA Setup Instructions" button for detailed steps.
   - You'll need to visit the Google reCAPTCHA admin page, create a new site, and obtain Site and Secret keys.
   - Add these keys to your `.env` file as instructed.
4. After adding the keys and restarting your application, you can enable the "Enable Registration Captcha" option.
5. Once enabled, the registration form will include a reCAPTCHA "I'm not a robot" checkbox.

Note: Ensure you keep your reCAPTCHA Secret Key confidential and never expose it in client-side code or public repositories.

### End User License Agreement (EULA)

The application includes a customizable EULA feature:

1. In the Admin Setup, go to the "User Setup" page.
2. In the "Access Options" section, you can:
   - Enable or disable the EULA
   - Require EULA acknowledgment for new users and password resets
3. Customize the EULA content by editing the `app/templates/pages/eula.html` file.
4. The EULA will be presented to users during registration and password resets when enabled.

## Email Setup

The Email Setup interface now allows administrators to:
- Test email configuration without saving changes
- Update the current session with new email settings
- Save email settings to the .env file (if available)

This process ensures that email settings are working correctly before updating the application's configuration.

1. In the Admin Setup, go to the "Email Setup" page.

2. Here you can configure:
   - From Email Address
   - SMTP Server
   - SMTP Port
   - SMTP Username
   - SMTP Password
   - Test Email Address (for sending test emails)

3. Testing Email Configuration:
   - After entering the email configuration, click the "Test Email" button.
   - This will attempt to send a test email using the entered configuration.
   - If successful, you'll see a success message. If not, an error message will be displayed.
   - This test does not update the session or `.env` file, allowing you to safely test different configurations.

4. Updating Session:
   - Once you've successfully tested the email configuration, click the "Update Session" button.
   - This will update the current application session with the new email settings.
   - The changes will be active for the duration of the current application run but will not persist after a restart unless saved to the `.env` file.

5. Saving Settings (if .env file is available):
   - If your application is set up with a `.env` file, you'll see a "Save Settings" button.
   - After updating the session, click "Save Settings" to write the new email configuration to your `.env` file.
   - This ensures that your email settings persist across application restarts.
   - If no `.env` file is available, you'll see a warning icon next to the "Save Settings" button. Hovering over this icon will explain that the save operation is not supported without a `.env` file.

6. Important Notes:
   - Always test your email configuration before updating the session or saving to `.env`.
   - If you're using a `.env` file, remember to restart your application after saving new settings for them to take effect.
   - If you're not using a `.env` file, you'll need to manually update your server environment with any changes you want to persist across restarts.

By following this process, you can ensure that your email configuration is working correctly before applying it to your application, reducing the risk of email-related issues in your production environment.

## Error Handling and Logging

The application includes improved error handling and logging capabilities:

- Detailed error logs are stored in the `app_logs` directory
- Error emails can be sent to administrators (configurable in the Email Setup)
- User-friendly error pages for common HTTP errors (403, 404, 500)

### Log Configuration in .env

The logging system can be configured using the following variables in your `.env` file:

- `LOG_FILE_DIRECTORY`: Specifies the directory where log files will be stored. Default is './app_logs'.
- `LOG_FILE_LEVEL`: Sets the minimum level of messages to be logged to files. Options are 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'. Default is 'INFO'.
- `LOG_RETENTION_DAYS`: Determines how many days of log files to keep before automatic deletion. Default is 7 days.
- `LOG_EMAIL_ENABLE`: Enables or disables error email notifications. Set to 'True' to enable, 'False' to disable.
- `LOG_EMAIL_LEVEL`: Sets the minimum level of messages that trigger email notifications. Options are 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'. Default is 'ERROR'.
- `ADMIN_USER_LIST`: A comma-separated list of email addresses that will receive error notification emails.

Example configuration:

```
LOG_FILE_DIRECTORY=./app_logs
LOG_FILE_LEVEL=INFO
LOG_RETENTION_DAYS=7
LOG_EMAIL_ENABLE=True
LOG_EMAIL_LEVEL=ERROR
ADMIN_USER_LIST=admin1@example.com,admin2@example.com
```

This configuration stores logs in the './app_logs' directory, logs messages of level INFO and above, keeps log files for 7 days, enables error email notifications for ERROR and CRITICAL levels, and sends these notifications to the specified admin email addresses.

### Log Viewer for Admin Users

Admin users have access to a Log Viewer tool, which provides a user-friendly interface to view and analyze application logs:

1. Log in with an admin account.
2. Click on the account icon in the top-right corner and select "Log Viewer" from the dropdown menu.
3. The Log Viewer displays a list of available log files and their content.
4. You can filter log entries by log level (INFO, WARNING, ERROR, CRITICAL) and search for specific content.
5. The Log Viewer provides a convenient way to monitor application activity and troubleshoot issues.

### Using app.logger in Modules

When adding new modules, you can use the `app.logger` to log various events and errors. Here's how to use it in your module code:

```python
from flask import current_app

# In your module functions:
def some_function():
    # Log an info message
    current_app.logger.info("This is an informational message")

    # Log a warning
    current_app.logger.warning("This is a warning message")

    # Log an error
    current_app.logger.error("This is an error message")

    # Log a critical error
    current_app.logger.critical("This is a critical error message")

    # For debugging (only shown when DEBUG mode is enabled)
    current_app.logger.debug("This is a debug message")
```

Using `current_app.logger` ensures that your logs are consistent with the main application's logging configuration.

### Debug Logging

Debug logging is controlled by the `FLASK_DEBUG` setting in your `.env` file:

```
FLASK_DEBUG=True
```

When `FLASK_DEBUG` is set to `True`:

1. Debug-level log messages will be displayed in the console.
2. The application will run in debug mode, providing detailed error messages and stack traces in the browser.
3. The Flask development server will automatically reload when code changes are detected.

For production environments, always set `FLASK_DEBUG=False` to disable debug logging and prevent sensitive information from being exposed.

## FMT Testing

The Flask Modular Template project includes a set of test files to ensure the functionality of various components. These tests are located in the `app/services/tests/` directory. To run the tests:

1. Ensure you're in the project's root directory and your virtual environment is activated.
2. Run the tests using pytest:
   ```
   pytest app/services/tests/
   ```

The test files cover different aspects of the application:

- `test_auth_service.py`: Tests for authentication-related functions
- `test_auth_service_db.py`: Tests for database operations related to authentication
- `test_email_service.py`: Tests for email service functionality
- `test_log_service.py`: Tests for logging service

Running these tests regularly can help catch potential issues early in the development process and ensure that core functionalities are working as expected.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Deployment

This application can be deployed using various methods. We provide guides for two popular deployment options:

1. [AWS Elastic Beanstalk Deployment Guide](README_AWS_Elastic_Beanstalk.md): This guide provides detailed instructions on how to deploy the application using AWS Elastic Beanstalk, including setting up AWS, configuring Elastic Beanstalk, ensuring sufficient storage, and establishing automatic deployment from GitHub.

2. [PythonAnywhere Deployment Guide](README_PythonAnywhere.md): This guide walks you through the process of deploying the application on PythonAnywhere, a platform that makes it easy to host, run, and code Python in the cloud.

Choose the deployment method that best suits your needs and infrastructure preferences. Both guides provide step-by-step instructions to get your Flask Modular Template application up and running in their respective environments.