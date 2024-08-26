from flask import Blueprint, request, render_template, redirect, url_for, current_app, session, abort, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service_forms import RegisterForm, LoginForm, ForgotForm, ResetForm, RemoveForm, CreatePasswordForm
from app.services.email_service import EmailService, EmailError
from app.services.auth_service_db import add_user, get_user_by_email, get_user, update_user, update_user_activation, generate_token, get_token, delete_token, update_user_password, delete_user, get_default_role, update_user_role
from datetime import datetime
import uuid
import requests

blueprint = Blueprint('auth', __name__, template_folder='auth_templates')

def send_email_wrapper(to, subject, body, html=False):
    try:
        email_service = EmailService(current_app.config)
        email_service.send_email(to, subject, body, html=html)
    except EmailError as e:
        flash(f"Failed to send email: {str(e)}", "danger")
        current_app.logger.error(f"Email sending failed: {str(e)}")

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if current_app.config['DISABLE_SELF_REGISTRATION']:
        abort(404)

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

    # Verify reCAPTCHA
    if current_app.config['ENABLE_REGISTRATION_CAPTCHA']:
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            flash('Please complete the reCAPTCHA.', 'danger')
            return redirect(url_for('auth.register'))

        verify_response = requests.post(url=f"https://www.google.com/recaptcha/api/siteverify?secret={current_app.config['RECAPTCHA_SECRET_KEY']}&response={recaptcha_response}").json()

        if not verify_response['success']:
            flash('reCAPTCHA verification failed. Please try again.', 'danger')
            return redirect(url_for('auth.register'))

    user_id = str(uuid.uuid4())
    is_admin = email in current_app.config['ADMIN_USER_LIST']

    add_user(user_id, username, email, password, is_active=False, is_admin=is_admin)

    default_role = get_default_role()
    if default_role:
        update_user_role(user_id, default_role)

    token = generate_token(user_id, 'activation')
    activation_link = url_for('auth.activate_account', token=token, _external=True)
    
    # Render the email template with the provided username and activation link
    email_body = render_template('email/activation_email.html', username=username, activation_link=activation_link)
    send_email_wrapper([email], f"Activate your {current_app.config['PROJECT_NAME']} Account", email_body, html=True)

    return render_template('pages/register_success.html', response_color="green"), 201

@blueprint.route('/activate/<token>', methods=['GET'])
def activate_account(token):
    token_data = get_token(token, 'activation')
    if not token_data or token_data.expires_at < datetime.now():
        return render_template('pages/activate_failure.html', response_color="red"), 400

    user = get_user(token_data.user_id)
    if user:
        update_user_activation(user.id)
        delete_token(token)
        return render_template('pages/activate_success.html', response_color="green"), 200

    return render_template('pages/activate_failure.html', response_color="red"), 400

@blueprint.route('/create_password/<token>', methods=['GET', 'POST'])
def create_password(token):
    token_data = get_token(token, 'activation')
    if not token_data:
        abort(404)

    user = get_user(token_data.user_id)
    if not user:
        abort(404)

    if request.method == 'POST':
        form = CreatePasswordForm(request.form)
        if form.validate():
            update_user_password(user.id, form.password.data)
            update_user_activation(user.id)
            delete_token(token)
            flash('Password created successfully. You can now log in.', 'success')
            return redirect(url_for('auth.login'))
    else:
        form = CreatePasswordForm()

    return render_template('forms/create_password.html', form=form, token=token, is_admin_setup=not user.is_active)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
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
    
    # Check if the email is in the ADMIN_USER_LIST and not in the database
    admin_emails = current_app.config['ADMIN_USER_LIST']
    is_admin_email = email in admin_emails

    if not user and is_admin_email and password == 'admin':
        # Create a new inactive admin user
        user_id = str(uuid.uuid4())
        user = add_user(user_id, email.split('@')[0], email, 'temporary', is_active=False, is_admin=True)
        
        # Generate a token for password creation
        token = generate_token(user.id, 'activation', expiration=None)
        
        # Redirect to create password form
        return redirect(url_for('auth.create_password', token=token))
    elif not user or not user.check_password(password) or not user.is_active:
        return render_template('pages/login_failure.html', response_color='red'), 400

    # Update is_admin status based on ADMIN_USER_LIST
    is_admin = email in admin_emails
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
    logout_user()
    session.clear()
    return redirect(url_for('home'))

@blueprint.route('/forgot', methods=['GET', 'POST'])
def forgot():
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
        send_email_wrapper([email], f"Reset your {current_app.config['PROJECT_NAME']} Password", email_body, html=True)

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
    if not token_data or token_data.expires_at < datetime.now():
        return render_template('pages/invalid_input.html', response_color="red"), 400

    user = get_user(token_data.user_id)
    if user:
        update_user_password(user.id, new_password)
        
        # Check if the user's account is inactive, and activate it if so
        if not user.is_active:
            update_user_activation(user.id)
            flash('Your account has been activated.', 'success')
        
        delete_token(token)
        flash('Your password has been reset successfully.', 'success')
        return render_template('pages/reset_success.html', response_color="green"), 200

    return render_template('pages/invalid_input.html', response_color="red"), 400

@blueprint.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == 'GET':
        form = RemoveForm(request.form)
        return render_template('forms/delete.html', form=form)

    # Otherwise handle the POST
    delete_user(current_user.id)
    logout_user()

    return render_template('pages/delete_success.html', response_color="green"), 200
