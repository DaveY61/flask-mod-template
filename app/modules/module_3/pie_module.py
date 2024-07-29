from flask import Blueprint, render_template, request
from flask_login import login_required

blueprint = Blueprint('pie2', __name__, 
                      static_folder='static', 
                      static_url_path='/modules/module_3/static',
                      template_folder='templates')

@blueprint.route('/pie_chart2', methods=['GET', 'POST'])
@login_required
def pie_chart2():
    values = {'value1': 25, 'value2': 25, 'value3': 25, 'value4': 25}
    
    if request.method == 'POST':
        values = {
            'value1': request.form.get('value1', 0),
            'value2': request.form.get('value2', 0),
            'value3': request.form.get('value3', 0),
            'value4': request.form.get('value4', 0)
        }
    
    return render_template('pages/pie_chart2.html', values=values)
