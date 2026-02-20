import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def create_comment(comment):
    """
    Creates a comment.

    Expects comment dict with:
      - post_id (int)
      - user_id (int)  -> maps to Comments.author_id
      - subject (str)
      - content (str)

    Automatically sets created_on.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            INSERT INTO Comments (post_id, author_id, subject, content, created_on)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                comment["post_id"],
                comment["user_id"],  # map user_id -> author_id
                comment.get("subject", ""),
                comment["content"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        new_id = db_cursor.lastrowid

        db_cursor.execute(
            """
            SELECT
                c.id,
                c.post_id,
                c.author_id,
                c.subject,
                c.content,
                c.created_on,
                u.first_name || ' ' || u.last_name AS author
            FROM Comments c
            JOIN Users u ON u.id = c.author_id
            WHERE c.id = ?
            """,
            (new_id,),
        )

        row = db_cursor.fetchone()
        return json.dumps(dict(row)) if row else json.dumps({})


def get_comments_by_post_id(post_id):
    """
    Returns all comments for a post, newest first.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                c.id,
                c.post_id,
                c.author_id,
                c.subject,
                c.content,
                c.created_on,
                u.first_name || ' ' || u.last_name AS author
            FROM Comments c
            JOIN Users u ON u.id = c.author_id
            WHERE c.post_id = ?
            ORDER BY datetime(c.created_on) DESC
            """,
            (post_id,),
        )

        return json.dumps([dict(row) for row in db_cursor.fetchall()])
