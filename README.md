# Flask Modular Template

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Adding New Modules](#adding-new-modules)
- [Enabling Modules and Managing Access](#enabling-modules-and-managing-access)
- [Role-Based Access Control](#role-based-access-control)
- [License](#license)
- [Deployment](#deployment)

## Overview

Flask Modular Template is a scalable and modular Python Flask application template. It provides a structured foundation for building web applications with easily extendable modules, user authentication, role-based access control, and an admin setup interface.

## Features

- Modular architecture for easy scaling and maintenance
- User authentication system (register, login, password reset)
- Role-based access control
- Admin setup interface for GUI configuration, module management, role management, user management, and email configuration
- Sample modules (Pie Chart, CSV Upload, Games) demonstrating integration
- Responsive design using Bootstrap 5
- Customizable styling through admin interface
- Sidebar navigation for admin pages and new modules

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
   VS_PROJECT_FOLDER_NAME=flask-mod-template
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

## Adding New Modules

1. Create a new folder in `app/modules/` for your module (e.g., `app/modules/new_module/`).

2. Create a Python file for your module (e.g., `new_module.py`) with the following structure:

   ```python
   from flask import Blueprint, render_template
   from flask_login import login_required
   from app.app import module_access_required
   import os

   # Automatically determine the module name and path
   module_path = os.path.relpath(__file__, start=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
   module_name = f'app.{module_path[:-3].replace(os.path.sep, ".")}'
   static_url_path = f'/modules/{os.path.dirname(module_path)}/static'

   blueprint = Blueprint('new_module', __name__, 
                         static_folder='static', 
                         static_url_path=static_url_path,
                         template_folder='templates')

   @blueprint.route('/new_module_route')
   @login_required
   @module_access_required(module_name)
   def new_module_view():
       return render_template('pages/new_module.html')
   ```

3. Create necessary templates in `app/modules/new_module/templates/pages/`.

4. Add any static files (CSS, JS) in `app/modules/new_module/static/`.

5. The module will be automatically discovered by the application. You don't need to manually update any configuration files.

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
   - Click "Save Configuration" to apply changes

5. To set a default role for new users: (optional)
   - Go to the "Role Setup" page
   - Select a role from the dropdown menu labeled "Default Role"
   - Click "Save Default Role" to apply the change
   - New users will now be automatically assigned this role upon registration
   - Note: The user's role can be changed later or set to "No Role" in the User Setup page

6. To control access for specific users:
   - Go to the "Role Setup" page
   - Create a new role or edit an existing one
   - Select the modules that should be accessible for this role
   - Go to the "User Setup" page
   - Assign the appropriate role to each user

6. The changes will take effect immediately for GUI settings and role assignments. For module enabling/disabling, you'll need to restart the application for the changes to take effect.

## Role-Based Access Control

1. Roles are defined in the "Role Setup" page of the Admin Setup interface.

2. Each role can be associated with one or more modules.

3. Users are assigned roles in the "User Setup" page.

4. When a user logs in, they will only see and have access to the modules associated with their role.

5. The `@module_access_required` decorator in each module's route ensures that only users with the appropriate role can access the module.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Deployment

This application can be deployed using various methods. One recommended approach is to use AWS Elastic Beanstalk, which provides an easy way to deploy and scale web applications.

For detailed instructions on how to deploy this application using AWS Elastic Beanstalk, including setting up AWS, configuring Elastic Beanstalk, ensuring sufficient storage, and establishing automatic deployment from GitHub, please refer to our [AWS Elastic Beanstalk Deployment Guide](README_AWS_Elastic_Beanstalk.md).