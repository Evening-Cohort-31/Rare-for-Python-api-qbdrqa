import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def _fetch_related_data_for_posts(db_cursor, post_ids):
    if not post_ids:
        return {}, {}, {}

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
                'id', r.id, 'label', r.label, 'image_url', r.image_url
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

    return tags_by_post, comments_by_post, reactions_by_post


def _attach_related_data(posts, tags_by_post, comments_by_post, reactions_by_post):
    for post in posts:
        if isinstance(post.get("user"), str):
            post["user"] = json.loads(post["user"])
        if isinstance(post.get("category"), str):
            post["category"] = json.loads(post["category"])

        post["tags"] = tags_by_post.get(post["id"], [])
        post["comments"] = comments_by_post.get(post["id"], [])
        post["reactions"] = reactions_by_post.get(post["id"], [])

    return posts


def update_post_tags(post_id, tag_ids, db_cursor=None):
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
                datetime.now(),
                post.get("image_url", ""),
                post["content"],
            ),
        )

        post_id = db_cursor.lastrowid

        if "tags" in post:
            tag_ids = post["tags"]
            if tag_ids and isinstance(tag_ids[0], dict):
                tag_ids = [t["id"] for t in tag_ids]
            update_post_tags(post_id, tag_ids, db_cursor)

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
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
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
            """
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, post_ids)
        posts = _attach_related_data(posts, tags, comments, reactions)

        return json.dumps(posts)


def get_user_posts(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
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
            AND p.approved = 1
            ORDER BY date(p.publication_date) DESC
            """,
            (user_id,),
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, post_ids)
        posts = _attach_related_data(posts, tags, comments, reactions)

        return json.dumps(posts)


def get_post_by_id(post_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
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
            """,
            (post_id,),
        )

        row = db_cursor.fetchone()
        if not row:
            return json.dumps(None)

        posts = [dict(row)]
        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, [post_id])
        posts = _attach_related_data(posts, tags, comments, reactions)

        return json.dumps(posts[0])


def get_post_details(post_id):
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

        category_id = post.get("category_id")
        if category_id is None and isinstance(post.get("category"), dict):
            category_id = post["category"].get("id")

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
                category_id,
                post["title"],
                post["content"],
                post.get("image_url", ""),
                post["id"],
            ),
        )

        if "tags" in post:
            tag_ids = post["tags"]
            if tag_ids and isinstance(tag_ids[0], dict):
                tag_ids = [t["id"] for t in tag_ids]
            update_post_tags(post["id"], tag_ids, db_cursor)

        return get_post_by_id(post["id"])


def get_post_title(post_id):
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
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
                p.id, p.title, p.content, p.approved,
                p.publication_date, p.image_url,
                u.first_name, u.last_name, u.username,
                c.id as category_id, c.label as category_label
            FROM Posts p
            JOIN Users u ON p.user_id = u.id
            JOIN Categories c ON p.category_id = c.id
            WHERE p.approved = 0
            ORDER BY p.publication_date DESC
            """
        )

        posts = []
        for row in db_cursor.fetchall():
            posts.append(
                {
                    "id": row["id"],
                    "user": {
                        "first_name": row["first_name"],
                        "last_name": row["last_name"],
                        "username": row["username"],
                    },
                    "category": {
                        "id": row["category_id"],
                        "label": row["category_label"],
                    },
                    "title": row["title"],
                    "publication_date": row["publication_date"],
                    "image_url": row["image_url"],
                    "content": row["content"],
                    "approved": row["approved"],
                }
            )

        return json.dumps(posts)


def approve_post(post_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
        db_cursor.execute("UPDATE POSTS SET approved = 1 WHERE id = ?", (post_id,))

        db_cursor.execute("SELECT * FROM Posts WHERE id = ?", (post_id,))
        return json.dumps(dict(db_cursor.fetchone()))


def get_posts_by_tag_id(tag_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
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
            JOIN PostTags pt ON pt.post_id = p.id
            WHERE p.approved = 1
              AND date(p.publication_date) <= date('now')
              AND pt.tag_id = ?
            ORDER BY date(p.publication_date) DESC
            """,
            (tag_id,),
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        # Fetch and attach related data
        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, post_ids)
        posts = _attach_related_data(posts, tags, comments, reactions)

        return json.dumps(posts)


def search_posts_by_title(search_term):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT
            p.id, p.title, p.content, p.approved,
            p.publication_date, p.image_url,
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
            AND p.approved = 1
            ORDER BY p.publication_date DESC
            """,
            (f"%{search_term}%",),
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        # Fetch and attach related data
        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, post_ids)
        posts = _attach_related_data(posts, tags, comments, reactions)

        return json.dumps(posts)


def delete_post(post_id):
    with sqlite3.connect(DB_PATH) as conn:
        db_cursor = conn.cursor()
        db_cursor.execute("DELETE FROM PostTags WHERE post_id = ?", (post_id,))
        db_cursor.execute("DELETE FROM Comments WHERE post_id = ?", (post_id,))
        db_cursor.execute("DELETE FROM Posts WHERE id = ?", (post_id,))
        return json.dumps({"deleted": True})


def get_subscribed_posts(user_id):
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
            WHERE p.user_id IN ({placeholders})
            AND p.approved = 1
            ORDER BY date(p.publication_date) DESC
            """,
            subscribed_users,
        )

        posts = [dict(row) for row in db_cursor.fetchall()]
        post_ids = [p["id"] for p in posts]

        tags, comments, reactions = _fetch_related_data_for_posts(db_cursor, post_ids)
        posts = _attach_related_data(posts, tags, comments, reactions)

        return json.dumps(posts)
