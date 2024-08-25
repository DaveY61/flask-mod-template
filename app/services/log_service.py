import logging
import os
from logging.handlers import TimedRotatingFileHandler
from flask import request, has_request_context
from flask.logging import default_handler
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import time

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.user_id = getattr(request, 'user_id', 'N/A')
            record.user_email = getattr(request, 'user_email', 'N/A')
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
        self.setLevel(logging.ERROR)

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            subject = "Error Log Notification"
            body = f"Error log entry:\n{self.format(record)}"
            self.send_email(subject, body)

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
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None):
        # Define filename prefix and extenstion
        self.prefix = "app"
        self.ext = ".log"
        
        # Generate the initial filename with the correct date format
        initial_filename = self._get_formatted_filename(filename)
        super().__init__(initial_filename, when, interval, backupCount, encoding, delay, utc, atTime)
        self.header_written = False
        self.namer = self._namer

    def _get_formatted_filename(self, base_filename):
        dir_name, _ = os.path.split(base_filename)
        return os.path.join(dir_name, f"{self.prefix}_{datetime.now().strftime('%Y-%m-%d')}{self.ext}")

    def _namer(self, default_name):
        dir_name, _ = os.path.split(default_name)
        return self._get_formatted_filename(default_name)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        
        self.baseFilename = self._get_formatted_filename(self.baseFilename)
        self.stream = self._open()
        
        self.deleteOldLogs()
        
        self.rolloverAt = self.computeRollover(int(time.time()))
        self.header_written = False

    def emit(self, record):
        try:
            if self.shouldRollover(record):
                self.doRollover()
            if not self.header_written:
                header = "Timestamp\tLog Level\tModule\tMessage\tUser ID\tUser Email\tRemote Address\tURL\tFunction\tLine\tFilename\n"
                self.stream.write(header)
                self.header_written = True
            super().emit(record)
            self.flush()
        except Exception:
            self.handleError(record)

    def _open(self):
        stream = super()._open()
        if os.path.getsize(self.baseFilename) == 0:
            self.header_written = False
        return stream

    def deleteOldLogs(self):
        """Delete log files older than the retention period."""
        dir_name, base_name = os.path.split(self.baseFilename)
        file_names = os.listdir(dir_name)
        base_name, ext = os.path.splitext(base_name)
        base_name = base_name.rsplit('_', 1)[0]  # Remove the date part
        retention_date = datetime.now() - timedelta(days=self.backupCount)
        print(f"Deleting log files older than: {retention_date}")  # Debug print
        
        for file_name in file_names:
            if file_name.startswith(base_name) and file_name.endswith(ext):
                file_date_str = file_name.rsplit('_', 1)[-1].split('.')[0]
                try:
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                    if file_date < retention_date:
                        os.remove(os.path.join(dir_name, file_name))
                        print(f"Removed old log file: {file_name}")  # Debug print
                except ValueError:
                    # If the date parsing fails, skip this file
                    continue

def setup_logger(app):
    if not app.logger.handlers:
        app.logger.removeHandler(default_handler)

        formatter = RequestFormatter(
            '%(asctime)s\t%(levelname)s\t%(module)s\t%(message)s\t'
            '%(user_id)s\t%(user_email)s\t%(remote_addr)s\t%(url)s\t'
            '%(funcName)s\t%(lineno)d\t%(filename)s'
        )

        log_dir = app.config['LOG_FILE_DIRECTORY']
        os.makedirs(log_dir, exist_ok=True)

        log_file_path = os.path.join(log_dir, 'app.log')  # This will be formatted correctly by HeaderFileHandler
        file_handler = HeaderFileHandler(
            filename=log_file_path,
            when='midnight',
            interval=1,
            backupCount=app.config['LOG_RETENTION_DAYS']
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(file_handler)

        email_handler = EmailHandler(app.config)
        email_handler.setFormatter(formatter)
        app.logger.addHandler(email_handler)

        if app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)
            app.logger.addHandler(console_handler)

        app.logger.setLevel(logging.DEBUG)

    return app.logger.handlers

def init_logger(app):
    setup_logger(app)

    @app.before_request
    def add_user_info_to_request():
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.user_id = request.user.id
            request.user_email = request.user.email
        else:
            request.user_id = 'N/A'
            request.user_email = 'N/A'