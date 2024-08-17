from flask import Blueprint, render_template, request, redirect
import csv
import io

blueprint = Blueprint('csv', __name__,
                      static_folder='static',
                      static_url_path='/csv/static',
                      template_folder='templates')

uploaded_data = []

@blueprint.route('/upload_csv', methods=['GET', 'POST'])
def upload_csv():
    global uploaded_data
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
            csv_input = csv.reader(stream)
            uploaded_data = [row for row in csv_input]
            return redirect('/csv/upload_csv')  # Use a direct URL instead of url_for
    
    return render_template('pages/upload_csv.html', uploaded_data=uploaded_data)
