import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def create_comment(comment):
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
                comment["author_id"],
                comment.get("subject", ""),
                comment["content"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        comment_id = db_cursor.lastrowid

        db_cursor.execute(
            """
            SELECT
                c.id,
                c.post_id,
                c.subject,
                c.content,
                c.created_on,
                u.first_name || ' ' || u.last_name AS author_display_name
            FROM Comments c
            JOIN Users u ON u.id = c.author_id
            WHERE c.id = ?
            """,
            (comment_id,),
        )

        row = db_cursor.fetchone()
        return json.dumps(dict(row)) if row else json.dumps({})


def get_comments_by_post_id(post_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                c.id,
                c.post_id,
                c.subject,
                c.content,
                c.created_on,
                u.first_name || ' ' || u.last_name AS author_display_name
            FROM Comments c
            JOIN Users u ON u.id = c.author_id
            WHERE c.post_id = ?
            ORDER BY datetime(c.created_on) DESC
            """,
            (post_id,),
        )

        return json.dumps([dict(row) for row in db_cursor.fetchall()])


def get_comment_by_id(comment_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                c.id,
                c.post_id,
                c.subject,
                c.content,
                c.created_on,
                u.first_name || ' ' || u.last_name AS author_display_name,
                u.id AS author_id
            FROM Comments c
            JOIN Users u ON u.id = c.author_id
            WHERE c.id = ?
            """,
            (comment_id,),
        )

        row = db_cursor.fetchone()
        return json.dumps(dict(row)) if row else json.dumps({})


def update_comment(comment_id, comment):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            UPDATE Comments
            SET subject = ?, content = ?
            WHERE id = ?
            """,
            (
                comment.get("subject", ""),
                comment["content"],
                comment_id,
            ),
        )

        return get_comment_by_id(comment_id)


def delete_comment(comment_id):
    with sqlite3.connect(DB_PATH) as conn:
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            DELETE FROM Comments
            WHERE id = ?
            """,
            (comment_id,),
        )

    return True
