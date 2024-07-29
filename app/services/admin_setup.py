from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
import os
import json
import importlib

blueprint = Blueprint('admin', __name__, template_folder='admin_templates')

def get_available_modules():
    modules_dir = os.path.join(current_app.root_path, 'modules')
    available_modules = []
    for module in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, module)
        if os.path.isdir(module_path):
            for file in os.listdir(module_path):
                if file.endswith('.py') and file != '__init__.py':
                    module_name = f"app.modules.{module}.{file[:-3]}"
                    available_modules.append(module_name)
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

        for module in mod_config['MODULE_LIST']:
            module['enabled'] = module['name'] in request.form.getlist('modules')
            module['menu_name'] = request.form.get(f"menu_name_{module['name']}", module['menu_name'])

        with open(mod_config_path, 'w') as f:
            json.dump(mod_config, f, indent=4)
        
        current_app.config['MODULE_LIST'] = [module['name'] for module in mod_config['MODULE_LIST'] if module['enabled']]

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

    return render_template('pages/admin_setup.html', form_data=form_data, 
                           modules=mod_config['MODULE_LIST'])