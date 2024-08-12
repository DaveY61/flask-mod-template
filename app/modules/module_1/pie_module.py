from flask import render_template, request

MODULE_INFO = {
    'blueprint_name': 'pie',
    'view_name': 'pie_chart',
    'menu_name': 'Pie Chart'
}

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
