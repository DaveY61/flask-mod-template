from app.app import app

if __name__ == '__main__':
    # Log Test log entries
    if ( True ):
        app.logger.debug("Debug log test")
        app.logger.info("Info log test")
        app.logger.warning("Warning log test")
        app.logger.error("Error log test")
        app.logger.critical("Critical log test")

    app.run(debug=True)