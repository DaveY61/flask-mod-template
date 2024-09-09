import logging
from logging.handlers import TimedRotatingFileHandler
from flask import request, has_request_context
from flask_login import current_user
from email.message import EmailMessage
from datetime import datetime
import smtplib
import os

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            if current_user.is_authenticated:
                record.user_id = current_user.id
                record.user_email = current_user.email
            else:
                record.user_id = 'N/A'
                record.user_email = 'N/A'
        else:
            record.url = None
            record.remote_addr = None
            record.user_id = 'N/A'
            record.user_email = 'N/A'

        return super().format(record)

class EmailHandler(logging.Handler):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setLevel(getattr(logging, config.get('LOG_EMAIL_LEVEL', 'ERROR')))

    def emit(self, record):
        if not self.config.get('LOG_EMAIL_ENABLE', False):
            return

        try:
            subject = "Error Log Notification"
            body = f"Error log entry:\n{self.format(record)}"
            self.send_email(subject, body)
        except Exception as e:
            # Temporarily disable email logging to avoid infinite loop
            original_email_enable = self.config['LOG_EMAIL_ENABLE']
            self.config['LOG_EMAIL_ENABLE'] = False
            
            try:
                # Log the error using the application logger
                from flask import current_app
                current_app.logger.critical(f"Failed to send error email. Reason: {str(e)}")
                current_app.logger.critical(f"Original error: {self.format(record)}")
            finally:
                # Restore the original email logging setting
                self.config['LOG_EMAIL_ENABLE'] = original_email_enable

    def send_email(self, subject, body):
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = self.config['EMAIL_FROM_ADDRESS']
        msg['To'] = self.config['ADMIN_USER_LIST']

        with smtplib.SMTP(self.config['SMTP_SERVER'], self.config['SMTP_PORT']) as server:
            server.starttls()
            server.login(self.config['SMTP_USERNAME'], self.config['SMTP_PASSWORD'])
            server.send_message(msg)

class HeaderFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None, utc=False, atTime=None):
        self.prefix = "app"
        self.ext = "log"
        self.backupCount = backupCount
        self.header = "Timestamp\tLog Level\tModule\tMessage\tUser ID\tUser Email\tRemote Address\tURL\tFunction\tLine\tFilename\n"
        
        # Ensure the initial filename is in the correct format
        dir_name = os.path.dirname(filename)
        self.baseFilename = os.path.join(dir_name, self._get_formatted_filename())
        
        super().__init__(self.baseFilename, when, interval, backupCount, encoding, utc=utc, atTime=atTime)
        self.date = self.get_current_date()

    def get_current_date(self):
        return datetime.now().date()
    
    def _get_formatted_filename(self):
        current_time = self.get_current_date()
        return f"{self.prefix}_{current_time.strftime('%Y-%m-%d')}.{self.ext}"

    def _open(self):
        if not os.path.exists(self.baseFilename):
            # If the file doesn't exist, create it and write the header
            with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                f.write(self.header)

            # New File/Date so check and delete old logs
            self.deleteOldLogs()
            
        else:
            # If the file exists, check its size
            if os.path.getsize(self.baseFilename) == 0:
                # If the file is empty, write the header
                with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                    f.write(self.header)
        
        # Open the file in append mode
        return open(self.baseFilename, 'a', encoding=self.encoding)

    def shouldRollover(self, record):
        if self.date != self.get_current_date():
            return True
        return False
    
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        
        self.date = self.get_current_date()
        self.baseFilename = os.path.join(os.path.dirname(self.baseFilename), self._get_formatted_filename())
        
        self.stream = self._open()
        
        # Clean up old log files
        self.deleteOldLogs()

    def deleteOldLogs(self):
        dir_name = os.path.dirname(self.baseFilename)
        
        log_files = []
        for filename in os.listdir(dir_name):
            if filename.startswith(self.prefix) and filename.endswith(self.ext):
                try:
                    file_date_str = filename.split('_')[1].split('.')[0]
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                    log_files.append((file_date, filename))
                except (IndexError, ValueError):
                    continue  # Skip files that don't match the expected format
        
        # Sort log files by date, newest first
        log_files.sort(reverse=True)
        
        # Keep only the most recent backupCount files (plus the current day)
        files_to_delete = log_files[self.backupCount + 1:]
        
        for _, filename in files_to_delete:
            os.remove(os.path.join(dir_name, filename))

    def emit(self, record):
        try:
            if self.shouldRollover(record):
                self.doRollover()
            super().emit(record)
            self.flush()
        except Exception:
            self.handleError(record)

def setup_logger(app):
    # Remove all existing handlers
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    formatter = RequestFormatter(
        '%(asctime)s\t%(levelname)s\t%(module)s\t%(message)s\t'
        '%(user_id)s\t%(user_email)s\t%(remote_addr)s\t%(url)s\t'
        '%(funcName)s\t%(lineno)d\t%(filename)s'
    )

    log_dir = app.config['LOG_FILE_DIRECTORY']
    os.makedirs(log_dir, exist_ok=True)

    log_file_path = os.path.join(log_dir, 'app.log')
    file_handler = HeaderFileHandler(
        filename=log_file_path,
        when='midnight',
        interval=1,
        backupCount=app.config['LOG_RETENTION_DAYS']
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, app.config.get('LOG_FILE_LEVEL', 'INFO')))
    app.logger.addHandler(file_handler)

    # Only add email handler if LOG_EMAIL_ENABLE is True
    if app.config.get('LOG_EMAIL_ENABLE', False):
        email_handler = EmailHandler(app.config)
        email_handler.setFormatter(formatter)
        app.logger.addHandler(email_handler)

    # Add console handler only if DEBUG is True
    if app.config.get('DEBUG', False):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)

    # Ensure all messages are passed to handlers
    app.logger.setLevel(logging.DEBUG)

    return app.logger.handlers

def init_logger(app):
    # Get the log directory from the config
    log_dir = app.config['LOG_FILE_DIRECTORY']

    # Check if the path is relative
    if not os.path.isabs(log_dir):
        # If it's relative, make it absolute based on the app's root path
        log_dir = os.path.abspath(os.path.join(app.root_path, '..', log_dir))
    
    # Update the config with the absolute path
    app.config['LOG_FILE_DIRECTORY'] = log_dir

    # Create the logger handlers (which also makes the folder if needed)
    setup_logger(app)