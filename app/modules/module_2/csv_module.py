from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from app.app import module_access_required
import csv
import io

blueprint = Blueprint('csv', __name__,
                      static_folder='static',
                      static_url_path='/modules/module_2/static',
                      template_folder='templates')

uploaded_data = []

@blueprint.route('/upload_csv', methods=['GET', 'POST'])
@login_required
@module_access_required('app.modules.module_2.csv_module')
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
