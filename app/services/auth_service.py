from flask import Blueprint, request, render_template, redirect, url_for, current_app, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.auth_service_forms import RegisterForm, LoginForm, ForgotForm, ResetForm, RemoveForm
from app.services.email_service import EmailService
from app.services.auth_service_db import add_user, get_user_by_email, get_user, update_user, update_user_activation, generate_token, get_token, delete_token, update_user_password, delete_user
from datetime import datetime
import uuid

blueprint = Blueprint('auth', __name__, template_folder='auth_templates')

def initialize_services():
    if not hasattr(current_app, 'services_initialized'):
        # Initialize email service
        email_service = EmailService(current_app.config)
        global send_email
        send_email = email_service.send_email

        # Mark services as initialized to avoid reinitialization on subsequent requests
        current_app.services_initialized = True

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    initialize_services()
    if request.method == 'GET':
        form = RegisterForm(request.form)
        return render_template('forms/register.html', form=form)

    # Otherwise handle the POST
    data = request.form
    username = data.get('username')
    email = data.get('email').lower()
    password = data.get('password')

    if not username or not email or not password:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    if get_user_by_email(email):
        return render_template('pages/register_failure.html', response_color="red"), 400

    hashed_password = generate_password_hash(password)
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    is_admin = email in current_app.config['ADMIN_USER_LIST']

    user = add_user(user_id, username, email, hashed_password, is_active=False, is_admin=is_admin)

    token = generate_token(user_id, 'activation')
    activation_link = url_for('auth.activate_account', token=token, _external=True)
    
    # Render the email template with the provided username and activation link
    email_body = render_template('email/activation_email.html', username=username, activation_link=activation_link)
    send_email([email], f"Activate your {current_app.config['PROJECT_NAME']} Account", email_body, html=True)

    return render_template('pages/register_success.html', response_color="green"), 201

@blueprint.route('/activate/<token>', methods=['GET'])
def activate_account(token):
    initialize_services()
    token_data = get_token(token, 'activation')
    if not token_data or token_data.expires_at < datetime.now():
        return render_template('pages/activate_failure.html', response_color="red"), 400

    user = get_user(token_data.user_id)
    if user:
        update_user_activation(user.id)
        delete_token(token)
        return render_template('pages/activate_success.html', response_color="green"), 200

    return render_template('pages/activate_failure.html', response_color="red"), 400

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    initialize_services()
    if request.method == 'GET':
        form = LoginForm(request.form)
        next_url = request.args.get('next')
        return render_template('forms/login.html', form=form, next=next_url)
    
    # Otherwise handle the POST
    data = request.form
    email = data.get('email').lower()
    password = data.get('password')
    next_url = data.get('next')

    if not email or not password:
        return render_template('pages/login_failure.html', response_color='red'), 400

    user = get_user_by_email(email)
    if not user or not user.check_password(password) or not user.is_active:
        return render_template('pages/login_failure.html', response_color='red'), 400

    # Update is_admin status based on ADMIN_USER_LIST
    is_admin = email in current_app.config['ADMIN_USER_LIST']
    user.is_admin = is_admin
    update_user(user)

    login_user(user)

    # Redirect to the next URL or home if next is not provided or is invalid
    if not next_url or next_url == 'None':
        next_url = url_for('home')

    return redirect(next_url)

@blueprint.route('/logout', methods=['GET'])
@login_required
def logout():
    initialize_services()
    logout_user()
    return redirect(url_for('home'))

@blueprint.route('/forgot', methods=['GET', 'POST'])
def forgot():
    initialize_services()
    if request.method == 'GET':
        form = ForgotForm(request.form)
        return render_template('forms/forgot.html', form=form)
    
    # Otherwise handle the POST
    data = request.form
    email = data.get('email').lower()

    if not email:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    user = get_user_by_email(email)
    if user:
        token = generate_token(user.id, 'reset')
        reset_link = url_for('auth.reset_password', token=token, _external=True)

        # Render the email template with the provided username and reset link
        email_body = render_template('email/forgot_password_email.html', username=user.username, activation_link=reset_link)
        send_email([email], f"Reset your {current_app.config['PROJECT_NAME']} Password", email_body, html=True)

    return render_template('pages/forgot_success.html', response_color="green"), 200

@blueprint.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):  
    initialize_services()
    if request.method == 'GET':
        form = ResetForm(request.form)
        return render_template('forms/reset.html', token=token, form=form)

    # Otherwise handle the POST
    data = request.form
    new_password = data.get('password')

    if not new_password:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    token_data = get_token(token, 'reset')
    if not token_data or token_data.expires_at < datetime.now():
        return render_template('pages/invalid_input.html', response_color="red"), 400

    hashed_password = generate_password_hash(new_password)
    user = get_user(token_data.user_id)
    if user:
        update_user_password(user.id, hashed_password)
        delete_token(token)
        return render_template('pages/reset_success.html', response_color="green"), 200

    return render_template('pages/invalid_input.html', response_color="red"), 400

@blueprint.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    initialize_services()
    if request.method == 'GET':
        form = RemoveForm(request.form)
        return render_template('forms/delete.html', form=form)

    # Otherwise handle the POST
    delete_user(current_user.id)
    logout_user()

    return render_template('pages/delete_success.html', response_color="green"), 200
