import os
import sqlite3
import pytest

from application.functions import db_handler


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_database.db"
    # Ensure the DB_NAME constant points to this temp file
    monkeypatch.setattr(db_handler, "DB_NAME", str(db_path))
    # Initialize a fresh database
    db_handler.init_db()
    yield db_handler
    # cleanup - remove file if present
    try:
        os.remove(str(db_path))
    except OSError:
        pass


def test_add_and_get_user(temp_db):
    db = temp_db
    user_id = "user-123"
    info = "Test User"

    # add and retrieve
    db.add_user(user_id, info)
    stored = db.get_user(user_id)
    assert stored == info

    # adding same user again should not raise and should leave value unchanged
    db.add_user(user_id, info)
    assert db.get_user(user_id) == info


def test_add_event_and_get_events(temp_db):
    db = temp_db
    user_id = "u-events"
    db.add_user(user_id, "")

    # add multiple events
    db.add_event(user_id, "chat_user", "Hello")
    db.add_event(user_id, "chat_llm", "Hi there")
    db.add_event(user_id, "annotation", "Note")

    events = db.get_events(user_id, limit=10)
    # get_events returns list of rows (event_type, content, timestamp)
    assert len(events) == 3
    types = [row[0] for row in events]
    contents = [row[1] for row in events]
    assert "chat_user" in types and "chat_llm" in types and "annotation" in types
    assert "Hello" in contents and "Hi there" in contents and "Note" in contents


def test_build_memory_prompt_and_clear_events(temp_db):
    db = temp_db
    user_id = "u-memory"
    db.add_user(user_id, "")

    db.add_event(user_id, "chat_user", "How are you?")
    db.add_event(user_id, "chat_llm", "I am fine")
    db.add_event(user_id, "annotation", "Important note")

    prompt = db.build_memory_prompt(user_id, limit=10)
    # should contain User:, Assistant:, and [Annotation]
    assert "User: How are you?" in prompt
    assert "Assistant: I am fine" in prompt
    assert "[Annotation] Important note" in prompt

    # clear events and ensure none remain
    db.clear_events(user_id)
    events_after = db.get_events(user_id)
    assert len(events_after) == 0


def test_list_users(temp_db):
    db = temp_db
    db.add_user("a", "A")
    db.add_user("b", "B")
    users = db.list_users()
    ids = [u[0] for u in users]
    assert "a" in ids and "b" in ids
