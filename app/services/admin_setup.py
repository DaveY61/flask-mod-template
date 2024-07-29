from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
import os
import json

blueprint = Blueprint('admin', __name__, template_folder='admin_templates')

@blueprint.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if not current_user.is_admin:
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('home'))

    config_path = os.path.join(os.path.dirname(__file__), '..', 'gui_config.cnf')
    
    if request.method == 'POST':
        # Get the new values from the form
        new_values = {
            'COMPANY_NAME': request.form.get('company_name'),
            'BODY_COLOR': request.form.get('body_color'),
            'PROJECT_NAME': request.form.get('project_name'),
            'PROJECT_NAME_COLOR': request.form.get('project_name_color')
        }

        # Update gui_config.cnf with new values
        with open(config_path, 'w') as f:
            json.dump(new_values, f, indent=4)
        
        # Update current_app.config with new values
        for key, value in new_values.items():
            current_app.config[key] = value

        flash('Configuration updated successfully!', 'success')

    # Read current values from current_app.config
    form_data = {
        'company_name': current_app.config['COMPANY_NAME'],
        'body_color': current_app.config['BODY_COLOR'],
        'project_name': current_app.config['PROJECT_NAME'],
        'project_name_color': current_app.config['PROJECT_NAME_COLOR']
    }

    return render_template('pages/admin_setup.html', form_data=form_data)