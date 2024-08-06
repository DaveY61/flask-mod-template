#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask import Flask, render_template, flash, redirect, url_for
from flask_login import LoginManager, current_user
from app.services.auth_service_db import setup_database, init_db
import pkgutil
import importlib
from dotenv import load_dotenv
from app.app_config import Config
from functools import wraps

#----------------------------------------------------------------------------#
# Establish Flask User Mgmt
#----------------------------------------------------------------------------#
login_manager = LoginManager()

def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from app.services.auth_service_db import get_user
        return get_user(user_id)
    
#----------------------------------------------------------------------------#
# Define App/Blueprint Functions for "create_app"
#----------------------------------------------------------------------------#
def create_app():
    # Load environment variables from .env file
    load_dotenv()
    
    # Create the Flask app with the specified template folder
    app = Flask(__name__)
    app.config.from_object(Config)

    # Setup and initialize the database
    setup_database(app.config)
    with app.app_context():
        init_db()

    # Initialize login manager
    init_login_manager(app)

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
    for module in app.config['MODULE_LIST']:
        if module['enabled']:
            module_name = module['name']
            module = importlib.import_module(module_name)
            if hasattr(module, 'blueprint'):
                app.register_blueprint(getattr(module, 'blueprint'))

#----------------------------------------------------------------------------#
# Create App
#----------------------------------------------------------------------------#
app = create_app()

#----------------------------------------------------------------------------#
# Method for User Module Access checking
#----------------------------------------------------------------------------#
def module_access_required(module_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            allowed_modules = current_user.get_allowed_modules()
            if module_name not in allowed_modules:
                flash('Access to this module is restricted.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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