from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.services.auth_service import create_user_account
from app.services.auth_service_db import is_email_taken, get_user, admin_required, get_all_users, update_user_role, delete_user, get_role_user_counts, get_default_role, update_default_role, generate_token
from app.services.email_service import EmailService
from app.mod_config_manager import ConfigManager
import os
import json
import ast
import re
from collections import defaultdict

blueprint = Blueprint('admin', __name__, template_folder='admin_templates')
config_manager = ConfigManager()

# Define the admin sidebar menu once
ADMIN_SIDEBAR_MENU = [
    {'icon': 'fas fa-cog', 'text': 'GUI Setup', 'action': 'showAdminSetup', 'params': ['gui']},
    {'icon': 'fas fa-puzzle-piece', 'text': 'Module Setup', 'action': 'showAdminSetup', 'params': ['modules']},
    {'icon': 'fas fa-user-tag', 'text': 'Role Setup', 'action': 'showAdminSetup', 'params': ['roles']},
    {'icon': 'fas fa-users', 'text': 'User Setup', 'action': 'showAdminSetup', 'params': ['users']},
    {'icon': 'fas fa-envelope', 'text': 'Email Setup', 'action': 'showAdminSetup', 'params': ['email']}
]

# Functions to update Module list
def update_module_list(app):
    modules_dir = os.path.join(app.root_path, 'modules')

    if not os.path.exists(modules_dir):
        return

    existing_modules = {m['name']: m for m in app.config.get('MODULE_LIST', [])}
    updated_modules = []

    for module_folder in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, module_folder)
        
        if os.path.isdir(module_path):
            try:
                module_info = extract_module_info(module_path, module_folder)
                if module_info:
                    if module_folder in existing_modules:
                        # Preserve existing menu name, enabled status, and order
                        module_info['menu_name'] = existing_modules[module_folder]['menu_name']
                        module_info['enabled'] = existing_modules[module_folder]['enabled']
                        module_info['order'] = existing_modules[module_folder]['order']
                    else:
                        # New module: use primary route as menu name, set as disabled by default, and add to end of list
                        default_menu_name = ' '.join(word.capitalize() for word in module_info['primary_route'].strip('/').replace('_', ' ').split())
                        module_info['menu_name'] = default_menu_name
                        module_info['enabled'] = False
                        module_info['order'] = len(existing_modules)
                    updated_modules.append(module_info)
            except Exception as e:
                current_app.logger.error(f"Error processing module {module_folder}: {str(e)}")

    # Sort modules based on their order
    updated_modules.sort(key=lambda x: x['order'])

    # Update the MODULE_LIST in the app config
    app.config['MODULE_LIST'] = updated_modules

    # Save the updated MODULE_LIST to mod_config.cnf
    try:
        save_module_config(app)
    except Exception as e:
        current_app.logger.error(f"Error saving module configuration: {str(e)}")

