import sqlite3
import json
from datetime import datetime


def _fetch_related_data_for_posts(db_cursor, post_ids):
    """Helper function to fetch tags, comments, and reactions for given post IDs
    
    Args:
        db_cursor: SQLite cursor
        post_ids: List of post IDs to fetch data for
        
    Returns:
        tuple: (tags_by_post, comments_by_post, reactions_by_post) dictionaries
    """
    if not post_ids:
        return {}, {}, {}
    
    placeholders = ','.join('?' * len(post_ids))
    
    # Fetch tags
    db_cursor.execute(f"""
        SELECT pt.post_id, t.id, t.label
        FROM PostTags pt
        JOIN Tags t ON pt.tag_id = t.id
        WHERE pt.post_id IN ({placeholders})
    """, post_ids)
    
    tags_by_post = {}
    for row in db_cursor.fetchall():
        tags_by_post.setdefault(row['post_id'], []).append({
            'id': row['id'], 'label': row['label']
        })
    
    # Fetch comments
    db_cursor.execute(f"""
        SELECT 
            cm.post_id, cm.id, cm.content,
            json_object(
                'id', u.id, 'first_name', u.first_name,
                'last_name', u.last_name, 'username', u.username
            ) as author
        FROM Comments cm
        JOIN Users u ON cm.author_id = u.id
        WHERE cm.post_id IN ({placeholders})
    """, post_ids)
    
    comments_by_post = {}
    for row in db_cursor.fetchall():
        comments_by_post.setdefault(row['post_id'], []).append({
            'id': row['id'],
            'content': row['content'],
            'author': json.loads(row['author'])
        })
    
    # Fetch reactions
    db_cursor.execute(f"""
        SELECT 
            pr.post_id, pr.id,
            json_object(
                'id', u.id, 'first_name', u.first_name,
                'last_name', u.last_name, 'username', u.username
            ) as user,
            json_object(
                'id', r.id, 'label', r.label, 'image_url', r.image_url
            ) as reaction
        FROM PostReactions pr
        JOIN Users u ON pr.user_id = u.id
        JOIN Reactions r ON pr.reaction_id = r.id
        WHERE pr.post_id IN ({placeholders})
    """, post_ids)
    
    reactions_by_post = {}
    for row in db_cursor.fetchall():
        reactions_by_post.setdefault(row['post_id'], []).append({
            'id': row['id'],
            'user': json.loads(row['user']),
            'reaction': json.loads(row['reaction'])
        })
    
    return tags_by_post, comments_by_post, reactions_by_post


def _attach_related_data(posts, tags_by_post, comments_by_post, reactions_by_post):
    """Helper to attach related data to post objects
    
    Args:
        posts: List of post dictionaries
        tags_by_post: Dictionary mapping post_id to tags
        comments_by_post: Dictionary mapping post_id to comments
        reactions_by_post: Dictionary mapping post_id to reactions
        
    Returns:
        list: Posts with related data attached
    """
    for post in posts:
        # Parse JSON fields
        if isinstance(post.get('user'), str):
            post['user'] = json.loads(post['user'])
        if isinstance(post.get('category'), str):
            post['category'] = json.loads(post['category'])
        
        # Attach related arrays
        post['tags'] = tags_by_post.get(post['id'], [])
        post['comments'] = comments_by_post.get(post['id'], [])
        post['reactions'] = reactions_by_post.get(post['id'], [])
    
    return posts


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


def get_all_posts():
    """Get all approved posts with full related data
    
    Returns:
        json string: List of all approved posts with tags, comments, and reactions
    """
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute("""
            SELECT
                p.id, p.title, p.content, p.approved,
                p.publication_date, p.image_url,
                json_object(
                    'id', u.id, 'first_name', u.first_name,
                    'last_name', u.last_name, 'username', u.username
                ) as user,
                json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.approved = 1
            AND date(p.publication_date) <= date('now')
            ORDER BY date(p.publication_date) DESC
        """)
        
        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p['id'] for p in posts]
        
        # Fetch and attach related data
        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, post_ids)
        posts = _attach_related_data(posts, tags, comments, reactions)
        
        return json.dumps(posts)


def get_user_posts(user_id):
    """Retrieves a user's posts from the database with full related data

    Args:
        user_id (int): The id of the user

    Returns:
        json string: A list of all the user's posts with tags, comments, and reactions
    """
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute("""
            SELECT
                p.id, p.title, p.content, p.approved,
                p.publication_date, p.image_url,
                json_object(
                    'id', u.id, 'first_name', u.first_name,
                    'last_name', u.last_name, 'username', u.username
                ) as user,
                json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.user_id = ?
            ORDER BY date(p.publication_date) DESC
        """, (user_id,))
        
        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p['id'] for p in posts]
        
        # Fetch and attach related data
        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, post_ids)
        posts = _attach_related_data(posts, tags, comments, reactions)
        
        return json.dumps(posts)


def get_post_by_id(post_id):
    """Get a single post with full related data
    
    Args:
        post_id (int): The id of the post
        
    Returns:
        json string: The post with tags, comments, and reactions, or None if not found
    """
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute("""
            SELECT
                p.id, p.title, p.content, p.approved,
                p.publication_date, p.image_url,
                json_object(
                    'id', u.id, 'first_name', u.first_name,
                    'last_name', u.last_name, 'username', u.username
                ) as user,
                json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.id = ?
        """, (post_id,))

        row = db_cursor.fetchone()
        if not row:
            return json.dumps(None)
        
        posts = [dict(row)]
        
        # Fetch and attach related data
        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, [post_id])
        posts = _attach_related_data(posts, tags, comments, reactions)
        
        return json.dumps(posts[0])


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

        updated_post = dict(db_cursor.fetchone())

        return json.dumps(updated_post)
