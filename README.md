# Flask Modular Template

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [GUI Customization](#GUI-Customization)
- [Adding New Modules](#adding-new-modules)
- [Enabling Modules and Managing Access](#enabling-modules-and-managing-access)
- [Role-Based Access Control](#role-based-access-control)
- [User Management](#user-management)
- [User Registration: reCAPTCHA](#User-Registration-reCAPTCHA)
- [Email Setup](#Email-Setup)
- [License](#license)
- [Deployment](#deployment)

## Overview

Flask Modular Template is a scalable and modular Python Flask application template. It provides a structured foundation for building web applications with easily extendable modules, user authentication, role-based access control, and an admin setup interface.

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

## Prerequisites

- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/flask-mod-template.git
   cd flask-mod-template
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add the following configurations:
   ```
   VS_PROJECT_FOLDER_NAME=your_project_folder_name
   LOG_FILE_DIRECTORY=./app_logs
   LOG_RETENTION_DAYS=30
   EMAIL_FAIL_DIRECTORY=./app_data/email
   EMAIL_FROM_ADDRESS=your_email@example.com
   EMAIL_ENABLE_ERROR=1
   SMTP_SERVER=your_smtp_server
   SMTP_PORT=587
   SMTP_USERNAME=your_smtp_username
   SMTP_PASSWORD=your_smtp_password
   ADMIN_USER_LIST=admin1@example.com,admin2@example.com
   USER_DATABASE_FILENAME=users.db
   USER_DATABASE_DIRECTORY=./app_data/users
   RECAPTCHA_SITE_KEY=your_captcha_site_key
   RECAPTCHA_SECRET_KEY=your_captcha_secret_key
   ```

   Note: Email-related settings can be configured through the Admin Setup Email page after initial setup.

5. Initialize the database:
   ```
   python -c "from app.services.auth_service_db import init_db; init_db()"
   ```

6. Run the application:
   ```
   python run.py
   ```

The application should now be running at `http://localhost:5000`.

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

5. All changes in user management take effect immediately after saving.

## User Registration: reCAPTCHA

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

## Email Setup

The Email Setup interface allows administrators to configure and test email settings without immediately applying changes to the application's configuration. This process ensures that email settings are working correctly before updating the application's session or the `.env` file.

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Deployment

This application can be deployed using various methods. We provide guides for two popular deployment options:

1. [AWS Elastic Beanstalk Deployment Guide](README_AWS_Elastic_Beanstalk.md): This guide provides detailed instructions on how to deploy the application using AWS Elastic Beanstalk, including setting up AWS, configuring Elastic Beanstalk, ensuring sufficient storage, and establishing automatic deployment from GitHub.

2. [PythonAnywhere Deployment Guide](README_PythonAnywhere.md): This guide walks you through the process of deploying the application on PythonAnywhere, a platform that makes it easy to host, run, and code Python in the cloud.

Choose the deployment method that best suits your needs and infrastructure preferences. Both guides provide step-by-step instructions to get your Flask Modular Template application up and running in their respective environments.