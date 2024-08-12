from flask import render_template, request, redirect, url_for
import csv
import io

MODULE_INFO = {
    'blueprint_name': 'csv',
    'view_name': 'csv_upload',
    'menu_name': 'CSV Upload'
}

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
