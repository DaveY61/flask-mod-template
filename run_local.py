from app.app import app

if __name__ == '__main__':
    #----------------------------------------------------------------------------------------------------------------
    # Log Test log entries:
    #
    # Setting the condition below to 'True' will generate each of the supported log entry types
    #  - IF enabled in the .env with: "LOG_EMAIL_ENABLE=True"
    #  - THEN Critcal/Error email is sent to the Admin users: "ADMIN_USER_LIST=admin1@example.com,admin2@example.com"
    #      NOTE: Be sure your SMTP email is correctly enabled first!
    #----------------------------------------------------------------------------------------------------------------
    if ( False ):
        app.logger.debug("Debug log test")
        app.logger.info("Info log test")
        app.logger.warning("Warning log test")
        app.logger.error("Error log test")
        app.logger.critical("Critical log test")

    #----------------------------------------------------------------------------------------------------------------
    # NOTE: Do NOT use "debug=True" for app..run().  
    #       Always set "FLASK_DEBUG=True" in the .env for Development 
    #       This is needed in debug mode so the logging system will print logs to the console.
    #----------------------------------------------------------------------------------------------------------------
    app.run()