def extract_module_info(module_path, module_name):
    module_info = {
        'name': module_name,
        'blueprint': None,
        'primary_route': None,
        'routes': {},
        'module_file': None
    }
    
    for file_name in os.listdir(module_path):
        if file_name.endswith('.py'):
            file_path = os.path.join(module_path, file_name)
            try:
                with open(file_path, 'r') as file:
                    tree = ast.parse(file.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'blueprint':
                            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'Blueprint':
                                module_info['blueprint'] = node.value.args[0].s
                                module_info['module_file'] = file_name[:-3]  # Remove .py extension
                        elif isinstance(node, ast.FunctionDef):
                            for decorator in node.decorator_list:
                                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'route':
                                    route = decorator.args[0].s if decorator.args else ''
                                    module_info['routes'][route] = node.name
                                    if module_info['primary_route'] is None or len(route) < len(module_info['primary_route']):
                                        module_info['primary_route'] = route
            except Exception as e:
                current_app.logger.error(f"Error parsing file {file_path}: {str(e)}")
    
    return module_info if module_info['routes'] and module_info['module_file'] else None

def save_module_config(app):
    config_path = os.path.join(app.root_path, 'mod_config.cnf')
    with open(config_path, 'w') as config_file:
        json.dump(app.config['MODULE_LIST'], config_file, indent=2)

# Define blueprint for setup routes
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
        try:
            # Update GUI config
            new_gui_values = {
                'COMPANY_NAME': request.form.get('company_name'),
                'COMPANY_ADDRESS': request.form.get('company_address'),
                'COMPANY_CONTACT': request.form.get('company_contact'),
                'JURISDICTION': request.form.get('jurisdiction'),

                'BODY_COLOR': request.form.get('body_color'),

                'PROJECT_NAME': request.form.get('project_name'),
                'PROJECT_NAME_COLOR': request.form.get('project_name_color')
            }

            with open(gui_config_path, 'w') as f:
                json.dump(new_gui_values, f, indent=4)
            
            for key, value in new_gui_values.items():
                current_app.config[key] = value

            flash('GUI configuration updated successfully!', 'success')
            current_app.logger.info("GUI configuration updated successfully")

        except Exception as e:
            flash(f'Error updating GUI configuration: {str(e)}', 'danger')
            current_app.logger.error(f"Error updating GUI configuration: {str(e)}")

        # Handle project icon upload
        if 'project_icon' in request.files:
            project_icon = request.files['project_icon']
            if project_icon and project_icon.filename.lower().endswith('.png'):
                try:
                    filename = secure_filename('project_icon.png')
                    icon_path = os.path.join(current_app.root_path, 'static', 'img', filename)
                    project_icon.save(icon_path)
                    flash('Project icon updated successfully!', 'success')
                    current_app.logger.info("Project icon updated successfully")
                except Exception as e:
                    flash(f'Error updating project icon: {str(e)}', 'danger')
                    current_app.logger.error(f"Error updating project icon: {str(e)}")
            elif project_icon:
                flash('Invalid file format for project icon. Please use PNG.', 'warning')
                current_app.logger.warning("Invalid file format for project icon upload attempt")

        # Handle account icon upload
        if 'account_icon' in request.files:
            account_icon = request.files['account_icon']
            if account_icon and account_icon.filename.lower().endswith('.png'):
                try:
                    filename = secure_filename('account_icon.png')
                    icon_path = os.path.join(current_app.root_path, 'static', 'img', filename)
                    account_icon.save(icon_path)
                    flash('Account icon updated successfully!', 'success')
                    current_app.logger.info("Account icon updated successfully")
                except Exception as e:
                    flash(f'Error updating account icon: {str(e)}', 'danger')
                    current_app.logger.error(f"Error updating account icon: {str(e)}")
            elif account_icon:
                flash('Invalid file format for account icon. Please use PNG.', 'warning')
                current_app.logger.warning("Invalid file format for account icon upload attempt")

    # Read current GUI values
    form_data = {
        'company_name': current_app.config['COMPANY_NAME'],
        'company_address': current_app.config['COMPANY_ADDRESS'],
        'company_contact': current_app.config['COMPANY_CONTACT'],
        'jurisdiction': current_app.config['JURISDICTION'],

        'body_color': current_app.config['BODY_COLOR'],

        'project_name': current_app.config['PROJECT_NAME'],
        'project_name_color': current_app.config['PROJECT_NAME_COLOR']
    }

    return render_template('pages/admin_setup_gui.html', 
                           form_data=form_data, 
                           use_sidebar=True,
                           sidebar_menu=ADMIN_SIDEBAR_MENU)

def setup_modules():
    update_module_list(current_app)
    
    # Get the list of roles
    roles = current_app.config.get('ROLE_LIST', [])

    # Check for duplicate blueprints and other potential issues
    blueprint_count = defaultdict(int)
    for module in current_app.config['MODULE_LIST']:
        blueprint_count[module['blueprint']] += 1
        module['status'] = []
        
        # Check for duplicate blueprints
        if blueprint_count[module['blueprint']] > 1:
            module['status'].append(('error', 'Duplicate blueprint name'))
        
        # Check for missing or invalid primary route
        if not module['primary_route'] or not module['primary_route'].startswith('/'):
            module['status'].append(('error', 'Invalid or missing primary route'))
        
        # Check if the primary route exists in the routes dictionary
        if module['primary_route'] not in module['routes']:
            module['status'].append(('error', 'Primary route not found in module routes'))
        
        # Check if the blueprint name is valid
        if not module['blueprint'] or not module['blueprint'].isidentifier():
            module['status'].append(('error', 'Invalid blueprint name'))
    
        # Check if the module is enabled and assigned to roles
        if module['enabled']:
            assigned_roles = [role['name'] for role in roles if module['name'] in role.get('modules', [])]
            if assigned_roles:
                module['status'].append(('success', f"Enabled in {len(assigned_roles)} Role{'s' if len(assigned_roles) > 1 else ''}"))
            else:
                module['status'].append(('warning', "Enabled, but no assigned Roles"))
        else:
            module['status'].append(('info', "Disabled"))

    if request.method == 'POST':
        try:
            module_order = json.loads(request.form.get('module_order', '[]'))
            enabled_modules = set(request.form.getlist('modules'))
            
            for i, module_name in enumerate(module_order):
                module = next((m for m in current_app.config['MODULE_LIST'] if m['name'] == module_name), None)
                if module:
                    module['order'] = i
                    module['enabled'] = module_name in enabled_modules
                    module['menu_name'] = request.form.get(f"menu_name_{module_name}", module['menu_name'])
            
            current_app.config['MODULE_LIST'].sort(key=lambda x: x['order'])
            save_module_config(current_app)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'success', 'message': 'Module configuration updated successfully!'})
            else:
                flash('Module configuration updated successfully!', 'success')
                
        except Exception as e:
            current_app.logger.error(f"Error saving module configuration: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'error', 'message': str(e)}), 400
            else:
                flash(f'Error updating module configuration: {str(e)}', 'danger')
    
    return render_template('pages/admin_setup_modules.html', 
                           modules=current_app.config['MODULE_LIST'],
                           use_sidebar=True,
                           sidebar_menu=ADMIN_SIDEBAR_MENU)

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
        success_msg = "" # Blank Msg = No Change

        if action == 'add_role':
            role_name = request.form.get('role_name')
            role_description = request.form.get('role_description')
            all_modules = request.form.get('all_modules') == 'on'
            is_default = request.form.get('new_role_default') == 'on'
            
            if any(role['name'].lower() == role_name.lower() for role in roles):
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

                # Set Msg, Roles Changed
                success_msg = "New role added successfully."
        
        elif action == 'delete_role':
            role_name = request.form.get('role_name')
            if user_counts.get(role_name, 0) == 0:
                roles = [role for role in roles if role['name'] != role_name]
                if default_role == role_name:
                    update_default_role(None)
                    default_role = None  # Update the local variable

                # Set Msg, Roles Changed
                success_msg = "Role deleted successfully."

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
        
            # Set Msg, Roles Changed
            success_msg = "Role update successfully."

        # Save updated roles (if changed)
        if ( len(success_msg) > 0) :
            try:
                with open(current_app.config['ROLE_CONFIG_PATH'], 'w') as f:
                    json.dump(roles, f, indent=4)

                flash(success_msg, 'success')

            except Exception as e:
                current_app.logger.error(f"Error saving role configuration: {str(e)}")
                flash('Error saving role config (for details, see \'Log Viewer\')', 'danger')        

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
                try:
                    update_user_role(user_id, new_role)
                    current_app.logger.info(f"Role updated to '{new_role}' for {user.username} (Email: {user.email})")
                    flash(f'Role updated for user {user.username}', 'success')
                except Exception as e:
                    current_app.logger.error(f"Failed to update role for {user.username} (Email: {user.email}): {str(e)}")
                    flash(f'Failed to update role for user {user.username}: {str(e)}', 'danger')
            else:
                current_app.logger.warning(f"Attempted to update role for non-existent user ID: {user_id}")
                flash('User not found', 'warning')
        
        elif action == 'delete_user':
            user_id = request.form.get('user_id')
            user = get_user(user_id)
            if user:
                try:
                    delete_user(user.id)
                    current_app.logger.info(f"User account removed: {user.username} (Email: {user.email}), Method: admin deletion")
                    flash('User deleted successfully', 'success')
                except Exception as e:
                    current_app.logger.error(f"Failed to delete user {user.username} (Email: {user.email}): {str(e)}")
                    flash(f'Failed to delete user {user.username}: {str(e)}', 'danger')
            else:
                current_app.logger.warning(f"Attempted to delete non-existent user ID: {user_id}")
                flash('User not found', 'warning')
        
        elif action == 'update_access_options':
            try:
                user_config = {
                    'REQUIRE_LOGIN_FOR_SITE_ACCESS': request.form.get('require_login_for_site_access') == 'on',
                    'DISABLE_SELF_REGISTRATION': request.form.get('disable_self_registration') == 'on',
                    'ENABLE_REGISTRATION_CAPTCHA': request.form.get('enable_registration_captcha') == 'on',
                    'ENABLE_EULA': request.form.get('enable_eula') == 'on',
                    'ENABLE_EULA_ACKNOWLEDGEMENT': request.form.get('enable_eula_acknowledgement') == 'on'
                }

                with open(current_app.config['USER_CONFIG_PATH'], 'w') as f:
                    json.dump(user_config, f, indent=4)

                current_app.config.update(user_config)
                flash('Access options updated successfully', 'success')

            except Exception as e:
                current_app.logger.error(f"Failed to update access options: {str(e)}")
                flash(f'Failed to update access options: {str(e)}', 'danger')
        
        elif action == 'add_user':
            new_username = request.form.get('new_username')
            new_email = request.form.get('new_email', '').lower()
            new_role = request.form.get('new_role') or None

            if not new_username or not new_email:
                return jsonify({'status': 'error', 'message': 'Username and email are required'}), 400

            if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400

            if is_email_taken(new_email):
                return jsonify({'status': 'error', 'message': 'Email address already exists'}), 400

            user = create_user_account(new_username, new_email, current_app.config['SECRET_KEY'], is_active=False, user_role=new_role, creation_method="admin creation")
            
            # Generate non-expiring token
            token = generate_token(user.id, 'activation', expiration=None)
            activation_link = url_for('auth.create_password', token=token, _external=True)
            
            # Send activation email
            email_body = render_template('email/new_user_activation_email.html', username=new_username, activation_link=activation_link)
            
            email_service = EmailService(current_app.config)
            result = email_service.send_email([new_email], f"Activate your {current_app.config['PROJECT_NAME']} Account", email_body, html=True)

            if result.success:
                flash(f'User {new_username} added successfully. An activation email has been sent.', 'success')
                return jsonify({'status': 'success', 'message': f'User {new_username} added successfully. An activation email has been sent.'})
            else:
                flash(f'User {new_username} added successfully, but failed to send activation email: {result.message} (for details, see \'Log Viewer\')', 'danger no-auto-dismiss')
                return jsonify({'status': 'success', 'message': f'User {new_username} added successfully. BUT activation email has NOT been sent.'})
            
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'success'})
        return redirect(url_for('admin.setup_type', setup_type='users'))

    return render_template('pages/admin_setup_users.html', 
                           users=users,
                           roles=roles,
                           use_sidebar=True,
                           sidebar_menu=ADMIN_SIDEBAR_MENU)

