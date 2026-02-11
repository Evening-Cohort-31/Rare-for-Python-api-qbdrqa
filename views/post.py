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

        db_cursor.execute("""
        INSERT into Posts (user_id, category, title, publication_date, image_url, content, approved) values (?,?,?,?,?,?,1)
                          """, (
                              post['user_id'],
                              post['category'],
                              post['title'],
                              datetime.now(),
                              post['image_url'],
                              post['content'],
                          ))
        
        post_id = db_cursor.lastrowid

        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
        db_cursor.execute(
        """
        SELECT *
        FROM Posts p
        WHERE p.id = ?
        """,
        (post_id)
        )

        new_post = dict(db_cursor.fetchone())
        

        return json.dumps(new_post)