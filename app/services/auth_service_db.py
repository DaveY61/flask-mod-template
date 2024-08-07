from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.exc import OperationalError
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user
import os
import uuid
from datetime import datetime, timedelta

engine = None
Session = None

def get_base():
    Base = declarative_base()

    class User(Base, UserMixin):
        __tablename__ = 'users'
        id = Column(String, primary_key=True)
        username = Column(String, nullable=False)
        email = Column(String, nullable=False, unique=True)
        password = Column(String, nullable=False)
        is_active = Column(Boolean, default=False)
        is_admin = Column(Boolean, default=False)
        created_at = Column(DateTime, default=func.now())
        user_role = Column(String)
        tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")

        def check_password(self, password):
            return check_password_hash(self.password, password)

        def get_allowed_modules(self):
            allowed_modules = []
            user_role = next((role for role in current_app.config['ROLE_LIST'] if role['name'] == self.user_role), None)
            
            if user_role:
                for module in current_app.config['MODULE_LIST']:
                    if module['enabled'] and module['name'] in user_role['modules']:
                        allowed_modules.append(module['name'])
            
            return allowed_modules

    class Token(Base):
        __tablename__ = 'tokens'
        id = Column(String, primary_key=True)
        user_id = Column(String, ForeignKey('users.id'))
        token = Column(String, nullable=False)
        token_type = Column(String, nullable=False)
        expires_at = Column(DateTime, nullable=False)
        user = relationship("User", back_populates="tokens")

    class DefaultRole(Base):
        __tablename__ = 'default_role'
        id = Column(Integer, primary_key=True)
        role_name = Column(String, nullable=True)

    return Base, User, Token, DefaultRole

Base, User, Token, DefaultRole = get_base()

def setup_database(config):
    global engine, Session, Base
    database_path = config['USER_DATABASE_PATH']
    if database_path != ':memory:':
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
    engine = create_engine(f'sqlite:///{database_path}', connect_args={'check_same_thread': False})
    Session = sessionmaker(bind=engine)
    Base, User, Token, DefaultRole = get_base()
    Base.metadata.bind = engine

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    if Session is None:
        raise RuntimeError("Database is not initialized. Call setup_database first.")
    return Session()

def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash("Access to Administer pages is restricted", "error")
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    return decorated_view

def add_user(id, username, email, password, is_active=False, is_admin=False, user_role=None):
    with get_db() as session:
        user = User(
            id=id,
            username=username,
            email=email,
            password=generate_password_hash(password, method='scrypt'),
            is_active=is_active,
            is_admin=is_admin,
            user_role=user_role
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

def get_user(user_id):
    with get_db() as session:
        return session.query(User).filter(User.id == user_id).first()

def get_user_by_email(email):
    with get_db() as session:
        return session.query(User).filter(User.email == email).first()

def update_user(user):
    with get_db() as session:
        session.merge(user)
        session.commit()

def delete_user(user_id):
    with get_db() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            session.commit()

def get_all_users():
    with get_db() as session:
        return session.query(User).all()

def get_role_user_counts():
    with get_db() as session:
        return dict(session.query(User.user_role, func.count(User.id)).group_by(User.user_role).all())

def generate_token(user_id, token_type):
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=20)
    with get_db() as session:
        new_token = Token(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            token_type=token_type,
            expires_at=expires_at
        )
        session.add(new_token)
        session.commit()
    return token

def get_token(token, token_type):
    with get_db() as session:
        token_obj = session.query(Token).filter(Token.token == token, Token.token_type == token_type).first()
        if token_obj and token_obj.expires_at > datetime.now():
            return token_obj
        return None

def delete_token(token):
    with get_db() as session:
        token_obj = session.query(Token).filter(Token.token == token).first()
        if token_obj:
            session.delete(token_obj)
            session.commit()

# Support for Default role

def get_default_role():
    try:
        with get_db() as session:
            default_role = session.query(DefaultRole).first()
            return default_role.role_name if default_role else None
    except OperationalError:
        # Table doesn't exist yet, so there's no default role
        return None

def update_default_role(role_name):
    try:
        with get_db() as session:
            default_role = session.query(DefaultRole).first()
            if default_role:
                default_role.role_name = role_name
            else:
                default_role = DefaultRole(role_name=role_name)
                session.add(default_role)
            session.commit()
    except OperationalError:
        # Table doesn't exist, so create it and add the default role
        Base.metadata.create_all(bind=engine)
        with get_db() as session:
            default_role = DefaultRole(role_name=role_name)
            session.add(default_role)
            session.commit()

# Additional helper functions

def update_user_role(user_id, role):
    with get_db() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.user_role = role
            session.commit()

def update_user_activation(user_id):
    with get_db() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = True
            # Delete the activation token
            session.query(Token).filter(Token.user_id == user_id, Token.token_type == 'activation').delete()
            session.commit()

def update_user_password(user_id, new_password):
    with get_db() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.password = generate_password_hash(new_password, method='scrypt')
            session.commit()

def update_user_admin_status(user_id, is_admin):
    with get_db() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_admin = is_admin
            session.commit()