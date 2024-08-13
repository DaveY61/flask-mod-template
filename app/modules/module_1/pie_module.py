from flask import Blueprint, render_template, request
from flask_login import login_required
from app.app import module_access_required
import os

# Automatically determine the module name and path
module_path = os.path.relpath(__file__, start=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
module_name = f'app.{module_path[:-3].replace(os.path.sep, ".")}'
static_url_path = f'/modules/{os.path.dirname(module_path)}/static'

blueprint = Blueprint('pie', __name__, 
                      static_folder='static', 
                      static_url_path=static_url_path,
                      template_folder='templates')

@blueprint.route('/pie_chart', methods=['GET', 'POST'])
@login_required
def pie_chart():
    values = {'value1': 25, 'value2': 25, 'value3': 25, 'value4': 25}
    
    if request.method == 'POST':
        values = {
            'value1': request.form.get('value1', 0),
            'value2': request.form.get('value2', 0),
            'value3': request.form.get('value3', 0),
            'value4': request.form.get('value4', 0)
        }
    
    return render_template('pages/pie_chart.html', values=values)
