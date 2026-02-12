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
            SELECT * FROM Posts p
            WHERE p.user_id = ?
            ORDERBY p.publication_date DESC
            """,
            (
                user_id,
            ),
        )

        user_posts = db_cursor.fetchall()

        return json.dumps([dict(row) for row in user_posts])    