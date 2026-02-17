import sqlite3
import json
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def create_post(post):
    """Adds post to the database

    Args:
        post (dict): Contains the content and metadata of the post being created

    Returns:
        json string: The newly created post
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            INSERT into Posts
                (user_id, category_id, title, publication_date, image_url, content, approved)
            VALUES
                (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                post["user_id"],
                post["category_id"],
                post["title"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                post.get("image_url", None),
                post["content"],
            ),
        )

        post_id = db_cursor.lastrowid

        db_cursor.execute(
            """
            SELECT *
            FROM Posts p
            WHERE p.id = ?
            """,
            (post_id,),
        )

        new_post = dict(db_cursor.fetchone())

        return json.dumps(new_post)


def get_all_posts():
    """Reader feed: approved posts only, published in the past only, newest first"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                p.id,
                p.title,
                p.publication_date,
                u.first_name || ' ' || u.last_name AS author,
                c.label AS category
            FROM Posts p
            JOIN Users u
                ON u.id = p.user_id
            JOIN Categories c
                ON c.id = p.category_id
            WHERE p.approved = 1
              AND date(p.publication_date) <= date('now')
            ORDER BY date(p.publication_date) DESC
            """
        )

        return json.dumps(
            [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "publication_date": row["publication_date"],
                    "author": row["author"],
                    "category": row["category"],
                }
                for row in db_cursor.fetchall()
            ]
        )


def get_user_posts(user_id):
    """Retrieves a users posts from the database

    Args:
        user_id (int): The id of the user

    Returns:
        json string: A list of all the user's posts
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT 
                p.id, 
                p.user_id, 
                p.category_id, 
                p.title, 
                p.publication_date, 
                u.first_name,
                u.last_name,
                u.username, 
                c.label
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.user_id = ?
            ORDER BY p.publication_date DESC
            """,
            (user_id,),
        )

        user_posts = db_cursor.fetchall()

        posts = []
        for row in user_posts:
            user = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "username": row["username"],
            }

            category = {"label": row["label"]}

            post = {
                "id": row["id"],
                "user": user,
                "category": category,
                "title": row["title"],
                "publication_date": row["publication_date"],
            }

            posts.append(post)

        return json.dumps(posts)


def get_post_by_id(id):
    """Existing function kept for backwards-compatibility (team may be using it)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT *
            FROM Posts p
            WHERE p.id = ?
            """,
            (id,),
        )

        post = db_cursor.fetchone()

        # If not found, return empty object (handler can optionally return 404)
        if post is None:
            return json.dumps({})

        return json.dumps(dict(post))


def get_post_details(post_id):
    """Reader detail: approved + published in the past, plus author display name."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                p.id,
                p.title,
                p.image_url,
                p.content,
                p.publication_date,
                u.first_name || ' ' || u.last_name AS author_display_name
            FROM Posts p
            JOIN Users u ON u.id = p.user_id
            WHERE p.id = ?
              AND p.approved = 1
              AND date(p.publication_date) <= date('now')
            """,
            (post_id,),
        )

        row = db_cursor.fetchone()

        if row is None:
            return json.dumps({})

        return json.dumps(
            {
                "id": row["id"],
                "title": row["title"],
                "image_url": row["image_url"],
                "content": row["content"],
                "publication_date": row["publication_date"],
                "author_display_name": row["author_display_name"],
            }
        )


def update_post(post):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            UPDATE Posts
            SET 
                category_id = ?,
                title = ?,
                content = ?,
                image_url = ?
            WHERE id = ?
            """,
            (
                post["category_id"],
                post["title"],
                post["content"],
                post["image_url"],
                post["id"],
            ),
        )

        db_cursor.execute(
            """
            SELECT *
            FROM Posts
            WHERE id = ?
            """,
            (post["id"],),
        )

        updated_post = db_cursor.fetchone()

        if updated_post is None:
            return json.dumps({})

        return json.dumps(updated_post)

def get_unapproved_posts():
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT *
            FROM Posts p
            JOIN Users u
            ON p.user_id = u.id
            JOIN Categories c
            ON p.category_id = c.id
            WHERE approved = 0
            ORDER BY p.publication_date DESC
            """
        )

        posts = db_cursor.fetchall()

        unapproved_posts = []

        for row in posts:
            user = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "username" : row["username"]
            }

            category = {
                "label": row["label"]
            }

            post = {
                "id": row["id"],
                "user": user,
                "category": category,
                "title": row["title"],
                "publication_date" : row["publication_date"],
                "image_url": row["image_url"],
                "content": row["content"],
                "approved": row["approved"]
            }

            unapproved_posts.append(post)

        return json.dumps(unapproved_posts)
    
def approve_post(post_id):
    with sqlite3.connect("./db.sqlite3") as conn:
        db_cursor = conn.cursor()
        db_cursor.execute(
            "UPDATE POSTS SET approved = 1 WHERE id = ?",
            (post_id,)
        )
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
        db_cursor.execute("SELECT * FROM Posts WHERE id = ?", (post_id,))
        return json.dumps(dict(db_cursor.fetchone()))
    
