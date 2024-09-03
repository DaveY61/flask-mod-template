import os
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from flask import current_app

class EmailResult:
    def __init__(self, success, message):
        self.success = success
        self.message = message

class EmailService:
    def __init__(self, config):
        self.config = config
        self.smtp_server = None
        self.last_logged_error = None
        self.last_logged_time = None

    def _log_error(self, message, error_type, details):
        current_time = datetime.now()
        error_details = f"{details}"

        # Check if this error has been logged recently (within the last second)
        if (self.last_logged_error == error_details and 
            self.last_logged_time and 
            (current_time - self.last_logged_time) < timedelta(seconds=1)):
            return  # Skip logging if it's a duplicate within 1 second

        error_message = f"{message} - Type: {error_type}"
        if details:
            error_message += f", Details: {error_details}"
        
        current_app.logger.error(error_message)

        # Update the last logged error and time
        self.last_logged_error = error_details
        self.last_logged_time = current_time

    def connect_to_smtp(self):
        try:
            if self.smtp_server is None or not self.test_conn_open(self.smtp_server):
                self.smtp_server = self.create_conn()
            return True
        except (smtplib.SMTPException, ConnectionRefusedError, OSError) as e:
            self._log_error("Failed to connect to SMTP server", "connection_error", str(e))
            return False

    def test_conn_open(self, conn):
        try:
            status = conn.noop()[0]
        except smtplib.SMTPServerDisconnected:
            status = -1
        return status == 250

    def create_conn(self):
        try:
            new_smtp_server = smtplib.SMTP(self.config['SMTP_SERVER'], self.config['SMTP_PORT'])
            new_smtp_server.starttls()
            new_smtp_server.login(self.config['SMTP_USERNAME'], self.config['SMTP_PASSWORD'])
            return new_smtp_server
        except smtplib.SMTPException as e:
            self._log_error("Failed to create SMTP connection", "smtp_error", str(e))
            raise

    def send_email(self, to, subject, body, cc=None, bcc=None, attachments=None, html=False):
        try:
            if not self.connect_to_smtp():
                return EmailResult(False, "Failed to connect to SMTP server")

            msg = MIMEMultipart()
            msg['From'] = self.config['EMAIL_FROM_ADDRESS']
            msg['To'] = ", ".join(to)
            if cc:
                msg['Cc'] = ", ".join(cc)
            if bcc:
                msg['Bcc'] = ", ".join(bcc)
            msg['Subject'] = subject

            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            if attachments:
                for attachment in attachments:
                    with open(attachment, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                        msg.attach(part)

            recipients = to + (cc if cc else []) + (bcc if bcc else [])
            self.smtp_server.sendmail(self.config['EMAIL_FROM_ADDRESS'], recipients, msg.as_string())
            
            return EmailResult(True, "Email sent successfully")

        except smtplib.SMTPException as e:
            self.save_failed_email(msg)
            self._log_error("SMTP error occurred", "smtp_error", str(e))
            return EmailResult(False, "Failed to send email due to SMTP error")
        except Exception as e:
            self.save_failed_email(msg)
            self._log_error("Unexpected error occurred", "unexpected_error", str(e))
            return EmailResult(False, "Failed to send email due to an unexpected error")
        
    def save_failed_email(self, msg):
        try:
            if 'EMAIL_FAIL_DIRECTORY' not in self.config:
                raise ValueError("EMAIL_FAIL_DIRECTORY not configured")
            
            if not os.path.exists(self.config['EMAIL_FAIL_DIRECTORY']):
                os.makedirs(self.config['EMAIL_FAIL_DIRECTORY'])
                
            failed_email_path = os.path.join(self.config['EMAIL_FAIL_DIRECTORY'], f"failed_{int(datetime.now().timestamp())}.eml")
            with open(failed_email_path, 'w') as f:
                f.write(msg.as_string())
        except Exception as e:
            self._log_error("Failed to save failed email", "file_error", str(e))

    def check_and_resend_failed_emails(self):
        if not os.path.exists(self.config['EMAIL_FAIL_DIRECTORY']):
            return
        
        try:
            self.connect_to_smtp()  # Connect once at the beginning
            for filename in os.listdir(self.config['EMAIL_FAIL_DIRECTORY']):
                file_path = os.path.join(self.config['EMAIL_FAIL_DIRECTORY'], filename)
                with open(file_path, 'r') as f:
                    msg = email.message_from_file(f)
                try:
                    recipients = msg['To'].split(", ") + msg.get_all('Cc', []) + msg.get_all('Bcc', [])
                    self.smtp_server.sendmail(self.config['EMAIL_FROM_ADDRESS'], recipients, msg.as_string())
                    os.remove(file_path)
                except Exception:
                    continue  # Skip this email if there's an error, but continue with others
        finally:
            if self.smtp_server:
                self.smtp_server.quit()  # Close the connection when done
            self.smtp_server = None  # Reset the connection