"""
tag.py

This module provides CRUD functions for the Tags table
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def get_tags():
    """Returns all tags"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
        SELECT * FROM Tags
        """
        )

        tags = db_cursor.fetchall()

        return json.dumps([dict(row) for row in tags])


def get_tag_by_id(tag_id):
    """Returns the specified tag"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
        SELECT * FROM Tags
        WHERE id = ?
        """,
            (tag_id,),
        )

        tag = db_cursor.fetchone()

        return json.dumps(dict(tag)) if tag else json.dumps({})


def create_tag(tag):
    """Creates a new tag"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
        INSERT INTO Tags
        (label)
        VALUES (?)
        """,
            (tag["label"],),
        )

        new_tag_id = db_cursor.lastrowid

        db_cursor.execute(
            """
            SELECT * FROM Tags
            WHERE id = ?
            """,
            (new_tag_id,),
        )

        new_tag = db_cursor.fetchone()

        return json.dumps(dict(new_tag)) if new_tag else json.dumps({})


def update_tag(tag_id, tag):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            UPDATE Tags
            SET label = ?
            WHERE id = ?
        """,
            (tag["label"], tag_id),
        )

        db_cursor.execute(
            """
            SELECT id, label
            FROM Tags
            WHERE id = ?
        """,
            (tag_id,),
        )

        row = db_cursor.fetchone()
        return json.dumps(dict(row)) if row else json.dumps({})


def delete_tag(tag_id):
    with sqlite3.connect(DB_PATH) as conn:
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            DELETE FROM Tags
            WHERE id = ?
        """,
            (tag_id,),
        )

        return db_cursor.rowcount > 0
