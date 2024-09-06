from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo

# Set your classes here.

class RegisterForm(Form):
    username = StringField(
        'Username', validators=[DataRequired(), Length(min=4, max=25)]
    )
    email = StringField(
        'Email', validators=[DataRequired(), Length(min=6, max=40)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=4, max=40)]
    )

class CreatePasswordForm(Form):
    password = PasswordField(
        'New Password', validators=[DataRequired(), Length(min=4, max=40)]
    )
    confirm = PasswordField(
        'Confirm Password', validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.')
        ]
    )

class LoginForm(Form):
    email = StringField(
        'Email', validators=[DataRequired(), Length(min=6, max=40)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=4, max=40)]
    )

class ForgotForm(Form):
    email = StringField(
        'Email', validators=[DataRequired(), Length(min=6, max=40)]
    )

class ResetForm(Form):
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=4, max=40)]
    )

class RemoveForm(Form):
    email = StringField(
        'Email', validators=[DataRequired(), Length(min=6, max=40)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=4, max=40)]
    )
