from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session, jsonify
from flask import Blueprint as FlaskBlueprint
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.services.auth_service_db import is_email_taken, add_user, get_user, admin_required, get_all_users, update_user_role, delete_user, get_role_user_counts, get_default_role, update_default_role, generate_token
from app.services.email_service import EmailService
import os
import json
import sys
import importlib
import inspect
import re
import uuid

blueprint = Blueprint('admin', __name__, template_folder='admin_templates')

# Define the admin sidebar menu once
ADMIN_SIDEBAR_MENU = [
    {'icon': 'fas fa-cog', 'text': 'GUI Setup', 'action': 'showAdminSetup', 'params': ['gui']},
    {'icon': 'fas fa-puzzle-piece', 'text': 'Module Setup', 'action': 'showAdminSetup', 'params': ['modules']},
    {'icon': 'fas fa-user-tag', 'text': 'Role Setup', 'action': 'showAdminSetup', 'params': ['roles']},
    {'icon': 'fas fa-users', 'text': 'User Setup', 'action': 'showAdminSetup', 'params': ['users']},
    {'icon': 'fas fa-envelope', 'text': 'Email Setup', 'action': 'showAdminSetup', 'params': ['email']}
]

def discover_module_info(module_name):
    try:
        module = importlib.import_module(module_name)
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, FlaskBlueprint):
                blueprint_name = obj.name
                module_file = inspect.getfile(module)
                view_name = None
                
                with open(module_file, 'r') as file:
                    content = file.read()
                    view_match = re.search(r'@blueprint\.route.*?\ndef\s+(\w+)', content, re.DOTALL)
                    if view_match:
                        view_name = view_match.group(1)
                
                return {
                    'name': module_name,
                    'blueprint_name': blueprint_name,
                    'view_name': view_name
                }
        return None
    except ImportError:
        return None

def get_available_modules():
    modules_dir = os.path.join(current_app.root_path, 'modules')
    available_modules = []
    for module in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, module)
        if os.path.isdir(module_path):
            for file in os.listdir(module_path):
                if file.endswith('.py') and file != '__init__.py':
                    module_name = f"app.modules.{module}.{file[:-3]}"
                    module_info = discover_module_info(module_name)
                    if module_info:
                        available_modules.append(module_info)
    return available_modules

# function to save the user config
def save_user_config(config):
    with open(current_app.config['USER_CONFIG_PATH'], 'w') as f:
        json.dump(config, f, indent=4)

@blueprint.route('/setup', methods=['GET', 'POST'])
@login_required
@admin_required
def setup():
    return render_template('pages/admin_setup.html', use_sidebar=True, sidebar_menu=ADMIN_SIDEBAR_MENU)

@blueprint.route('/setup/<setup_type>', methods=['GET', 'POST'])
@login_required
@admin_required
def setup_type(setup_type):
    if setup_type == 'gui':
        return setup_gui()
    elif setup_type == 'modules':
        return setup_modules()
    elif setup_type == 'roles':
        return setup_roles()
    elif setup_type == 'users':
        return setup_users()
    elif setup_type == 'email':
        return setup_email()
    else:
        flash('Invalid setup type.', 'danger')
        return redirect(url_for('admin.setup'))

def setup_gui():
    gui_config_path = current_app.config['GUI_CONFIG_PATH']
    
    if request.method == 'POST':
        # Update GUI config
        new_gui_values = {
            'COMPANY_NAME': request.form.get('company_name'),
            'BODY_COLOR': request.form.get('body_color'),
            'PROJECT_NAME': request.form.get('project_name'),
            'PROJECT_NAME_COLOR': request.form.get('project_name_color')
        }

        with open(gui_config_path, 'w') as f:
            json.dump(new_gui_values, f, indent=4)
        
        for key, value in new_gui_values.items():
            current_app.config[key] = value

        # Handle project icon upload
        if 'project_icon' in request.files:
            project_icon = request.files['project_icon']
            if project_icon and project_icon.filename.lower().endswith('.png'):
                filename = secure_filename('project_icon.png')
                icon_path = os.path.join(current_app.root_path, 'static', 'img', filename)
                project_icon.save(icon_path)
                flash('Project icon updated successfully!', 'success')

        flash('GUI configuration updated successfully!', 'success')

    # Read current GUI values
    form_data = {
        'company_name': current_app.config['COMPANY_NAME'],
        'body_color': current_app.config['BODY_COLOR'],
        'project_name': current_app.config['PROJECT_NAME'],
        'project_name_color': current_app.config['PROJECT_NAME_COLOR']
    }

    return render_template('pages/admin_setup_gui.html', 
                           form_data=form_data, 
                           use_sidebar=True,
                           sidebar_menu=ADMIN_SIDEBAR_MENU)

