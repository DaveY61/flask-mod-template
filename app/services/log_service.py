import logging
import os
from logging.handlers import TimedRotatingFileHandler
from flask import request, has_request_context
from flask.logging import default_handler
import smtplib
from email.message import EmailMessage

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.user_id = getattr(request, 'user_id', 'N/A')
        else:
            record.url = None
            record.remote_addr = None
            record.user_id = 'N/A'

        return super().format(record)

class EmailHandler(logging.Handler):
    def __init__(self, config):
        super().__init__()
        self.config = config

    def emit(self, record):
        if record.levelno == logging.ERROR:
            subject = "Error Log Notification"
            body = f"Error log entry:\n{self.format(record)}"
            self.send_email(subject, body)

    def send_email(self, subject, body):
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = self.config['EMAIL_FROM_ADDRESS']
        msg['To'] = self.config['ADMIN_USER_LIST']

        try:
            with smtplib.SMTP(self.config['SMTP_SERVER'], self.config['SMTP_PORT']) as server:
                server.starttls()
                server.login(self.config['SMTP_USERNAME'], self.config['SMTP_PASSWORD'])
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

def setup_logger(app):
    app.logger.removeHandler(default_handler)

    formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s\n'
        'User ID: %(user_id)s\n'
        'Function: %(funcName)s, Line: %(lineno)d, File: %(filename)s\n'
    )

    log_dir = app.config['LOG_FILE_DIRECTORY']
    os.makedirs(log_dir, exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'app.log'),
        when='midnight',
        interval=1,
        backupCount=app.config['LOG_RETENTION_DAYS']
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

    if app.config['EMAIL_ENABLE_ERROR']:
        email_handler = EmailHandler(app.config)
        email_handler.setLevel(logging.ERROR)
        email_handler.setFormatter(formatter)
        app.logger.addHandler(email_handler)

    app.logger.setLevel(logging.DEBUG)

def init_app_logger(app):
    setup_logger(app)

    @app.before_request
    def add_user_id_to_request():
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.user_id = request.user.id
        else:
            request.user_id = 'N/A'

# Usage in app.py or wherever you initialize your Flask app:
# from log_service import init_app
# init_app(app)

# Usage in your routes or other parts of your application:
# current_app.logger.debug("This is a debug message")
# current_app.logger.info("This is an info message")
# current_app.logger.warning("This is a warning message")
# current_app.logger.error("This is an error message")
# current_app.logger.critical("This is a critical message")