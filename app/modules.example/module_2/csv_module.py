from flask import Blueprint, render_template, request, redirect, current_app, flash
import csv
import io
import os

blueprint = Blueprint('csv', __name__,
                      static_folder='static',
                      static_url_path='/csv/static',
                      template_folder='templates')

uploaded_data = []

@blueprint.route('/upload_csv', methods=['GET', 'POST'])
def upload_csv():
    global uploaded_data
    if request.method == 'POST':
        try:
            file = request.files['file']
            if not file:
                raise ValueError("No file uploaded")

            if not file.filename.lower().endswith('.csv'):
                raise ValueError("Invalid file type. Please upload a CSV file.")

            # Check file size (e.g., limit to 5MB)
            if len(file.read()) > 5 * 1024 * 1024:
                file.seek(0)  # Reset file pointer
                raise ValueError("File size exceeds the limit (5MB)")

            file.seek(0)  # Reset file pointer after checking size
            stream = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
            csv_input = csv.reader(stream)

            # Validate CSV content (e.g., check for minimum number of rows and columns)
            uploaded_data = list(csv_input)
            if len(uploaded_data) < 2:  # At least header row and one data row
                raise ValueError("CSV file must contain at least a header row and one data row")
            if any(len(row) < 2 for row in uploaded_data):  # At least two columns
                raise ValueError("CSV file must contain at least two columns")

            flash('CSV file uploaded and processed successfully', 'success')
            current_app.logger.info(f"CSV file '{file.filename}' uploaded and processed successfully")
            return redirect('/csv/upload_csv')

        except ValueError as ve:
            flash(str(ve), 'danger')
            current_app.logger.warning(f"CSV upload error: {str(ve)}")
            uploaded_data = []
        except csv.Error as ce:
            flash(f'Error processing the CSV file: {str(ce)}', 'danger')
            current_app.logger.error(f"CSV processing error: {str(ce)}")
            uploaded_data = []
        except Exception as e:
            flash('An unexpected error occurred while processing the file.', 'danger')
            current_app.logger.error(f"Unexpected error in CSV upload: {str(e)}", exc_info=True)
            uploaded_data = []

    return render_template('pages/upload_csv.html', uploaded_data=uploaded_data)