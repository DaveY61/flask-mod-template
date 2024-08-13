#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask import Flask, render_template, redirect, url_for, request, jsonify, abort, current_app, session, send_from_directory
from flask import url_for as flask_url_for, render_template as flask_render_template
from flask_login import LoginManager, current_user, login_required
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, PrefixLoader
from app.services.auth_service_db import setup_database, init_db
import pkgutil
import importlib
from dotenv import load_dotenv
from app.app_config import Config
from app.mod_config_manager import ConfigManager
import os
import contextlib

#----------------------------------------------------------------------------#
# Helper functions to register services and modules
#----------------------------------------------------------------------------#
def create_module_jinja_env(app, module_name, blueprint_name):
    module_template_folder = os.path.join(app.root_path, 'modules', module_name.split('.')[-2], 'templates')
    module_loader = FileSystemLoader(module_template_folder)
    
    # Combine the module loader with the app's existing loaders
    loaders = [module_loader]
    if isinstance(app.jinja_loader, ChoiceLoader):
        loaders.extend(app.jinja_loader.loaders)
    else:
        loaders.append(app.jinja_loader)
    
    # Create a new Jinja2 environment
    env = Environment(loader=ChoiceLoader(loaders))
    
    # Copy over the filters and globals from the app's Jinja environment
    env.filters.update(app.jinja_env.filters)
    env.globals.update(app.jinja_env.globals)
    
    # Create a custom url_for function
    def custom_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', '')
            if not filename.startswith(('css/', 'js/', 'img/')):
                # This is likely a module-specific static file
                return url_for('module_proxy', module_path=f"{blueprint_name}/static/{filename}")
        elif '.' in endpoint:
            # This is likely a module endpoint, so we need to adjust it
            module, view = endpoint.split('.')
            if module == blueprint_name:
                return url_for('module_proxy', module_path=f"{blueprint_name}/{view}", **values)
        return url_for(endpoint, **values)

    env.globals['url_for'] = custom_url_for
    
    return env

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
# Define Loaders for Dynamic Modules
#----------------------------------------------------------------------------#
config_manager = ConfigManager()

def create_module_loader(app):
    module_loaders = {}
    module_config = app.config['MODULE_LIST']
    
    for module in module_config:
        module_name = module['name']
        module_path = os.path.join(app.root_path, 'modules', module_name, 'templates')
        module_loaders[module_name] = FileSystemLoader(module_path)
    
    return PrefixLoader(module_loaders)

def setup_module_loader(app):
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        create_module_loader(app)
    ])

#----------------------------------------------------------------------------#
# Define App/Blueprint Functions for "create_app"
#----------------------------------------------------------------------------#
def create_app():
    # Load environment variables from .env file
    load_dotenv()
    
    # Create the Flask app with the specified template folder
    app = Flask(__name__)
    app.config.from_object(Config)

    # Store the original static folder
    app.config['ORIGINAL_STATIC_FOLDER'] = app.static_folder

    # Setup and initialize the database
    setup_database(app.config)
    with app.app_context():
        init_db()

    # Initialize login and config managers
    init_login_manager(app)
    config_manager.init_app(app)

    # Store config_manager in app for access in route functions
    app.config_manager = config_manager

    # Estbalish method to require login when enabled
    @app.before_request
    def require_login():
        # List of endpoints that don't require login
        public_endpoints = ['static', 'auth.login', 'auth.forgot', 'auth.reset_password', 'auth.create_password']
        
        if app.config['REQUIRE_LOGIN_FOR_SITE_ACCESS']:
            if not current_user.is_authenticated and request.endpoint not in public_endpoints:
                return redirect(url_for('auth.login', next=request.url))

    return app

#----------------------------------------------------------------------------#
# Create App
#----------------------------------------------------------------------------#
app = create_app()
setup_module_loader(app)

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
# Basic pages
@app.route('/')
def home():
    return render_template('pages/home.html')

@app.route('/about')
def about():
    return render_template('pages/about.html')

# Register blueprint routes for 'services'
register_blueprints(app, 'services')

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html', response_color="red"), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', response_color="red"), 404

@contextlib.contextmanager
def temporary_static_folder(app, folder):
    original_folder = app.static_folder
    app.static_folder = folder
    yield
    app.static_folder = original_folder

@app.route('/module_static/<blueprint_name>/<path:filename>')
def module_static(blueprint_name, filename):
    module_config = current_app.config_manager.get_module_config()
    for module in module_config.get('MODULE_LIST', []):
        if module['blueprint_name'] == blueprint_name:
            module_name = module['name'].split('.')[-2]
            module_static_folder = os.path.join(current_app.root_path, 'modules', module_name, 'static')
            return send_from_directory(module_static_folder, filename)
    abort(404)

# Proxy for enabled module pages
@app.route('/<path:module_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def module_proxy(module_path):
    app.logger.info(f"Accessing module_path: {module_path}")
    for module in app.config['MODULE_LIST']:
        app.logger.info(f"Checking module: {module['name']}, blueprint: {module['blueprint']}")
        if module['enabled'] and module_path.startswith(f"{module['blueprint']}/"):
            module_name = module['name']
            blueprint_name = module['blueprint']
            
            app.logger.info(f"Matched module: {module_name}")
            
            # Check if the user has access to this module
            allowed_modules = current_user.get_allowed_modules()
            if module_name not in allowed_modules:
                return jsonify({"error": "Access to this module is restricted"}), 403
            
            try:
                # Use the full module path for import
                full_module_path = f"app.modules.{module_name}"
                module_instance = importlib.import_module(full_module_path)
                app.logger.info(f"Imported module: {module_instance}")
                
                if not hasattr(module_instance, 'blueprint'):
                    app.logger.error(f"Module {module_name} does not have a 'blueprint' attribute")
                    app.logger.error(f"Module attributes: {dir(module_instance)}")
                    abort(404)
                
                blueprint = module_instance.blueprint
                app.logger.info(f"Blueprint: {blueprint}")
                
                # Extract the specific route within the module
                module_specific_path = '/' + module_path[len(f"{blueprint_name}/"):]
                app.logger.info(f"Module specific path: {module_specific_path}")
                
                # Find the appropriate view function based on the module_specific_path
                view_function = None
                for route, func_name in module['routes'].items():
                    app.logger.info(f"Checking route: {route} -> {func_name}")
                    if module_specific_path.startswith(route):
                        view_function = getattr(blueprint, func_name)
                        app.logger.info(f"Found view function: {view_function}")
                        break
                
                if view_function is None:
                    app.logger.error(f"No view function found for path: {module_specific_path}")
                    abort(404)
                
                # Call the view function
                return view_function()
            
            except Exception as e:
                app.logger.error(f"Error in module_proxy: {str(e)}", exc_info=True)
                abort(404)
    app.logger.error(f"No matching module found for path: {module_path}")
    abort(404)