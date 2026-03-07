"""
post.py

This module provides CRUD functions for the Posts table
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

from views.user import check_if_admin

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def _fetch_related_data_for_posts(db_cursor, post_ids):
    """Returns comments, tags, reactions, and reaction counts for the provided posts"""
    if not post_ids:
        return {}, {}, {}, {}

    placeholders = ",".join("?" * len(post_ids))

    db_cursor.execute(
        f"""
        SELECT pt.post_id, t.id, t.label
        FROM PostTags pt
        JOIN Tags t ON pt.tag_id = t.id
        WHERE pt.post_id IN ({placeholders})
        """,
        post_ids,
    )
    tags_by_post = {}
    for row in db_cursor.fetchall():
        tags_by_post.setdefault(row["post_id"], []).append(
            {"id": row["id"], "label": row["label"]}
        )

    db_cursor.execute(
        f"""
        SELECT 
            cm.post_id, cm.id, cm.subject, cm.content, cm.created_on,
            json_object(
                'id', u.id, 'first_name', u.first_name,
                'last_name', u.last_name, 'username', u.username
            ) as author
        FROM Comments cm
        JOIN Users u ON cm.author_id = u.id
        WHERE cm.post_id IN ({placeholders})
        """,
        post_ids,
    )
    comments_by_post = {}
    for row in db_cursor.fetchall():
        comments_by_post.setdefault(row["post_id"], []).append(
            {
                "id": row["id"],
                "subject": row["subject"] or "",
                "content": row["content"],
                "created_on": row["created_on"],
                "author": json.loads(row["author"]),
            }
        )

    db_cursor.execute(
        f"""
        SELECT 
            pr.post_id, pr.id,
            json_object(
                'id', u.id, 'first_name', u.first_name,
                'last_name', u.last_name, 'username', u.username
            ) as user,
            json_object(
                'id', r.id, 'label', r.label, 'emoji', r.emoji
            ) as reaction
        FROM PostReactions pr
        JOIN Users u ON pr.user_id = u.id
        JOIN Reactions r ON pr.reaction_id = r.id
        WHERE pr.post_id IN ({placeholders})
        """,
        post_ids,
    )
    reactions_by_post = {}
    for row in db_cursor.fetchall():
        reactions_by_post.setdefault(row["post_id"], []).append(
            {
                "id": row["id"],
                "user": json.loads(row["user"]),
                "reaction": json.loads(row["reaction"]),
            }
        )

    # Query for reaction counts (all reactions with counts for each post)
    # Create a UNION ALL clause for each post_id (SQLite compatible)
    union_clauses = " UNION ALL ".join(
        f"SELECT {post_id} as post_id" for post_id in post_ids
    )
    db_cursor.execute(
        f"""
        SELECT 
            posts.post_id,
            r.id as reaction_id,
            r.label,
            r.emoji,
            COUNT(pr.id) as count
        FROM ({union_clauses}) AS posts
        CROSS JOIN Reactions r
        LEFT JOIN PostReactions pr 
            ON pr.post_id = posts.post_id 
            AND pr.reaction_id = r.id
        GROUP BY posts.post_id, r.id
        """
    )
    reaction_counts_by_post = {}
    for row in db_cursor.fetchall():
        reaction_counts_by_post.setdefault(row["post_id"], []).append(
            {
                "reaction_id": row["reaction_id"],
                "label": row["label"],
                "emoji": row["emoji"],
                "count": row["count"],
            }
        )

    return tags_by_post, comments_by_post, reactions_by_post, reaction_counts_by_post


def _attach_related_data(
    posts, tags_by_post, comments_by_post, reactions_by_post, reaction_counts_by_post
):
    """Attaches the provided tags, comments, reactions, and reaction counts to their related Posts entries"""
    for post in posts:
        if isinstance(post.get("user"), str):
            post["user"] = json.loads(post["user"])
        if isinstance(post.get("category"), str):
            post["category"] = json.loads(post["category"])

        post["tags"] = tags_by_post.get(post["id"], [])
        post["comments"] = comments_by_post.get(post["id"], [])
        post["reactions"] = reactions_by_post.get(post["id"], [])
        post["reaction_counts"] = reaction_counts_by_post.get(post["id"], [])

    return posts


def update_post_tags(post_id, tag_ids, db_cursor=None):
    """Updates the PostTags table for the provided post"""

    def _update_tags(cursor):
        cursor.execute(
            """
            DELETE FROM PostTags WHERE post_id = ?
            """,
            (post_id,),
        )

        if tag_ids:
            cursor.executemany(
                """
                INSERT INTO PostTags (post_id, tag_id)
                VALUES (?, ?)
                """,
                [(post_id, tag_id) for tag_id in tag_ids],
            )

    if db_cursor:
        _update_tags(db_cursor)
    else:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            _update_tags(cursor)


def create_post(post):
    """Creates a new post"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        blob_data = None
        if "image" in post and post["image"]:
            # Check if it's already binary data (from formData) or a file path
            if isinstance(post["image"], bytes):
                blob_data = post["image"]
            else:
                # Fallback for file path (backwards compatibility)
                with open(post["image"], "rb") as file:
                    blob_data = file.read()

        db_cursor.execute(
            """
            INSERT into Posts
            (
                user_id, 
                category_id, 
                title, 
                publication_date, 
                image, 
                content, 
                status, 
                updated_at
            )
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post["user_id"],
                post["category_id"],
                post["title"],
                None,  # publication_date set when approved
                blob_data,
                post["content"],
                post.get("status", "draft"),  # default to 'draft'
                datetime.now(),
            ),
        )

        post_id = db_cursor.lastrowid

        if "tags" in post:
            tag_ids = post["tags"]
            if isinstance(tag_ids, str):
                tag_ids = json.loads(tag_ids)
            if tag_ids and isinstance(tag_ids[0], dict):
                tag_ids = [t["id"] for t in tag_ids]
            tag_ids = [int(t) for t in tag_ids]
            update_post_tags(post_id, tag_ids, db_cursor)

        new_post = get_post_by_id(post_id, post["user_id"], db_cursor)

        return new_post


def get_all_posts():
    """Returns all approved posts of active users"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                p.id, p.title, p.content, p.status,
                p.publication_date, p.updated_at,
                p.admin_comments,
                json_object(
                    'id', u.id, 'first_name', u.first_name,
                    'last_name', u.last_name, 'username', u.username
                ) as user,
                json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.status = 'approved'
              AND date(p.publication_date) <= date('now')
              AND u.active = 1
            ORDER BY date(p.publication_date) DESC
            """
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        tags, comments, reactions, reaction_counts = _fetch_related_data_for_posts(
            db_cursor, post_ids
        )
        posts = _attach_related_data(posts, tags, comments, reactions, reaction_counts)

        return json.dumps(posts)


def get_user_posts(user_id, own_posts=False):
    """Returns posts for the provided user. If own_posts=True, returns all posts regardless of status. Otherwise returns only approved posts."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        if not own_posts:
            # Viewing someone else's profile - only show approved posts from active users
            db_cursor.execute(
                """
                SELECT
                    p.id, p.title, p.content, p.status,
                    p.publication_date, p.updated_at,
                    p.admin_comments,
                    json_object(
                        'id', u.id, 'first_name', u.first_name,
                        'last_name', u.last_name, 'username', u.username
                    ) as user,
                    json_object('id', c.id, 'label', c.label) as category
                FROM Posts p
                JOIN Users u ON p.user_id = u.id
                JOIN Categories c ON p.category_id = c.id
                WHERE p.user_id = ?
                AND p.status = 'approved'
                AND u.active = 1
                ORDER BY date(p.publication_date) DESC
                """,
                (user_id,),
            )
        else:
            # "My Posts" - show all posts regardless of status
            db_cursor.execute(
                """
                SELECT
                    p.id, p.title, p.content, p.status,
                    p.publication_date, p.updated_at,
                    p.admin_comments,
                    json_object(
                        'id', u.id, 'first_name', u.first_name,
                        'last_name', u.last_name, 'username', u.username
                    ) as user,
                    json_object('id', c.id, 'label', c.label) as category
                FROM Posts p
                JOIN Users u ON p.user_id = u.id
                JOIN Categories c ON p.category_id = c.id
                WHERE p.user_id = ?
                ORDER BY p.updated_at DESC
                """,
                (user_id,),
            )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        tags, comments, reactions, reaction_counts = _fetch_related_data_for_posts(
            db_cursor, post_ids
        )
        posts = _attach_related_data(posts, tags, comments, reactions, reaction_counts)

        return json.dumps(posts)


def get_post_by_id(post_id, user_id, cursor=None):
    """Returns the specified post. If cursor is provided (internal call), returns post regardless of status. Otherwise, returns post only if user owns it OR it's approved."""

    execution = """
    SELECT
        p.id, p.title, p.content, p.status, p.user_id,
        p.publication_date, p.updated_at,
        p.admin_comments,
        json_object(
            'id', u.id, 'first_name', u.first_name,
            'last_name', u.last_name, 'username', u.username
        ) as user,
        json_object('id', c.id, 'label', c.label) as category
    FROM Posts p
    JOIN Users u ON p.user_id = u.id
    JOIN Categories c ON p.category_id = c.id
    WHERE p.id = ?
    AND u.active = 1
    """

    if cursor is not None:
        db_cursor = cursor
        db_cursor.execute(execution, (post_id,))
    else:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            db_cursor = conn.cursor()

            db_cursor.execute(
                execution,
                (post_id,),
            )

    row = db_cursor.fetchone()

    if not row:
        return json.dumps(None)

    # If cursor provided (internal call), return post regardless of status
    # Otherwise, only return if user owns it OR is admin OR post is approved
    if cursor is None:
        post_user_id = row["user_id"]
        post_status = row["status"]
        is_admin = check_if_admin(user_id, db_cursor)

        # If no user_id provided (anonymous) OR (user doesn't own the post AND not admin), only return if approved
        if (
            user_id is None or (post_user_id != user_id and not is_admin)
        ) and post_status != "approved":
            return json.dumps(None)

    posts = [dict(row)]
    tags, comments, reactions, reaction_counts = _fetch_related_data_for_posts(
        db_cursor, [post_id]
    )
    posts = _attach_related_data(posts, tags, comments, reactions, reaction_counts)

    return json.dumps(posts[0])


def get_post_details(post_id):
    """Returns an approved posts with user info"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                p.id,
                p.title,
                p.content,
                p.publication_date,
                p.updated_at,
                p.admin_comments,
                p.status,
                u.first_name || ' ' || u.last_name AS author_display_name
            FROM Posts p
            JOIN Users u ON u.id = p.user_id
            WHERE p.id = ?
              AND p.status = 'approved'
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
                "content": row["content"],
                "publication_date": row["publication_date"],
                "author_display_name": row["author_display_name"],
            }
        )


def update_post(post):
    """Updates a post"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        category_id = post.get("category_id")
        if category_id is None and isinstance(post.get("category"), dict):
            category_id = post["category"].get("id")

        # Check if a new image is being provided
        has_new_image = "image" in post and post["image"]
        blob_data = None

        # Check if status is being updated and is not "approved"
        update_status = "status" in post and post["status"] != "approved"

        if has_new_image:
            if isinstance(post["image"], bytes):
                blob_data = post["image"]

        # Build UPDATE query conditionally based on whether image and/or status is provided
        if has_new_image and update_status:
            db_cursor.execute(
                """
                UPDATE Posts
                SET 
                    category_id = ?,
                    title = ?,
                    content = ?,
                    image = ?,
                    status = ?,
                    publication_date = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    category_id,
                    post["title"],
                    post["content"],
                    blob_data,
                    post["status"],
                    datetime.now(),
                    post["id"],
                ),
            )
        elif has_new_image:
            db_cursor.execute(
                """
                UPDATE Posts
                SET 
                    category_id = ?,
                    title = ?,
                    content = ?,
                    image = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    category_id,
                    post["title"],
                    post["content"],
                    blob_data,
                    datetime.now(),
                    post["id"],
                ),
            )
        elif update_status:
            db_cursor.execute(
                """
                UPDATE Posts
                SET 
                    category_id = ?,
                    title = ?,
                    content = ?,
                    status = ?,
                    publication_date = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    category_id,
                    post["title"],
                    post["content"],
                    post["status"],
                    datetime.now(),
                    post["id"],
                ),
            )
        else:
            # Don't update image, status, or publication_date
            db_cursor.execute(
                """
                UPDATE Posts
                SET 
                    category_id = ?,
                    title = ?,
                    content = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    category_id,
                    post["title"],
                    post["content"],
                    datetime.now(),
                    post["id"],
                ),
            )

        if "tags" in post:
            tag_ids = post["tags"]
            if isinstance(tag_ids, str):
                tag_ids = json.loads(tag_ids)
            if tag_ids and isinstance(tag_ids[0], dict):
                tag_ids = [t["id"] for t in tag_ids]
            tag_ids = [int(t) for t in tag_ids]
            update_post_tags(post["id"], tag_ids, db_cursor)

        # Get user_id from the database
        db_cursor.execute(
            """
            SELECT user_id FROM Posts WHERE id = ?
            """,
            (post["id"],),
        )
        row = db_cursor.fetchone()
        user_id = row["user_id"] if row else None

        return get_post_by_id(post["id"], user_id, db_cursor)


