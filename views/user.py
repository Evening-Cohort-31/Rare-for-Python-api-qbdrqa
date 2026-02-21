import sqlite3
import json
from datetime import datetime
from pathlib import Path
from itertools import chain

from .post import get_user_posts


DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"


def login_user(user):
    """Checks for the user in the database

    Args:
        user (dict): Contains the username and password of the user trying to login

    Returns:
        json string: If the user was found will return valid boolean of True and the user's id as the token
                     If the user was not found will return valid boolean False
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            select id, username, active
            from Users
            where username = ?
            and password = ?
        """,
            (user["username"], user["password"]),
        )

        user_from_db = db_cursor.fetchone()

        if user_from_db is not None and user_from_db["active"]:
            response = {"valid": True, "token": user_from_db["id"]}
        else:
            response = {"valid": False}

        return json.dumps(response)


def create_user(user):
    """Adds a user to the database when they register

    Args:
        user (dictionary): The dictionary passed to the register post request

    Returns:
        json string: Contains the token of the newly created user
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
        Insert into Users (first_name, last_name, username, email, password, bio, created_on, active, type) values (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
            (
                user["first_name"],
                user["last_name"],
                user["username"],
                user["email"],
                user["password"],
                user["bio"],
                datetime.now(),
                user["type"],
            ),
        )

        id = db_cursor.lastrowid

        return json.dumps({"token": id, "valid": True})


def list_users():
    """Returns a list of all users from the database

    Returns:
        json string: A list of all users
    """
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
        select
            u.id,
            u.first_name,
            u.last_name,
            u.username,
            u.email,
            u.password,
            u.bio,
            u.created_on,
            u.active,
            u.type,
            u.profile_image_url
        from Users u
        """
        )

        users = []
        dataset = db_cursor.fetchall()

        for row in dataset:
            user = {
                "id": row["id"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "username": row["username"],
                "email": row["email"],
                "password": row["password"],
                "bio": row["bio"],
                "created_on": row["created_on"],
                "active": row["active"],
                "type": row["type"],
                "is_staff": True if row["type"] == "admin" else False,
                "profile_image_url": row["profile_image_url"],
            }
            users.append(user)

        return json.dumps(users)


def get_user(userId):
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
        SELECT * FROM Users u
        WHERE u.id = ?
        """,
            (userId,),
        )

        user = db_cursor.fetchone()

        return json.dumps(dict(user))


def update_user(user):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            UPDATE Users
            SET
                first_name = ?,
                last_name = ?,
                email = ?,
                bio = ?,
                username = ?,
                password = ?,
                profile_image_url = ?,
                active = ?,
                type = ?
            WHERE id = ?
            """,
            (
                user["first_name"],
                user["last_name"],
                user["email"],
                user["bio"],
                user["username"],
                user["password"],
                user["profile_image_url"],
                user["active"],
                user["type"],
                user["id"],
            ),
        )

        db_cursor.execute(
            """
            SELECT * FROM Users
            WHERE id = ?
            """,
            (user["id"],),
        )

        updated_user = db_cursor.fetchone()

        return json.dumps(dict(updated_user))


def get_user_home_page(userId):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT 
                u.id, 
                u.first_name, 
                u.last_name, 
                u.email, 
                u.bio, 
                u.username, 
                u.profile_image_url, 
                u.created_on, 
                u.type,
                json_group_array(
                    json_object(
                        'id', su.id,
                        'username', su.username,
                        'created_on', su.created_on
                    )
                ) AS subscriptions
            FROM Users u
            LEFT JOIN Subscriptions s
            ON s.follower_id = u.id
            LEFT JOIN Users su
            ON s.author_id = su.id 
            WHERE u.id = ?
            GROUP BY u.id
            """,
            (userId,),
        )

        row = db_cursor.fetchone()

        user = dict(row)

        # Parse the JSON string from SQLite to avoid double encoding
        user["subscriptions"] = json.loads(user["subscriptions"])

        subscribed_posts = [get_user_posts(int(s["id"])) for s in user["subscriptions"]]

        user['posts'] = json.loads(get_user_posts(userId))
        # Flatten the list of arrays into a single array
        user["subscribed_posts"] = list(
            chain.from_iterable([json.loads(post) for post in subscribed_posts])
        )

        return json.dumps(user)
