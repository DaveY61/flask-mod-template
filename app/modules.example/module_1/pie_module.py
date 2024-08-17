from flask import Blueprint, render_template, request

blueprint = Blueprint('pie', __name__, 
                      static_folder='static', 
                      static_url_path='/pie/static',
                      template_folder='templates')

@blueprint.route('/pie_chart', methods=['GET', 'POST'])
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