def setup_modules():
    mod_config_path = current_app.config['MOD_CONFIG_PATH']
    
    # Get available modules from the file system
    available_modules = get_available_modules()
    
    # Read current configuration
    with open(mod_config_path, 'r') as f:
        mod_config = json.load(f)

    if request.method == 'POST':
        # Update MODULE_LIST
        module_order = json.loads(request.form.get('module_order', '[]'))
        enabled_modules = set(request.form.getlist('modules'))
        
        modules_enabled_disabled = False
        new_module_list = []
        
        existing_modules = {m['name']: m for m in mod_config['MODULE_LIST']}
        available_modules_dict = {m['name']: m for m in available_modules}
        
        # Use the module_order to sort the modules and include new modules
        for module_name in module_order:
            if module_name in existing_modules:
                module = existing_modules[module_name]
            elif module_name in available_modules_dict:
                module = available_modules_dict[module_name]
                module['enabled'] = False
                module['menu_name'] = module['name'].split('.')[-1]
            else:
                # Module {module_name} not found in existing configuration or available modules
                continue

            new_enabled = module_name in enabled_modules
            new_menu_name = request.form.get(f"menu_name_{module_name}", module.get('menu_name', ''))
            
            if new_enabled != module.get('enabled', False):
                modules_enabled_disabled = True
            
            new_module = {
                'name': module_name,
                'enabled': new_enabled,
                'menu_name': new_menu_name,
                'blueprint_name': module.get('blueprint_name'),
                'view_name': module.get('view_name')
            }
            
            new_module_list.append(new_module)

        # Add any new modules that weren't in the module_order
        for module in available_modules:
            if module['name'] not in [m['name'] for m in new_module_list]:
                new_module = {
                    'name': module['name'],
                    'enabled': False,
                    'menu_name': module['name'].split('.')[-1],
                    'blueprint_name': module['blueprint_name'],
                    'view_name': module['view_name']
                }
                
                new_module_list.append(new_module)

        # Update the module configuration
        mod_config['MODULE_LIST'] = new_module_list

        with open(mod_config_path, 'w') as f:
            json.dump(mod_config, f, indent=4)
        
        current_app.config['MODULE_LIST'] = new_module_list

        # After updating modules, update roles
        roles = current_app.config['ROLE_LIST']

        # Get the list of valid module names
        valid_module_names = [m['name'] for m in new_module_list]

        # Update roles to remove any modules that no longer exist
        for role in roles:
            role['modules'] = [m for m in role['modules'] if m in valid_module_names]

        # Save updated roles
        with open(current_app.config['ROLE_CONFIG_PATH'], 'w') as f:
            json.dump(roles, f, indent=4)

        # Update the config
        current_app.config['ROLE_LIST'] = roles

        if modules_enabled_disabled:
            flash('Module configuration updated. The application will restart for changes to take effect.', 'warning')
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            flash('Module configuration updated successfully!', 'success')

    return render_template('pages/admin_setup_modules.html', 
                           modules=mod_config['MODULE_LIST'],
                           use_sidebar=True,
                           sidebar_menu=ADMIN_SIDEBAR_MENU)

