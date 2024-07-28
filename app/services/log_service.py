import os
import csv
from datetime import datetime
from inspect import currentframe, getframeinfo
from app.services.email_service import EmailService

class LogService:
    def __init__(self, config):
        self.config = config
        self.log_file_directory = config['LOG_FILE_DIRECTORY']
        self.retention_days = config['LOG_RETENTION_DAYS']
        self.enable_error_email = config['EMAIL_ENABLE_ERROR']
        self.admin_emails = config['ADMIN_USER_LIST']

        if not os.path.exists(self.log_file_directory):
            os.makedirs(self.log_file_directory)

    def log(self, log_type, message, user_id=None):
        log_file_path = self.get_log_file_path()
        frameinfo = getframeinfo(currentframe().f_back)
        log_entry = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': log_type,
            'message': message,
            'user_id': user_id,
            'function': frameinfo.function,
            'line': frameinfo.lineno,
            'file': frameinfo.filename,
        }

        with open(log_file_path, 'a', newline='') as log_file:
            writer = csv.DictWriter(log_file, fieldnames=log_entry.keys())

            # New log file is being created
            if log_file.tell() == 0:
                writer.writeheader()  # Write headers (once) in the new file
                self.clean_old_logs() # Check and remove any old log files

            # Write new row to the file
            writer.writerow(log_entry)

        if self.enable_error_email and log_type == 'ERROR':
            self.send_error_email(log_entry)

    def get_log_file_path(self):
        # Build the fully path specified log filename
        log_file_name = f"log_{datetime.now().strftime('%Y-%m-%d')}.csv"
        return os.path.join(self.log_file_directory, log_file_name)

    def clean_old_logs(self):
        # Determine "date" for today
        today = datetime.today().date()  # Get the current date without the time

        # Check for old log files
        for log_file in os.listdir(self.log_file_directory):

            # Build the fully path specified log filename
            log_file_path = os.path.join(self.log_file_directory, log_file)

            # Get the file creation date
            file_creation_date = datetime.fromtimestamp(os.path.getctime(log_file_path)).date()

            # Calculate the elapsed days
            elapsed_days = (today - file_creation_date).days

            # Compare elapsed with target days for log removal
            if (elapsed_days > self.retention_days):
                os.remove(log_file_path)

    def send_error_email(self, log_entry):
        subject = "Error Log Notification"
        body = f"Error log entry:\n{log_entry}"

        email_service = EmailService(self.config)
        email_service.send_email(self.admin_emails, subject, body)
