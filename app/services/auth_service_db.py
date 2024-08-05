import sqlite3
import os
import uuid
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import  redirect, url_for, flash
from flask_login import UserMixin, current_user

USER_DATABASE = None

def setup_database(config):
    global USER_DATABASE
    USER_DATABASE = config['USER_DATABASE_PATH']

def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')  # Assuming UTF-8 encoding
    if s:
        return datetime.fromisoformat(s)
    return None

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter('timestamp', convert_datetime)

def add_column_if_not_exists(db, table_name, column_name, column_definition):
    cur = db.execute(f"PRAGMA table_info({table_name})")
    columns = [row['name'] for row in cur.fetchall()]
    if column_name not in columns:
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

def init_db():
    if os.path.exists(USER_DATABASE):
        print("Database already exists.")
        return

    print("Creating new database.")

    # Ensure the directory for the database exists
    os.makedirs(os.path.dirname(USER_DATABASE), exist_ok=True)

    conn = sqlite3.connect(USER_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at timestamp NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            user_id TEXT NOT NULL,
            token TEXT NOT NULL,
            token_type TEXT NOT NULL,
            expires_at timestamp NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Add the is_admin column if it does not exist
    add_column_if_not_exists(cursor, 'users', 'is_admin', 'INTEGER NOT NULL DEFAULT 0')

    # Add the user_role column if it does not exist
    add_column_if_not_exists(cursor, 'users', 'user_role', 'TEXT')

    conn.commit()
    conn.close()
    print("Database initialized")

def get_db():
    if not os.path.exists(USER_DATABASE):
        print("Database does not exist. Initializing...")
        init_db()

    conn = sqlite3.connect(USER_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for better concurrency
    return conn

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

class User(UserMixin):
    def __init__(self, id, username, email, password, is_active, created_at, is_admin=False, user_role=None):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self._is_active = is_active
        self.created_at = created_at
        self._is_admin = is_admin
        self.user_role = user_role

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @property
    def is_admin(self):
        return self._is_admin

    @is_admin.setter
    def is_admin(self, value):
        self._is_admin = value

    def get_id(self):
        return self.id

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def save(self):
        with get_db() as db:
            db.execute('''
                INSERT INTO users (id, username, email, password, is_active, is_admin, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username=excluded.username,
                    email=excluded.email,
                    password=excluded.password,
                    is_active=excluded.is_active,
                    is_admin=excluded.is_admin,
                    created_at=excluded.created_at
            ''', (self.id, self.username, self.email, self.password, self._is_active, self._is_admin, self.created_at))

    def save(self):
        with get_db() as db:
            cursor = db.cursor()
            self.add_column_if_not_exists(cursor, 'users', 'user_role', 'TEXT')
            cursor.execute('''
                INSERT INTO users (id, username, email, password, is_active, is_admin, created_at, user_role)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username=excluded.username,
                    email=excluded.email,
                    password=excluded.password,
                    is_active=excluded.is_active,
                    is_admin=excluded.is_admin,
                    created_at=excluded.created_at,
                    user_role=excluded.user_role
            ''', (self.id, self.username, self.email, self.password, self._is_active, self._is_admin, self.created_at, self.user_role))
            db.commit()

    @classmethod
    def get_all_users(cls):
        with get_db() as db:
            cursor = db.cursor()
            cls.add_column_if_not_exists(cursor, 'users', 'user_role', 'TEXT')
            cur = cursor.execute('SELECT * FROM users')
            return [cls(**row) for row in cur.fetchall()]

    def update_role(self, role):
        self.user_role = role
        with get_db() as db:
            cursor = db.cursor()
            self.add_column_if_not_exists(cursor, 'users', 'user_role', 'TEXT')
            cursor.execute('UPDATE users SET user_role = ? WHERE id = ?', (role, self.id))
            db.commit()

    @staticmethod
    def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

    @classmethod
    def delete_user(cls, user_id):
        with get_db() as db:
            db.execute('DELETE FROM users WHERE id = ?', (user_id,))
            db.execute('DELETE FROM tokens WHERE user_id = ?', (user_id,))

    @classmethod
    def get(cls, user_id):
        with get_db() as db:
            cur = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cur.fetchone()
            if row:
                return cls(**row)

    @classmethod
    def get_by_email(cls, email):
        with get_db() as db:
            cur = db.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cur.fetchone()
            if row:
                return cls(**row)

    def update_activation(self):
        self.is_active = 1
        with get_db() as db:
            db.execute('UPDATE users SET is_active = ?, is_admin = ? WHERE id = ?', (self.is_active, self.is_admin, self.id))

    def update_password(self, hashed_password):
        self.password = hashed_password
        with get_db() as db:
            db.execute('UPDATE users SET password = ?, is_admin = ? WHERE id = ?', (hashed_password, self.is_admin, self.id))

    def update_admin_status(self, is_admin):
        self.is_admin = is_admin
        with get_db() as db:
            cursor = db.cursor()
            self.add_column_if_not_exists(cursor, 'users', 'is_admin', 'INTEGER NOT NULL DEFAULT 0')
            cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', (is_admin, self.id))
            db.commit()

    @staticmethod
    def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

    def delete(self):
        with get_db() as db:
            db.execute('DELETE FROM users WHERE id = ?', (self.id,))
            db.execute('DELETE FROM tokens WHERE user_id = ?', (self.id,))

    @classmethod
    def generate_token(cls, user_id, token_type):
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=20)
        with get_db() as db:
            db.execute('''
                INSERT INTO tokens (user_id, token, token_type, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, token, token_type, expires_at))
        return token

    @classmethod
    def get_token(cls, token, token_type):
        with get_db() as db:
            cur = db.execute('SELECT user_id, expires_at FROM tokens WHERE token = ? AND token_type = ?', (token, token_type))
            return cur.fetchone()

    @classmethod
    def delete_token(cls, token):
        with get_db() as db:
            db.execute('DELETE FROM tokens WHERE token = ?', (token,))