@blueprint.route('/setup/roles', methods=['GET', 'POST'])
@login_required
@admin_required
def setup_roles():
    roles = current_app.config['ROLE_LIST']
    modules = current_app.config['MODULE_LIST']
    default_role = get_default_role()

    user_counts = get_role_user_counts()

    def add_user_counts(roles_list):
        return [
            {**role, 'users_count': user_counts.get(role['name'], 0)}
            for role in roles_list
        ]

    roles_with_counts = add_user_counts(roles)

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_role':
            role_name = request.form.get('role_name')
            role_description = request.form.get('role_description')
            all_modules = request.form.get('all_modules') == 'on'
            is_default = request.form.get('new_role_default') == 'on'
            
            if any(role['name'] == role_name for role in roles):
                flash('A role with this name already exists. Please choose a different name.', 'danger')
            else:
                if all_modules:
                    selected_modules = [m['name'] for m in modules]
                else:
                    selected_modules = request.form.getlist('modules')
                
                new_role = {
                    'name': role_name,
                    'description': role_description,
                    'modules': selected_modules
                }
                roles.append(new_role)
                if is_default:
                    update_default_role(role_name)
                    default_role = role_name  # Update the local variable
                flash('New role added successfully.', 'success')
        
        elif action == 'delete_role':
            role_name = request.form.get('role_name')
            if user_counts.get(role_name, 0) == 0:
                roles = [role for role in roles if role['name'] != role_name]
                if default_role == role_name:
                    update_default_role(None)
                    default_role = None  # Update the local variable
                flash('Role deleted successfully.', 'success')
            else:
                flash('Cannot delete role while it\'s in use.', 'danger')
        
        elif action == 'update_role':
            role_name = request.form.get('role_name')
            new_description = request.form.get('role_description')
            selected_modules = request.form.getlist('modules')
            is_default = request.form.get('is_default') == 'true'
            
            for role in roles:
                if role['name'] == role_name:
                    role['description'] = new_description
                    role['modules'] = selected_modules
                    break
            
            if is_default:
                update_default_role(role_name)
                default_role = role_name  # Update the local variable
            elif default_role == role_name:
                update_default_role(None)
                default_role = None  # Update the local variable
            
            flash('Role updated successfully.', 'success')
        
        # Save updated roles to file
        with open(current_app.config['ROLE_CONFIG_PATH'], 'w') as f:
            json.dump(roles, f, indent=4)
        
        # Update the config
        current_app.config['ROLE_LIST'] = roles

        # Refresh roles_with_counts after any changes
        roles_with_counts = add_user_counts(roles)

    return render_template('pages/admin_setup_roles.html', 
                        roles=roles_with_counts, 
                        modules=modules,
                        default_role=default_role,
                        use_sidebar=True,
                        sidebar_menu=ADMIN_SIDEBAR_MENU)

# Update the setup_users function
@blueprint.route('/setup/users', methods=['GET', 'POST'])
@login_required
@admin_required
def setup_users():
    users = get_all_users()
    roles = current_app.config['ROLE_LIST']

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_role':
            user_id = request.form.get('user_id')
            new_role = request.form.get('user_role')
            user = get_user(user_id)
            if user:
                update_user_role(user_id, new_role)
                flash(f'Role updated for user {user.username}', 'success')
            else:
                flash('User not found', 'error')
        
        elif action == 'delete_user':
            user_id = request.form.get('user_id')
            delete_user(user_id)
            flash('User deleted successfully', 'success')
        
        elif action == 'update_access_options':
            user_config = {
                'DISABLE_SELF_REGISTRATION': request.form.get('disable_self_registration') == 'on',
                'REQUIRE_LOGIN_FOR_SITE_ACCESS': request.form.get('require_login_for_site_access') == 'on'
            }
            save_user_config(user_config)
            current_app.config.update(user_config)
            flash('Access options updated successfully', 'success')
        
        elif action == 'add_user':
            new_username = request.form.get('new_username')
            new_email = request.form.get('new_email', '').lower()  # Convert email to lowercase
            new_role = request.form.get('new_role') or None

            if not new_username or not new_email:
                return jsonify({'status': 'error', 'message': 'Username and email are required'}), 400

            if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400

            if is_email_taken(new_email):
                return jsonify({'status': 'error', 'message': 'Email address already exists'}), 400

            user_id = str(uuid.uuid4())
            add_user(user_id, new_username, new_email, current_app.config['SECRET_KEY'], is_active=False, user_role=new_role)
            
            # Generate non-expiring token
            token = generate_token(user_id, 'activation', expiration=None)
            activation_link = url_for('auth.create_password', token=token, _external=True)
            
            # Send activation email
            email_body = render_template('email/new_user_activation_email.html', username=new_username, activation_link=activation_link)

            # Create a temporary EmailService instance with the current configuration
            temp_email_service = EmailService(current_app.config)
            temp_email_service.send_email([new_email], f"Activate your {current_app.config['PROJECT_NAME']} Account", email_body, html=True)

            flash(f'User {new_username} added successfully. An activation email has been sent.', 'success')
            return jsonify({'status': 'success'})

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'success'})
        return redirect(url_for('admin.setup_type', setup_type='users'))

    return render_template('pages/admin_setup_users.html', 
                           users=users,
                           roles=roles,
                           use_sidebar=True,
                           sidebar_menu=ADMIN_SIDEBAR_MENU)

