"""
tag.py

This module provides CRUD functions for the Tags table
"""

import sqlite3
import json

def get_tags():
    """Returns all tags"""
    with sqlite3.connect("./db.sqlite3") as conn:
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
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
        """
        SELECT * FROM Tags
        WHERE id = ?
        """, (tag_id,),
        )

        tag = db_cursor.fetchone()

        return dict(tag)

def create_tag(tag):
    """Creates a new tag"""
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
        """
        INSERT INTO Tags
        (label)
        VALUES (?)
        """,(
            tag["label"],
        ),
        )

        new_tag_id = db_cursor.lastrowid

        db_cursor.execute(
            """
            SELECT * FROM Tags
            WHERE id = ?
            """, (
                new_tag_id
            ),
        )

        new_tag = db_cursor.fetchone

        return dict(new_tag)