def setup_email():
    # Load email configuration from app.config
    email_config = {
        'EMAIL_FROM_ADDRESS': current_app.config.get('EMAIL_FROM_ADDRESS', ''),
        'SMTP_SERVER': current_app.config.get('SMTP_SERVER', ''),
        'SMTP_PORT': current_app.config.get('SMTP_PORT', 587),
        'SMTP_USERNAME': current_app.config.get('SMTP_USERNAME', ''),
        'SMTP_PASSWORD': current_app.config.get('SMTP_PASSWORD', ''),
        'EMAIL_FAIL_DIRECTORY': current_app.config.get('EMAIL_FAIL_DIRECTORY', '')
    }

    # If session has email_config, use it (it means it was previously updated)
    if 'email_config' in session:
        email_config.update(session['email_config'])

    # Initialize test_email with the value from the form, session, or current user's email
    test_email = request.form.get('test_email')
    if not test_email:
        test_email = session.get('admin_test_email', current_user.email)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'test_email':
            temp_config = {
                'EMAIL_FROM_ADDRESS': request.form.get('email_from_address'),
                'SMTP_SERVER': request.form.get('smtp_server'),
                'SMTP_PORT': int(request.form.get('smtp_port')),
                'SMTP_USERNAME': request.form.get('smtp_username'),
                'SMTP_PASSWORD': request.form.get('smtp_password'),
                'EMAIL_FAIL_DIRECTORY': current_app.config['EMAIL_FAIL_DIRECTORY']
            }
            
            email_service = EmailService(temp_config)
            result = email_service.send_email(
                [request.form.get('test_email')],
                "Test Email from Admin Setup",
                "This is a test email sent from the Admin Setup page."
            )
            
            if result.success:
                return jsonify({'status': 'success', 'message': 'Test email sent successfully!'})
            else:
                return jsonify({'status': 'error', 'message': result.message + " (for details, see 'Log Viewer')"})

        elif action == 'update_session':
            try:
                email_config = {
                    'EMAIL_FROM_ADDRESS': request.form.get('email_from_address'),
                    'SMTP_SERVER': request.form.get('smtp_server'),
                    'SMTP_PORT': int(request.form.get('smtp_port')),
                    'SMTP_USERNAME': request.form.get('smtp_username'),
                    'SMTP_PASSWORD': request.form.get('smtp_password'),
                }
                # Update both session and app.config
                session['email_config'] = email_config
                current_app.config.update(email_config)
                return jsonify({'status': 'success', 'message': 'Email configuration updated in session and app config.'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Error updating configuration: {str(e)}'})

        elif action == 'save_settings':
            try:
                env_path = os.path.join(current_app.root_path, '..', '.env')
                
                if os.path.exists(env_path):
                    email_vars = [
                        'EMAIL_FROM_ADDRESS',
                        'SMTP_SERVER',
                        'SMTP_PORT',
                        'SMTP_USERNAME',
                        'SMTP_PASSWORD'
                    ]

                    with open(env_path, 'r') as env_file:
                        env_lines = env_file.readlines()

                    updated_vars = set()
                    for i, line in enumerate(env_lines):
                        for var in email_vars:
                            if line.strip().startswith(f"{var}="):
                                env_lines[i] = f"{var}={request.form.get(var.lower())}\n"
                                updated_vars.add(var)
                                break

                    for var in email_vars:
                        if var not in updated_vars:
                            env_lines.append(f"{var}={request.form.get(var.lower())}\n")

                    with open(env_path, 'w') as env_file:
                        env_file.writelines(env_lines)

                    return jsonify({'status': 'success', 'message': 'Email settings saved to .env file. Please restart your application for changes to take effect.'})
                else:
                    return jsonify({'status': 'error', 'message': 'No .env file found. Please update your server environment manually.'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Error saving settings: {str(e)}'})

    return render_template('pages/admin_setup_email.html',
                           use_sidebar=True,
                           sidebar_menu=ADMIN_SIDEBAR_MENU,
                           email_config=email_config,
                           test_email=test_email,
                           env_file_exists=os.path.exists(os.path.join(current_app.root_path, '..', '.env')))