def get_post_title(post_id):
    """Returns the title of the provided post"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
        db_cursor.execute(
            """
            SELECT id, title FROM Posts WHERE id = ?
            """,
            (post_id,),
        )
        row = db_cursor.fetchone()
        return json.dumps(dict(row)) if row else json.dumps({})


def get_unapproved_posts():
    """Returns all unapproved posts"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                p.id, p.title, p.content, p.status,
                p.publication_date, p.updated_at,
                json_object(
                    'id', u.id, 'first_name', u.first_name,
                    'last_name', u.last_name, 'username', u.username
                ) as user,
                json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.status = 'submitted'
              AND u.active = 1
            ORDER BY p.submitted_at DESC
            """
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        tags, comments, reactions, reaction_counts = _fetch_related_data_for_posts(
            db_cursor, post_ids
        )
        posts = _attach_related_data(posts, tags, comments, reactions, reaction_counts)

        return json.dumps(posts)


def submit_post(post_id):
    """Submits a post for review"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT user_id FROM Posts p
            WHERE p.id = ?
            """,
            (post_id,),
        )

        row = dict(db_cursor.fetchone())

        user_id = row["user_id"]

        is_admin = check_if_admin(user_id, db_cursor)

        if is_admin:
            return approve_post(post_id, user_id)

        db_cursor.execute(
            """
            UPDATE Posts 
            SET status = ?, submitted_at = ?, updated_at = ? 
            WHERE id = ?
            """,
            (
                "submitted",
                datetime.now(),
                datetime.now(),
                post_id,
            ),
        )

        return get_post_by_id(post_id, user_id, db_cursor)


def approve_post(post_id, reviewer_id, cursor=None):
    """Approves a post for publication"""

    if cursor:
        db_cursor = cursor

    else:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            db_cursor = conn.cursor()
            db_cursor.execute(
                """
                UPDATE Posts 
                SET status = ?, publication_date = ?, reviewed_at = ?, reviewer_id = ?, updated_at = ? 
                WHERE id = ?
                """,
                (
                    "approved",
                    datetime.now(),
                    datetime.now(),
                    reviewer_id,
                    datetime.now(),
                    post_id,
                ),
            )

            db_cursor.execute(
                """
                SELECT user_id FROM Posts
                WHERE id = ?
                """,
                (post_id,),
            )

            row = dict(db_cursor.fetchone())
            user_id = row["user_id"]

            return get_post_by_id(post_id, user_id, db_cursor)


def reject_post(post_id, reviewer_id, admin_comments=None):
    """Rejects a post and kicks it back for edits"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
        db_cursor.execute(
            """
            UPDATE Posts 
            SET status = ?, reviewed_at = ?, reviewer_id = ?, admin_comments = ?, updated_at = ? 
            WHERE id = ?
            """,
            (
                "rejected",
                datetime.now(),
                reviewer_id,
                admin_comments,
                datetime.now(),
                post_id,
            ),
        )

        db_cursor.execute(
            """
            SELECT user_id FROM Posts
            WHERE id = ?
            """,
            (post_id,),
        )

        row = dict(db_cursor.fetchone())
        user_id = row["user_id"]

        return get_post_by_id(post_id, user_id, db_cursor)


