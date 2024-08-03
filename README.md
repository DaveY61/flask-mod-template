# Flask Modular Template

## Overview

Flask Modular Template is a scalable and modular Python Flask application template. It provides a structured foundation for building web applications with easily extendable modules, user authentication, and an admin setup interface.

## Features

- Modular architecture for easy scaling and maintenance
- User authentication system (register, login, password reset)
- Admin setup interface for GUI configuration and module management
- Sample modules (Pie Chart, CSV Upload) demonstrating integration
- Responsive design using Bootstrap 5
- Customizable styling through admin interface

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

   blueprint = Blueprint('new_module', __name__, 
                         static_folder='static', 
                         static_url_path='/modules/new_module/static',
                         template_folder='templates')

   @blueprint.route('/new_module_route')
   def new_module_view():
       return render_template('pages/new_module.html')
   ```

3. Create necessary templates in `app/modules/new_module/templates/pages/`.

4. Add any static files (CSS, JS) in `app/modules/new_module/static/`.

5. Update `app/mod_config.cnf` to include your new module:

   ```json
   {
     "MODULE_LIST": [
       {
         "name": "app.modules.new_module.new_module",
         "enabled": true,
         "menu_name": "New Module",
         "blueprint_name": "new_module",
         "view_name": "new_module_view"
       },
       ...
     ]
   }
   ```

6. Restart the application for the changes to take effect.

## Using the Admin Setup Page

1. Log in with an admin account (email listed in `ADMIN_USER_LIST` in `.env`).

2. Click on the account icon in the top-right corner and select "Admin Setup".

3. In the Admin Setup page, you can:
   - Modify GUI settings (Company Name, Body Color, Project Name, Project Name Color)
   - Enable/disable modules
   - Change the order of modules in the navigation menu
   - Modify module menu names

4. Click "Save Configuration" to apply changes. If you've enabled/disabled modules, you'll need to restart the application for the changes to take effect.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.