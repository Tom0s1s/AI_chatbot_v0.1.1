# db_handler.py
# Handles database requests and responses for cookies, user IDs, and behavior logging

import sqlite3 as sql

DB_NAME = "database.db"

# -----------------------------
# Database Initialization
# -----------------------------
def init_db():
    """Initialize the database with users and events tables."""
    conn = sql.connect(DB_NAME)
    print("Database initialized")

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            info TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            event_type TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

# -----------------------------
# User Management
# -----------------------------
def add_user(user_id, user_info=""):
    """Insert a new user if not already present."""
    conn = sql.connect(DB_NAME)
    try:
        conn.execute(
            'INSERT OR IGNORE INTO users (id, info) VALUES (?, ?)',
            (user_id, user_info)
        )
        conn.commit()
    finally:
        conn.close()

def get_user(user_id):
    """Retrieve user info by ID."""
    conn = sql.connect(DB_NAME)
    cursor = conn.execute(
        'SELECT info FROM users WHERE id = ?',
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    # Return the info field (string) or None if not found
    if row:
        return row[0]
    return None

# -----------------------------
# Event Logging
# -----------------------------
def add_event(user_id, event_type, content):
    """Log a user event (annotation, chat message, LLM response, etc.)."""
    conn = sql.connect(DB_NAME)
    try:
        conn.execute(
            'INSERT INTO events (user_id, event_type, content) VALUES (?, ?, ?)',
            (user_id, event_type, content)
        )
        conn.commit()
    finally:
        conn.close()

def get_events(user_id, limit=50):
    """Retrieve the most recent events for a user."""
    conn = sql.connect(DB_NAME)
    cursor = conn.execute(
        'SELECT event_type, content, timestamp FROM events WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

# -----------------------------
# Memory Prompt Builder
# -----------------------------
def build_memory_prompt(user_id, limit=50):
    """
    Build a memory prompt string from the user's recent chat history and events.
    Returns a single string suitable for feeding into an LLM.
    """
    events = get_events(user_id, limit=limit)
    # Reverse so oldest is first
    events = events[::-1]

    lines = []
    for event_type, content, timestamp in events:
        if event_type == "chat_user":
            lines.append(f"User: {content}")
        elif event_type == "chat_llm":
            lines.append(f"Assistant: {content}")
        elif event_type == "annotation":
            lines.append(f"[Annotation] {content}")
        else:
            lines.append(f"[{event_type}] {content}")

    return "\n".join(lines)


def list_users():
    """Return a list of all users as (id, info)."""
    conn = sql.connect(DB_NAME)
    cursor = conn.execute('SELECT id, info FROM users')
    rows = cursor.fetchall()
    conn.close()
    return rows


def clear_events(user_id):
    """Delete events for a given user_id."""
    conn = sql.connect(DB_NAME)
    try:
        conn.execute('DELETE FROM events WHERE user_id = ?', (user_id,))
        conn.commit()
    finally:
        conn.close()
