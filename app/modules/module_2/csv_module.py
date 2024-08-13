from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
import csv
import io
import os

# Automatically determine the module name and path
module_path = os.path.relpath(__file__, start=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
module_name = f'app.{module_path[:-3].replace(os.path.sep, ".")}'
static_url_path = f'/modules/{os.path.dirname(module_path)}/static'

blueprint = Blueprint('csv', __name__,
                      static_folder='static',
                      static_url_path=static_url_path,
                      template_folder='templates')

uploaded_data = []

@blueprint.route('/upload_csv', methods=['GET', 'POST'])
@login_required
def upload_csv():
    global uploaded_data
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
            csv_input = csv.reader(stream)
            uploaded_data = [row for row in csv_input]
            return redirect(url_for('csv.upload_csv'))
    
    return render_template('pages/upload_csv.html', uploaded_data=uploaded_data)
