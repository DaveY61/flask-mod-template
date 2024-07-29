#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from app.services.auth_service_db import User
import pkgutil
import importlib
from dotenv import load_dotenv
from app.app_config import Config

#----------------------------------------------------------------------------#
# Define App/Blueprint Functions for "create_app"
#----------------------------------------------------------------------------#
def create_app():
    # Load environment variables from .env file
    load_dotenv()
    
    # Create the Flask app with the specified template folder
    app = Flask(__name__)
    app.config.from_object(Config)
    #app.config['EXPLAIN_TEMPLATE_LOADING'] = True

    return app

def register_blueprints(app, package_name):
    # Dynamically discover/add routes for the package_name
    package = importlib.import_module(f'app.{package_name}')
    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if is_pkg:
            continue
        module = importlib.import_module(f"app.{package_name}.{module_name}")
        if hasattr(module, 'blueprint'):
            app.register_blueprint(getattr(module, 'blueprint'))

def register_modules_conditionally(app):
    for module_name in app.config['MODULE_LIST']:
        module = importlib.import_module(module_name)
        if hasattr(module, 'blueprint'):
            app.register_blueprint(getattr(module, 'blueprint'))

#----------------------------------------------------------------------------#
# Create App
#----------------------------------------------------------------------------#
app = create_app()

#----------------------------------------------------------------------------#
# Establish Flask User Mgmt
#----------------------------------------------------------------------------#
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

#----------------------------------------------------------------------------#
# Inject Config for calls to "render_template"
#----------------------------------------------------------------------------#
@app.context_processor
def inject_config():
   return dict(config=app.config)

#----------------------------------------------------------------------------#
# Inject User Status for calls to "render_template"
#----------------------------------------------------------------------------#
@app.context_processor
def inject_user():
    is_admin = False
    if current_user.is_authenticated:
        is_admin = current_user.is_admin
    return dict(is_admin=is_admin)

#----------------------------------------------------------------------------#
# Define App Route Endpoints
#----------------------------------------------------------------------------#
@app.route('/')
def home():
    return render_template('pages/home.html')

@app.route('/about')
def about():
    return render_template('pages/about.html')

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html', response_color="red"), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', response_color="red"), 404

# Register blueprint routes for 'services'
register_blueprints(app, 'services')

# Register blueprint routes for 'modules' (conditionally)
register_modules_conditionally(app)

if __name__ == '__main__':
    app.run(debug=True)