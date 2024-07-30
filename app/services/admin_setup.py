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
                
                # Get the file path of the module
                module_file = inspect.getfile(module)
                
                route = None
                view_name = None
                
                # Read the file and look for the route decorator
                with open(module_file, 'r') as file:
                    content = file.read()
                    # Look for the route decorator
                    match = re.search(r'@blueprint\.route\([\'"](.+?)[\'"]\)', content)
                    if match:
                        route = match.group(1).lstrip('/')
                    
                    # Look for the function definition after the route decorator
                    view_match = re.search(r'@blueprint\.route.*?\ndef\s+(\w+)', content, re.DOTALL)
                    if view_name:
                        view_name = view_match.group(1)
                
                return {
                    'name': module_name,
                    'blueprint_name': blueprint_name,
                    'route': route,
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
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('home'))

    gui_config_path = current_app.config['GUI_CONFIG_PATH']
    mod_config_path = current_app.config['MOD_CONFIG_PATH']
    
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

        # Update MODULE_LIST
        with open(mod_config_path, 'r') as f:
            mod_config = json.load(f)

        module_order = json.loads(request.form.get('module_order', '[]'))
        enabled_modules = set(request.form.getlist('modules'))
        
        modules_enabled_disabled = False
        new_module_list = []
        
        for module_name in module_order:
            module = next((m for m in mod_config['MODULE_LIST'] if m['name'] == module_name), None)
            if module:
                new_enabled = module_name in enabled_modules
                new_menu_name = request.form.get(f"menu_name_{module_name}", module.get('menu_name', ''))
                
                if new_enabled != module.get('enabled', False):
                    modules_enabled_disabled = True
                
                new_module = {
                    'name': module_name,
                    'enabled': new_enabled,
                    'menu_name': new_menu_name,
                    'blueprint_name': module['blueprint_name'],
                    'view_name': module['view_name'],
                    'route': module.get('route')  # Use .get() to avoid KeyError if 'route' is missing
                }
                
                new_module_list.append(new_module)
            else:
                print(f"Warning: Module {module_name} not found in existing configuration")

        # Update the module configuration
        mod_config['MODULE_LIST'] = new_module_list

        with open(mod_config_path, 'w') as f:
            json.dump(mod_config, f, indent=4)
        
        current_app.config['MODULE_LIST'] = new_module_list

        if modules_enabled_disabled:
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            flash('Configuration updated successfully!', 'success')

    # Read current values
    form_data = {
        'company_name': current_app.config['COMPANY_NAME'],
        'body_color': current_app.config['BODY_COLOR'],
        'project_name': current_app.config['PROJECT_NAME'],
        'project_name_color': current_app.config['PROJECT_NAME_COLOR']
    }

    with open(mod_config_path, 'r') as f:
        mod_config = json.load(f)

    available_modules = get_available_modules()
    existing_modules = {m['name']: m for m in mod_config['MODULE_LIST']}
    
    # Merge available modules with existing configuration and add new modules
    updated_module_list = []
    for module in available_modules:
        if module['name'] in existing_modules:
            existing_module = existing_modules[module['name']]
            # Preserve existing information, update only if new info is available
            if module['blueprint_name']:
                existing_module['blueprint_name'] = module['blueprint_name']
            if module['route']:
                existing_module['route'] = module['route']
            if module['view_name']:
                existing_module['view_name'] = module['view_name']
            updated_module_list.append(existing_module)
        else:
            # New module discovered
            new_module = {
                'name': module['name'],
                'enabled': False,  # Default to disabled for new modules
                'menu_name': module['name'].split('.')[-1],  # Default menu name to the last part of the module name
                'blueprint_name': module['blueprint_name'],
                'view_name': module['view_name'],
                'route': module['route']
            }
            updated_module_list.append(new_module)

    # Ensure all modules in the existing configuration are included
    for module_name, module in existing_modules.items():
        if module_name not in [m['name'] for m in updated_module_list]:
            updated_module_list.append(module)

    # Update the module configuration
    mod_config['MODULE_LIST'] = updated_module_list

    with open(mod_config_path, 'w') as f:
        json.dump(mod_config, f, indent=4)
    
    current_app.config['MODULE_LIST'] = updated_module_list

    return render_template('pages/admin_setup.html', form_data=form_data, 
                           modules=updated_module_list)