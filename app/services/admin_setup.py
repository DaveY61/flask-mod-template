from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask import Blueprint as FlaskBlueprint
from flask_login import login_required, current_user
import os
import json
import sys
import importlib
import inspect
import re

blueprint = Blueprint('admin', __name__, template_folder='admin_templates')

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

@blueprint.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if not current_user.is_admin:
        flash('Access to the Admin Setup page is restricted.', 'danger')
        return redirect(url_for('home'))

    sidebar_menu = [
        {'icon': 'fas fa-cog', 'text': 'GUI Setup', 'action': 'showAdminSetup', 'params': ['gui']},
        {'icon': 'fas fa-puzzle-piece', 'text': 'Module Setup', 'action': 'showAdminSetup', 'params': ['modules']},
        {'icon': 'fas fa-user-tag', 'text': 'Roles Setup', 'action': 'showAdminSetup', 'params': ['roles']}
    ]

    return render_template('pages/admin_setup.html', use_sidebar=True, sidebar_menu=sidebar_menu)

@blueprint.route('/setup/<setup_type>', methods=['GET', 'POST'])
@login_required
def setup_type(setup_type):
    if not current_user.is_admin:
        flash('Access to the Admin Setup page is restricted.', 'danger')
        return redirect(url_for('home'))

    if setup_type == 'gui':
        return setup_gui()
    elif setup_type == 'modules':
        return setup_modules()
    elif setup_type == 'roles':
        return setup_roles()
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
                           sidebar_menu=[
                               {'icon': 'fas fa-cog', 'text': 'GUI Setup', 'action': 'showAdminSetup', 'params': ['gui']},
                               {'icon': 'fas fa-puzzle-piece', 'text': 'Module Setup', 'action': 'showAdminSetup', 'params': ['modules']},
                               {'icon': 'fas fa-user-tag', 'text': 'Roles Setup', 'action': 'showAdminSetup', 'params': ['roles']}
                           ])

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
                print(f"Warning: Module {module_name} not found in existing configuration or available modules")
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
                           sidebar_menu=[
                               {'icon': 'fas fa-cog', 'text': 'GUI Setup', 'action': 'showAdminSetup', 'params': ['gui']},
                               {'icon': 'fas fa-puzzle-piece', 'text': 'Module Setup', 'action': 'showAdminSetup', 'params': ['modules']},
                               {'icon': 'fas fa-user-tag', 'text': 'Roles Setup', 'action': 'showAdminSetup', 'params': ['roles']}
                           ])

@blueprint.route('/setup/roles', methods=['GET', 'POST'])
@login_required
def setup_roles():
    if not current_user.is_admin:
        flash('Access to the Admin Setup page is restricted.', 'danger')
        return redirect(url_for('home'))

    roles = current_app.config['ROLE_LIST']
    modules = current_app.config['MODULE_LIST']

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_role':
            role_name = request.form.get('role_name')
            role_description = request.form.get('role_description')
            all_modules = request.form.get('all_modules') == 'on'
            
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
        
        elif action == 'delete_role':
            role_name = request.form.get('role_name')
            roles = [role for role in roles if role['name'] != role_name]
        
        elif action == 'update_modules':
            role_name = request.form.get('role_name')
            selected_modules = request.form.getlist('modules')
            for role in roles:
                if role['name'] == role_name:
                    role['modules'] = selected_modules
                    break
        
        # Save updated roles to file
        with open(current_app.config['ROLE_CONFIG_PATH'], 'w') as f:
            json.dump(roles, f, indent=4)
        
        # Update the config
        current_app.config['ROLE_LIST'] = roles
        
        flash('Roles configuration updated successfully!', 'success')

    return render_template('pages/admin_setup_roles.html', 
                           roles=roles, 
                           modules=modules, 
                           use_sidebar=True,
                           sidebar_menu=[
                               {'icon': 'fas fa-cog', 'text': 'GUI Setup', 'action': 'showAdminSetup', 'params': ['gui']},
                               {'icon': 'fas fa-puzzle-piece', 'text': 'Module Setup', 'action': 'showAdminSetup', 'params': ['modules']},
                               {'icon': 'fas fa-user-tag', 'text': 'Roles Setup', 'action': 'showAdminSetup', 'params': ['roles']}
                           ])