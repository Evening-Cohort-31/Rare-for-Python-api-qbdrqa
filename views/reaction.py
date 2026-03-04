"""
tag.py

This module provides CRUD functions for the Reactions table
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def create_reaction(reaction):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        try:
            db_cursor.execute(
                """
                INSERT INTO Reactions
                (label, emoji)
                VALUES (?, ?)
                """,
                (
                    reaction["label"],
                    reaction["emoji"],
                ),
            )

            reaction_id = db_cursor.lastrowid

            db_cursor.execute(
                """
                SELECT * FROM Reactions
                WHERE id = ?
                """,
                (reaction_id,),
            )

            new_reaction = dict(db_cursor.fetchone())

            return json.dumps(new_reaction)
        except sqlite3.IntegrityError:
            return json.dumps({"ok": False, "error": "This emoji already exists"})


def delete_reaction(reaction_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            DELETE FROM Reactions
            WHERE id = ?
            """,
            (reaction_id,),
        )

        return json.dumps({"deleted": True})


def update_reaction(reaction):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        try:
            db_cursor.execute(
                """
                UPDATE Reactions
                SET
                    label = ?,
                    emoji = ?
                WHERE id = ?
                """,
                (
                    reaction["label"],
                    reaction["emoji"],
                    reaction["id"],
                ),
            )

            db_cursor.execute(
                """
                SELECT * FROM Reactions
                WHERE id = ?
                """,
                (reaction["id"],),
            )

            updated_reaction = db_cursor.fetchone()

            return json.dumps(dict(updated_reaction))
        except sqlite3.IntegrityError:
            return json.dumps({"ok": False, "error": "This emoji already exists"})