@blueprint.route('/setup/email', methods=['GET', 'POST'])
@login_required
@admin_required
def setup_email():
    # Initialize email_config with current values
    email_config = {
        'EMAIL_FROM_ADDRESS': current_app.config['EMAIL_FROM_ADDRESS'],
        'SMTP_SERVER': current_app.config['SMTP_SERVER'],
        'SMTP_PORT': current_app.config['SMTP_PORT'],
        'SMTP_USERNAME': current_app.config['SMTP_USERNAME'],
        'SMTP_PASSWORD': current_app.config['SMTP_PASSWORD'],
    }
    
    # Initialize test_email with the value from the form, session, or current user's email
    test_email = request.form.get('test_email')
    if not test_email:
        test_email = session.get('admin_test_email', current_user.email)

    if request.method == 'POST':
        action = request.form.get('action')

        # Update the email_config with form data for all actions
        email_config['EMAIL_FROM_ADDRESS'] = request.form.get('email_from_address')
        email_config['SMTP_SERVER'] = request.form.get('smtp_server')
        email_config['SMTP_PORT'] = int(request.form.get('smtp_port'))
        email_config['SMTP_USERNAME'] = request.form.get('smtp_username')
        email_config['SMTP_PASSWORD'] = request.form.get('smtp_password')

        # Update current_app.config
        current_app.config.update(email_config)

        # Save the test email in the session
        session['admin_test_email'] = test_email

        if action == 'update_config':
            flash('Email configuration updated in current session.', 'success')

        elif action == 'test_email':
            # Create a temporary EmailService instance with the current configuration
            temp_email_service = EmailService(current_app.config)

            subject = "Test Email from Admin Setup"
            body = "This is a test email sent from the Admin Setup page."

            try:
                temp_email_service.send_email([test_email], subject, body)
                flash('Test email sent successfully!', 'success')
            except Exception as e:
                flash(f'Error sending test email: {str(e)}', 'danger')

        elif action == 'save_and_restart':
            # Update .env file with new email configuration
            env_path = os.path.join(current_app.root_path, '..', '.env')
            
            # Email-related variables to update
            email_vars = [
                'EMAIL_FROM_ADDRESS',
                'SMTP_SERVER',
                'SMTP_PORT',
                'SMTP_USERNAME',
                'SMTP_PASSWORD'
            ]

            # Read existing .env file
            if os.path.exists(env_path):
                with open(env_path, 'r') as env_file:
                    env_lines = env_file.readlines()
            else:
                env_lines = []

            # Update email-related variables
            updated_vars = set()
            for i, line in enumerate(env_lines):
                for var in email_vars:
                    if line.strip().startswith(f"{var}="):
                        env_lines[i] = f"{var}={current_app.config[var]}\n"
                        updated_vars.add(var)
                        break

            # Add any missing email-related variables
            for var in email_vars:
                if var not in updated_vars:
                    env_lines.append(f"{var}={current_app.config[var]}\n")

            # Write updated content back to .env file
            with open(env_path, 'w') as env_file:
                env_file.writelines(env_lines)

            # Update the current process environment
            for var in email_vars:
                os.environ[var] = str(current_app.config[var])

            # Restart the Flask application
            os.execv(sys.executable, ['python'] + sys.argv)

    return render_template('pages/admin_setup_email.html',
                           use_sidebar=True,
                           sidebar_menu=ADMIN_SIDEBAR_MENU,
                           email_config=email_config,
                           test_email=test_email)

@blueprint.route('/setup/set_default_role', methods=['POST'])
@login_required
@admin_required
def set_default_role():
    role_name = request.form.get('default_role')
    update_default_role(role_name if role_name != 'none' else None)
    flash('Default role updated successfully.', 'success')
    return redirect(url_for('admin.setup_type', setup_type='roles'))