"""
category.py

This module provides CRUD functions for the Categories Table
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def get_all_categories():
    """Returns a list of all Categories"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT * FROM Categories
            ORDER BY label
            """,
        )

        categories = db_cursor.fetchall()

        return json.dumps([dict(row) for row in categories])


def get_category_by_id(category_id):
    """Returns the Category with the provided id"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT * FROM Categories
            WHERE id = ?
            """,
            (category_id,),
        )

        category = db_cursor.fetchone()

        return json.dumps(dict(category)) if category else json.dumps({})


def create_category(category):
    """Creates a new category"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            INSERT INTO Categories
            (label)
            VALUES (?) 
            """,
            (category["label"],),
        )

        category_id = db_cursor.lastrowid

        db_cursor.execute(
            """
            SELECT * FROM Categories
            WHERE id = ?
            """,
            (category_id,),
        )

        category = db_cursor.fetchone()

        return json.dumps(dict(category)) if category else json.dumps({})


def update_category(category_id, category):
    """Updates the category with the provided id"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            UPDATE Categories
            SET label = ?
            WHERE id = ?
            """,
            (category["label"], category_id),
        )

        db_cursor.execute(
            """
            SELECT * FROM Categories
            WHERE id = ?
            """,
            (category_id,),
        )

        category = db_cursor.fetchone()

        return json.dumps(dict(category)) if category else json.dumps({})


def delete_category(category_id):
    """Deletes the category with the provided id"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            DELETE FROM Categories
            WHERE id = ?
            """,
            (category_id,),
        )

        deleted_count = db_cursor.rowcount

        if deleted_count == 0:
            return False

        return True
