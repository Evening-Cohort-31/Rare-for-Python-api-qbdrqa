import sqlite3
import json
from datetime import datetime


def create_post(post):
    """Adds post to the database

    Args:
        post (dict): Contains the content and metadata of the post being created

    Returns:
        json string: The newly created post
    """


def get_all_posts():
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
        INSERT into Posts (user_id, category_id, title, publication_date, image_url, content, approved) values (?,?,?,?,?,?,1)
                          """,
            (
                post["user_id"],
                post["category_id"],
                post["title"],
                datetime.now(),
                post["image_url"],
                post["content"],
            ),
        )

        post_id = db_cursor.lastrowid

        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
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


def get_user_posts(user_id):
    """Retrieves a users posts from the database

    Args:
        user_id (int): The id of the user

    Returns:
        json string: A list of all the user's posts
    """
    with sqlite3.connect("./db.sqlite3") as conn:
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
            JOIN Users u
            ON p.user_id = u.id
            JOIN Categories c
            ON p.category_id = c.id
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
                "username": row["username"]
            }

            category = {
                "label": row["label"]
            }

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
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
            *
            FROM Posts p
            WHERE p.id = ?
            """,
            (id,),
        )

        post = db_cursor.fetchone()

        return json.dumps(dict(post))

def update_post(post):
    with sqlite3.connect("./db.sqlite3") as conn:
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
            )
        )

        db_cursor.execute(
        """
        SELECT *
        FROM Posts
        WHERE id = ?
        """,
        (post["id"],)
        )

        updated_post = dict(db_cursor.fetchone())

        return json.dumps(updated_post)
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

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "publication_date": row["publication_date"],
                "author": row["author"],
                "category": row["category"],
            }
            for row in db_cursor.fetchall()
        ]
