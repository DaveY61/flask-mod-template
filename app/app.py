#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, abort
from flask_login import LoginManager, current_user, login_required
from app.services.auth_service_db import setup_database, init_db
import pkgutil
import importlib
from dotenv import load_dotenv
from app.app_config import Config
from app.mod_config_manager import ConfigManager
from functools import wraps

login_manager = LoginManager()
config_manager = ConfigManager()

#----------------------------------------------------------------------------#
# Establish Flask User Mgmt
#----------------------------------------------------------------------------#
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

    # Initialize login and config managers
    init_login_manager(app)
    config_manager.init_app(app)

    @app.before_request
    def require_login():
        # List of endpoints that don't require login
        public_endpoints = ['static', 'auth.login', 'auth.forgot', 'auth.reset_password', 'auth.create_password']
        
        if app.config['REQUIRE_LOGIN_FOR_SITE_ACCESS']:
            if not current_user.is_authenticated and request.endpoint not in public_endpoints:
                return redirect(url_for('auth.login', next=request.url))

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

#----------------------------------------------------------------------------#
# Create App
#----------------------------------------------------------------------------#
app = create_app()

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

# Add proxy to handle enabled modules
@app.route('/<path:module_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def module_proxy(module_path):
    module_config = config_manager.get_module_config()
    for module in module_config['MODULE_LIST']:
        if module['enabled'] and module_path.startswith(f"{module['blueprint_name']}/"):
            module_name = module['name']
            
            # Check if the user has access to this module
            allowed_modules = current_user.get_allowed_modules()
            if module_name not in allowed_modules:
                return jsonify({"error": f"Access to the {module_name} module is restricted"}), 403
            
            try:
                module = importlib.import_module(module_name)
                view_function = getattr(module, module['view_name'])
                return view_function()
            except (ImportError, AttributeError):
                abort(404)
    abort(404)

# Register blueprint routes for 'services'
register_blueprints(app, 'services')

if __name__ == '__main__':
    app.run(debug=True)