def get_posts_by_tag_id(tag_id):
    """Returns all approved posts with the provided tag"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                p.id, p.title, p.content, p.status,
                p.publication_date, p.updated_at,
                json_object(
                    'id', u.id, 'first_name', u.first_name,
                    'last_name', u.last_name, 'username', u.username
                ) as user,
                json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            JOIN PostTags pt ON pt.post_id = p.id
            WHERE p.status = 'approved'
              AND date(p.publication_date) <= date('now')
              AND pt.tag_id = ?
            ORDER BY date(p.publication_date) DESC
            """,
            (tag_id,),
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        # Fetch and attach related data
        tags, comments, reactions, reaction_counts = _fetch_related_data_for_posts(
            db_cursor, post_ids
        )
        posts = _attach_related_data(posts, tags, comments, reactions, reaction_counts)

        return json.dumps(posts)


def search_posts_by_title(search_term):
    """Returns any posts with the provided term in it's title"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
            p.id, p.title, p.content, p.status,
            p.publication_date, p.updated_at,
            json_object(
                'id', u.id, 'first_name', u.first_name,
                'last_name', u.last_name, 'username', u.username
            ) as user,
            json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u 
            ON u.id = p.user_id
            JOIN Categories c
            ON c.id = p.category_id
            WHERE p.title LIKE ?
            AND p.status = 'approved'
            ORDER BY p.publication_date DESC
            """,
            (f"%{search_term}%",),
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        # Fetch and attach related data
        tags, comments, reactions, reaction_counts = _fetch_related_data_for_posts(
            db_cursor, post_ids
        )
        posts = _attach_related_data(posts, tags, comments, reactions, reaction_counts)

        return json.dumps(posts)


