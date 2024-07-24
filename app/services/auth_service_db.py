import sqlite3
import os
import uuid
from datetime import datetime, timedelta

USER_DATABASE = None

def setup_database(config):
    global USER_DATABASE
    USER_DATABASE = config.USER_DATABASE_PATH

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

def generate_token(user_id, token_type):
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=20)
    with get_db() as db:
        db.execute('''
            INSERT INTO tokens (user_id, token, token_type, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, token, token_type, expires_at))
    return token

def create_user(user_id, username, email, password, created_at):
    with get_db() as db:
        db.execute('''
            INSERT INTO users (id, username, email, password, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, email, password, created_at))

def get_user_by_email(email):
    with get_db() as db:
        cur = db.execute('SELECT id, username, password, is_active FROM users WHERE email = ?', (email,))
        return cur.fetchone()

def get_user_by_id(user_id):
    with get_db() as db:
        cur = db.execute('SELECT id, username, password, is_active FROM users WHERE id = ?', (user_id,))
        return cur.fetchone()

def update_user_activation(user_id):
    with get_db() as db:
        db.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))

def delete_user(user_id):
    with get_db() as db:
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.execute('DELETE FROM tokens WHERE user_id = ?', (user_id,))

def get_token(token, token_type):
    with get_db() as db:
        cur = db.execute('SELECT user_id, expires_at FROM tokens WHERE token = ? AND token_type = ?', (token, token_type))
        return cur.fetchone()

def delete_token(token):
    with get_db() as db:
        db.execute('DELETE FROM tokens WHERE token = ?', (token,))

def update_user_password(user_id, hashed_password):
    with get_db() as db:
        db.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
