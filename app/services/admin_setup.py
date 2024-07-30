from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
import os
import json
import sys
import importlib
import inspect
from flask import Blueprint as FlaskBlueprint

blueprint = Blueprint('admin', __name__, template_folder='admin_templates')

def discover_module_info(module_name):
    try:
        module = importlib.import_module(module_name)
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, FlaskBlueprint):
                blueprint_name = obj.name
                routes = []
                for func_name, func in inspect.getmembers(obj):
                    if hasattr(func, '_rule'):
                        routes.append(func._rule)
                    elif hasattr(func, 'view_class'):
                        for method in func.view_class.methods:
                            route = getattr(func.view_class, method.lower(), None)
                            if route and hasattr(route, '_rule'):
                                routes.append(route._rule)
                return {
                    'name': module_name,
                    'blueprint_name': blueprint_name,
                    'route': routes[0] if routes else None
                }
        return None
    except ImportError:
        print(f"Warning: Unable to import module {module_name}")
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
        
        available_modules = {m['name']: m for m in get_available_modules()}
        
        for module_name in module_order:
            if module_name in [m['name'] for m in mod_config['MODULE_LIST']]:
                module = next(m for m in mod_config['MODULE_LIST'] if m['name'] == module_name)
                new_enabled = module_name in enabled_modules
                new_menu_name = request.form.get(f"menu_name_{module_name}", module.get('menu_name', ''))
                
                if new_enabled != module.get('enabled', False):
                    modules_enabled_disabled = True
                
                new_module = {
                    'name': module_name,
                    'enabled': new_enabled,
                    'menu_name': new_menu_name,
                    'blueprint_name': module['blueprint_name'],
                    'view_name': module['view_name']
                }
                
                if module_name in available_modules:
                    new_module['route'] = available_modules[module_name]['route']
                
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
    available_modules_dict = {m['name']: m for m in available_modules}
    
    # Merge available modules with existing configuration
    for module in mod_config['MODULE_LIST']:
        available_module = available_modules_dict.get(module['name'])
        if available_module:
            module['route'] = available_module['route']
        else:
            module['route'] = None
            print(f"Warning: Module {module['name']} not found in available modules")

    return render_template('pages/admin_setup.html', form_data=form_data, 
                           modules=mod_config['MODULE_LIST'])