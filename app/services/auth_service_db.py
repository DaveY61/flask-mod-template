import sqlite3
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

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

class User(UserMixin):
    def __init__(self, id, username, email, password, is_active, created_at):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self._is_active = is_active
        self.created_at = created_at

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

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
                INSERT INTO users (id, username, email, password, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.id, self.username, self.email, self.password, self._is_active, self.created_at))

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
            db.execute('UPDATE users SET is_active = ? WHERE id = ?', (self.is_active, self.id))

    def update_password(self, hashed_password):
        self.password = hashed_password
        with get_db() as db:
            db.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, self.id))

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
