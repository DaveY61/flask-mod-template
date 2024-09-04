from flask import Blueprint, request, render_template, redirect, url_for, current_app, session, abort, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service_forms import RegisterForm, LoginForm, ForgotForm, ResetForm, RemoveForm, CreatePasswordForm
from app.services.email_service import EmailService
from app.services.auth_service_db import (
    add_user, get_user_by_email, get_user, get_default_role, delete_user,
    generate_token, get_token, delete_token, 
    update_user, update_user_password, update_user_activation, update_user_role, update_user_eula_acknowledgement,
    increment_login_attempts, reset_login_attempts)
from datetime import datetime
import uuid
import requests

blueprint = Blueprint('auth', __name__, template_folder='auth_templates')

# Auth Service Helper Functions
def send_email_wrapper(to, subject, body, html=False):
    email_service = EmailService(current_app.config)
    result = email_service.send_email(to, subject, body, html=html)
    
    if not result.success:
        flash(f"Failed to send email: {result.message}", "danger")
    
    return result.success

def handle_eula_acknowledgement(form_data, user=None):
    if current_app.config['ENABLE_EULA'] and current_app.config['ENABLE_EULA_ACKNOWLEDGEMENT']:
        if user and user.eula_acknowledged:
            return True  # User has already acknowledged EULA
        
        eula_acknowledged = form_data.get('eula_acknowledged') == 'on'
        if not eula_acknowledged:
            flash('Please acknowledge the End User License Agreement.', 'warning')
            return False
        if user:
            update_user_eula_acknowledgement(user.id, True)
    return True

def activate_user_account(user, activation_method):
    update_user_activation(user.id)
    current_app.logger.info(f"Account activated: {user.username} (Email: {user.email}), Method: {activation_method}")

def create_user_account(username, email, password, is_active=False, is_admin=False, user_role=None, eula_acknowledged=False, creation_method="self-registration"):
    user_id = str(uuid.uuid4())
    user = add_user(user_id, username, email, password, is_active, is_admin, user_role, eula_acknowledged)
    current_app.logger.info(f"Account added: {username} (Email: {email}), Method: {creation_method}")
    return user

# Auth Service routes
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
    eula_acknowledged = data.get('eula_acknowledged') == 'on'

    if not username or not email or not password:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    # Check if the email is in the ADMIN_USER_LIST
    is_admin = email in current_app.config['ADMIN_USER_LIST']

    if is_admin and password == 'admin':
        # Create a new inactive admin user
        user = create_user_account(username, email, password, is_active=False, is_admin=is_admin, eula_acknowledged=eula_acknowledged, creation_method="admin register")
        
        # Generate a token for password creation
        token = generate_token(user.id, 'activation', expiration=None)
        
        # Store EULA acknowledgment in session
        session['eula_acknowledged'] = eula_acknowledged
        
        # Redirect to create password form without eula_acknowledged parameter
        return redirect(url_for('auth.create_password', token=token))

    if get_user_by_email(email):
        current_app.logger.warning(f"Registration attempt with existing email: {email}")
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

    # Verify EULA Acknowledgement
    if not handle_eula_acknowledgement(request.form):
        return redirect(url_for('auth.register'))
    
    # Verified, so mark "acknowledged"" as "True" when it is enabled
    acknowledged = False
    if current_app.config['ENABLE_EULA'] and current_app.config['ENABLE_EULA_ACKNOWLEDGEMENT']:
        acknowledged = True

    # Pass all checks, add the new user
    user = create_user_account(username, email, password, is_active=False, is_admin=is_admin, eula_acknowledged=acknowledged)

    default_role = get_default_role()
    if default_role:
        update_user_role(user.id, default_role)

    token = generate_token(user.id, 'activation')
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
        activate_user_account(user, "activation token")
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

    is_admin_setup = user.is_admin and not user.is_active
    eula_acknowledged = session.get('eula_acknowledged', False)

    if request.method == 'POST':
        form = CreatePasswordForm(request.form)
        if form.validate():
            # Only check EULA if it wasn't already acknowledged
            if not eula_acknowledged and not handle_eula_acknowledgement(request.form, user):
                return render_template('forms/create_password.html', form=form, token=token, is_admin_setup=is_admin_setup, eula_acknowledged=eula_acknowledged)

            update_user_password(user.id, form.password.data)
            activate_user_account(user, "create password")
            delete_token(token)
            # Clear the session data
            session.pop('eula_acknowledged', None)
            flash('Password created successfully. You can now log in.', 'success')
            return redirect(url_for('auth.login'))
    else:
        form = CreatePasswordForm()

    return render_template('forms/create_password.html', form=form, token=token, is_admin_setup=is_admin_setup, eula_acknowledged=eula_acknowledged)

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
    
    # Check for lockout immediately
    if user and user.is_locked_out():
        lockout_time = user.lockout_until - datetime.utcnow()
        minutes = int(lockout_time.total_seconds() / 60)
        return render_template('pages/login_lockout.html', minutes=minutes), 403

    # Check if the email is in the ADMIN_USER_LIST
    admin_emails = current_app.config['ADMIN_USER_LIST']
    is_admin_email = email in admin_emails

    if is_admin_email and password == 'admin':
        if not user:
            # Create a new inactive admin user
            user = create_user_account(email.split('@')[0], email, 'temporary', is_active=False, is_admin=True, creation_method="admin login")

        elif not user.is_active:
            # If user exists but is not active, allow them to reset their password
            pass
        else:
            # If user exists and is active, this is an invalid login attempt
            return render_template('pages/login_failure.html', response_color='red'), 400
        
        # Generate a token for password creation
        token = generate_token(user.id, 'activation', expiration=None)
        
        # Redirect to create password form
        return redirect(url_for('auth.create_password', token=token))
    
    elif not user or not user.check_password(password) or not user.is_active:

        # Increment login attempt and Check for lockout 
        if user:
            increment_login_attempts(user.id)
            user = get_user_by_email(email)
            if user.is_locked_out():
                lockout_time = user.lockout_until - datetime.utcnow()
                minutes = int(lockout_time.total_seconds() / 60)
                return render_template('pages/login_lockout.html', minutes=minutes), 403
        
        return render_template('pages/login_failure.html', response_color='red'), 400

    # Update is_admin status based on ADMIN_USER_LIST
    is_admin = email in admin_emails
    user.is_admin = is_admin
    update_user(user)

    login_user(user)
    reset_login_attempts(user.id)
    current_app.logger.info(f"Successful login: {user.username} (Email: {user.email})")

    # Redirect to the next URL or home if next is not provided or is invalid
    if not next_url or next_url == 'None':
        next_url = url_for('home')

    return redirect(next_url)

