from flask import Blueprint, request, session, render_template, redirect, url_for,current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.auth_service_forms import RegisterForm, LoginForm, ForgotForm, ResetForm, RemoveForm
from app.services.email_service import EmailService
from app.services.auth_service_db import setup_database, generate_token, create_user, get_user_by_email, update_user_activation, delete_user, get_token, delete_token, update_user_password
from datetime import datetime
import uuid

blueprint = Blueprint('auth', __name__, template_folder='auth_templates')

@blueprint.before_app_request
def initialize_services():
    if not hasattr(current_app, 'services_initialized'):
        # Initialize services that require application context here
        setup_database(current_app.config)
        email_service = EmailService(current_app.config)
        global send_email
        send_email = email_service.send_email

        # Mark services as initialized to avoid reinitialization on subsequent requests
        current_app.services_initialized = True

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        form = RegisterForm(request.form)
        return render_template('forms/register.html', form=form)

    # Otherwise handle the POST
    data = request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    if get_user_by_email(email):
        return render_template('pages/register_failure.html', response_color="red"), 400

    hashed_password = generate_password_hash(password)
    user_id = str(uuid.uuid4())
    created_at = datetime.now()

    create_user(user_id, username, email, hashed_password, created_at)

    token = generate_token(user_id, 'activation')
    activation_link = url_for('auth.activate_account', token=token, _external=True)
    
    # Render the email template with the provided username and activation link
    email_body = render_template('email/activation_email.html', username=username, activation_link=activation_link)
    send_email([email], f"Activate your {current_app.config.PROJECT_NAME} Account", email_body, html=True)

    return render_template('pages/register_success.html', response_color="green"), 201

@blueprint.route('/activate/<token>', methods=['GET'])
def activate_account(token):
    token_data = get_token(token, 'activation')
    if not token_data or token_data['expires_at'] < datetime.now():
        return render_template('pages/activate_failure.html', response_color="red"), 400

    update_user_activation(token_data['user_id'])
    delete_token(token)

    return render_template('pages/activate_success.html', response_color="green"), 200

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        form = LoginForm(request.form)
        return render_template('forms/login.html', form=form)
    
    # Otherwise handle the POST
    data = request.form
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return render_template('pages/login_failure.html', response_color='red'), 400

    user = get_user_by_email(email)
    if not user or not check_password_hash(user['password'], password) or not user['is_active']:
        return render_template('pages/login_failure.html', response_color='red'), 400

    session['user_id'] = user['id']
    session['username'] = user['username']

    return redirect(url_for('home'))

@blueprint.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('home'))

@blueprint.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'GET':
        form = ForgotForm(request.form)
        return render_template('forms/forgot.html', form=form)
    
    # Otherwise handle the POST
    data = request.form
    email = data.get('email')

    if not email:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    user = get_user_by_email(email)
    if user:
        token = generate_token(user['id'], 'reset')
        reset_link = url_for('auth.reset_password', token=token, _external=True)

        # Render the email template with the provided username and reset link
        email_body = render_template('email/forgot_password_email.html', username=user['username'], activation_link=reset_link)
        send_email([email], f"Reset your {current_app.config.PROJECT_NAME} Password", email_body, html=True)

    return render_template('pages/forgot_success.html', response_color="green"), 200

@blueprint.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):  
    if request.method == 'GET':
        form = ResetForm(request.form)
        return render_template('forms/reset.html', token=token, form=form)

    # Otherwise handle the POST
    data = request.form
    new_password = data.get('password')

    if not new_password:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    token_data = get_token(token, 'reset')
    if not token_data or token_data['expires_at'] < datetime.now():
        return render_template('pages/invalid_input.html', response_color="red"), 400

    hashed_password = generate_password_hash(new_password)
    update_user_password(token_data['user_id'], hashed_password)
    delete_token(token)

    return render_template('pages/reset_success.html', response_color="green"), 200

@blueprint.route('/delete', methods=['GET', 'POST'])
def delete():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    if request.method == 'GET':
        form = RemoveForm(request.form)
        return render_template('forms/delete.html', form=form)

    # Otherwise handle the POST
    
    delete_user(user_id)
    session.clear()

    return render_template('pages/delete_success.html', response_color="green"), 200