def delete_post(post_id):
    """Deletes the specified post"""
    with sqlite3.connect(DB_PATH) as conn:
        db_cursor = conn.cursor()
        db_cursor.execute("DELETE FROM PostTags WHERE post_id = ?", (post_id,))
        db_cursor.execute("DELETE FROM Comments WHERE post_id = ?", (post_id,))
        db_cursor.execute("DELETE FROM Posts WHERE id = ?", (post_id,))
        return json.dumps({"deleted": True})


def add_reaction(post_id, user_id, reaction_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
        db_cursor.execute(
            """
            INSERT INTO PostReactions (user_id, reaction_id, post_id)
            VALUES (?, ?, ?)
            """,
            (user_id, reaction_id, post_id),
        )
        return json.dumps({"id": db_cursor.lastrowid})


def remove_reaction(post_reaction_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
        db_cursor.execute(
            """
            DELETE FROM PostReactions
            WHERE id = ?
            """,
            (post_reaction_id,),
        )

        return json.dumps({"deleted": True})


def get_reactions():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT * FROM Reactions
            """
        )

        reactions = db_cursor.fetchall()

        return json.dumps([dict(row) for row in reactions])


def get_subscribed_posts(user_id):
    """ "Returns a list of all approved posts of users the provided user is subscribed to."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT s.author_id FROM
            Subscriptions s
            WHERE s.follower_id = ?
            """,
            (user_id,),
        )

        subscribed_users = [row["author_id"] for row in db_cursor.fetchall()]

        if not subscribed_users:
            return json.dumps([])

        placeholders = ",".join("?" * len(subscribed_users))

        db_cursor.execute(
            f"""
            SELECT
                p.id, p.title, p.content, p.status,
                p.publication_date, p.updated_at,
                json_object(
                    'id', u.id, 'first_name', u.first_name,
                    'last_name', u.last_name, 'username', u.username
                ) as user,
                json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.user_id IN ({placeholders})
            AND p.status = 'approved'
            ORDER BY date(p.publication_date) DESC
            """,
            subscribed_users,
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        tags, comments, reactions, reaction_counts = _fetch_related_data_for_posts(
            db_cursor, post_ids
        )
        posts = _attach_related_data(posts, tags, comments, reactions, reaction_counts)

        return json.dumps(posts)


def get_post_header_image(post_id):
    """Returns only the profile image blob"""
    with sqlite3.connect(DB_PATH) as conn:
        db_cursor = conn.cursor()
        db_cursor.execute("SELECT image FROM Posts WHERE id = ?", (post_id,))
        result = db_cursor.fetchone()
        return result[0] if result and result[0] else None


def get_posts_by_category_id(category_id):
    """Return all posts with the given category"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                p.id, p.title, p.content, p.status,
                p.publication_date, p.updated_at,
                json_object(
                    'id', u.id, 'first_name', u.first_name,
                    'last_name', u.last_name, 'username', u.username
                ) as user,
                json_object('id', c.id, 'label', c.label) as category
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.status = 'approved'
              AND date(p.publication_date) <= date('now')
              AND c.id = ?
            ORDER BY date(p.publication_date) DESC

            """,
            (category_id,),
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        # Fetch and attach related data
        tags, comments, reactions, reaction_counts = _fetch_related_data_for_posts(
            db_cursor, post_ids
        )
        posts = _attach_related_data(posts, tags, comments, reactions, reaction_counts)

        return json.dumps(posts)
