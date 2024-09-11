#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask import Flask, render_template, redirect, url_for, request, abort, send_from_directory, render_template_string, current_app
from flask_login import LoginManager, current_user, login_required
from jinja2 import FileSystemLoader, ChoiceLoader, PrefixLoader
from jinja2.exceptions import TemplateNotFound
from app.services.auth_service_db import setup_database, init_db
from app.services.log_service import init_logger
import pkgutil
import importlib
from dotenv import load_dotenv
from app.app_config import Config
from app.mod_config_manager import ConfigManager
import os

#----------------------------------------------------------------------------#
# Helper functions to register services and modules
#----------------------------------------------------------------------------#
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
# Define method for "create_app"
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

    # Store config_manager in app for access in route functions
    app.config_manager = config_manager

    # Establish method to require login when enabled
    @app.before_request
    def require_login():
        # List of endpoints that don't require login
        public_endpoints = ['static', 'auth.login', 'auth.forgot', 'auth.reset_password', 'auth.create_password']
        
        if app.config['REQUIRE_LOGIN_FOR_SITE_ACCESS']:
            if not current_user.is_authenticated and request.endpoint not in public_endpoints:
                return redirect(url_for('auth.login', next=request.url))

    # Initialize the app logger service
    init_logger(app)
    app.logger.info("Application started")

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

@app.route('/eula')
def eula():
    if not current_app.config.get('ENABLE_EULA', False):
        abort(404)  # This will raise a 404 error
    return render_template('pages/eula.html')

@app.route('/about')
def about():
    return render_template('pages/about.html')

# Register blueprint routes for 'services'
register_blueprints(app, 'services')

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    current_app.logger.critical(f"{str(error)}")
    return render_template('errors/500.html', response_color="red"), 500

@app.errorhandler(404)
def not_found_error(error):
    current_app.logger.warning(f"{str(error)}")
    return render_template('errors/404.html', response_color="red"), 404

@app.errorhandler(403)
def forbidden_error(error):
    current_app.logger.warning(f"{str(error)}")
    return render_template('errors/403.html', response_color="red"), 404

# Proxy for enabled module pages
@app.route('/<path:module_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def module_proxy(module_path):
    def custom_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename')
            template_name = request.template_name if hasattr(request, 'template_name') else 'Unknown template'
            if filename:
                # Check both module-specific and main app static folders
                for module in app.config['MODULE_LIST']:
                    if module['enabled']:
                        module_static_folder = os.path.join(app.root_path, 'modules', module['name'], 'static')
                        file_path = os.path.join(module_static_folder, filename)
                        if os.path.isfile(file_path):
                            return f"/{module['blueprint']}/static/{filename}"
                
                app_static_folder = os.path.join(app.root_path, 'static')
                app_file_path = os.path.join(app_static_folder, filename)
                if os.path.isfile(app_file_path):
                    return url_for('static', filename=filename)
                
                raise FileNotFoundError(f"Static file '{filename}' not found in '{template_name}'")
            
            return url_for('static', filename=filename)
        
        if '.' in endpoint:
            blueprint, view = endpoint.split('.')
            for module in app.config['MODULE_LIST']:
                if module['blueprint'] == blueprint:
                    return url_for('module_proxy', module_path=f"{blueprint}/{view}", **values)
        
        return url_for(endpoint, **values)

    # Handle static file requests
    if 'static' in module_path:
        parts = module_path.split('/')
        blueprint_name = parts[0]
        static_path = '/'.join(parts[2:])
        
        for module in app.config['MODULE_LIST']:
            if module['blueprint'] == blueprint_name:
                static_folder = os.path.join(app.root_path, 'modules', module['name'], 'static')
                if os.path.isfile(os.path.join(static_folder, static_path)):
                    return send_from_directory(static_folder, static_path)
        
        return send_from_directory(app.static_folder, static_path)
    
    error_logged = False

    # Process module requests
    for module in app.config['MODULE_LIST']:
        if module['enabled'] and module_path.startswith(f"{module['blueprint']}/"):
            # Check if the user has permission to access this module
            if module['name'] not in current_user.get_allowed_modules():
                abort(403)  # Forbidden access

            module_name = module['name']
            blueprint_name = module['blueprint']
            module_file_name = module['module_file']
            
            try:
                module_file = importlib.import_module(f"app.modules.{module_name}.{module_file_name}")
                
                if not hasattr(module_file, 'blueprint'):
                    current_app.logger.error(f"Blueprint '{blueprint_name}' not found for Module: {module_name} in File: {module_file_name}.py")
                    error_logged = True
                    abort(500)
                
                module_specific_path = '/' + module_path[len(f"{blueprint_name}/"):]
                
                # Strict route matching
                view_function = None
                matched_route = None
                for route, func_name in module['routes'].items():
                    if module_specific_path == route:  # Exact match
                        matched_route = route
                        if hasattr(module_file, func_name):
                            view_function = getattr(module_file, func_name)
                            break
                
                if view_function is None:
                    if matched_route:
                        current_app.logger.error(f"View function '{func_name}()' not found for Module: {module_name} in File: {module_file_name}.py")
                        error_logged = True
                        abort(500)
                    else:
                        # No matching route found, continue to next module or eventually 404
                        continue
                
                template_error = None
                def custom_render_template(template_name, **context):
                    nonlocal template_error
                    request.template_name = template_name
                    context['url_for'] = custom_url_for
                    
                    template_path = os.path.join(app.root_path, 'modules', module_name, 'templates', template_name)
                    
                    try:
                        with open(template_path, 'r') as file:
                            template_content = file.read()
                    except FileNotFoundError:
                        template_error = f"Template '{template_name}' not found for Module: {module_name} in File: {module_file_name}.py"
                        raise TemplateNotFound(template_name)
                    
                    return render_template_string(template_content, **context)
                
                module_file.url_for = custom_url_for
                module_file.render_template = custom_render_template
                
                try:
                    return view_function()
                except TemplateNotFound:
                    if template_error:
                        current_app.logger.error(template_error)
                    else:
                        current_app.logger.error(f"Unexpected TemplateNotFound in Module: {module_name}, File: {module_file_name}.py")
                    error_logged = True
                    abort(500)
                except FileNotFoundError as e:
                    current_app.logger.error(f"{str(e)} for Module: {module_name} in File: {module_file_name}.py")
                    error_logged = True
                    abort(500)
                except Exception as e:
                    if not error_logged:
                        current_app.logger.error(f"Unexpected error in Module: {module_name}, File: {module_file_name}.py - {str(e)}")
                        error_logged = True
                    abort(500)
            
            except Exception as e:
                if not error_logged:
                    current_app.logger.error(f"Unexpected error in Module: {module_name}, File: {module_file_name}.py - {str(e)}")
                    error_logged = True
                abort(500)

    # If no module matched, it's a 404
    abort(404)