@blueprint.route('/logout', methods=['GET'])
@login_required
def logout():
    current_app.logger.info(f"Logged out: {current_user.username} (Email: {current_user.email})")
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
    token_data = get_token(token, 'reset')
    if not token_data or token_data.expires_at < datetime.now():
        return render_template('pages/invalid_input.html', response_color="red"), 400

    user = get_user(token_data.user_id)
    if not user:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    if request.method == 'GET':
        form = ResetForm(request.form)
        return render_template('forms/reset.html', token=token, form=form, user=user)

    # Otherwise handle the POST
    data = request.form
    new_password = data.get('password')

    if not new_password:
        return render_template('pages/invalid_input.html', response_color="red"), 400

    # Pass the user object to handle_eula_acknowledgement
    if not handle_eula_acknowledgement(request.form, user):
        form = ResetForm(request.form)
        return render_template('forms/reset.html', token=token, form=form, user=user)

    update_user_password(user.id, new_password)
    
    # Check if the user's account is inactive, and activate it if so
    if not user.is_active:
        activate_user_account(user, "password reset")
        flash('Your account has been activated.', 'success')
    else:
        current_app.logger.info(f"Password reset: {user.username} (Email: {user.email})")
    
    reset_login_attempts(user.id)
    delete_token(token)
    return render_template('pages/reset_success.html', response_color="green"), 200

@blueprint.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == 'GET':
        form = RemoveForm(request.form)
        return render_template('forms/delete.html', form=form)

    # Otherwise handle the POST
    data = request.form
    email = data.get('email').lower()
    password = data.get('password')

    if not email or not password:
        flash('Please provide both email and password.', 'warning')
        return redirect(url_for('auth.delete'))

    if email != current_user.email:
        flash('The provided email does not match your account.', 'warning')
        return redirect(url_for('auth.delete'))

    if not current_user.check_password(password):
        flash('Incorrect password.', 'warning')
        return redirect(url_for('auth.delete'))

    current_app.logger.info(f"Account removed: {current_user.username} (Email: {current_user.email}), Method: self-deletion")
    delete_user(current_user.id)
    logout_user()

    return render_template('pages/delete_success.html', response_color="green"), 200    