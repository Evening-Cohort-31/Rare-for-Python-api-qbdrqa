import sqlite3
import json
from datetime import datetime
from pathlib import Path

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

        blob_data = None
        if "profile_image" in user and user["profile_image"]:
            # Check if it's already binary data (from formData) or a file path
            if isinstance(user["profile_image"], bytes):
                blob_data = user["profile_image"]
            else:
                # Fallback for file path (backwards compatibility)
                with open(user["profile_image"], "rb") as file:
                    blob_data = file.read()

        db_cursor.execute(
            """
        Insert into Users (first_name, last_name, username, email, password, bio, profile_image, created_on, active, type, updated_at) values (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
            (
                user["first_name"],
                user["last_name"],
                user["username"],
                user["email"],
                user["password"],
                user["bio"],
                blob_data,
                datetime.now(),
                user["type"],
                datetime.now(),
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
            SELECT
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
                CASE
                    WHEN d.admin_id IS NOT NULL THEN
                        json_group_array(json_object(
                            'action', d.action,
                            'admin_id', d.admin_id,
                            'approver_one_id', d.approver_one_id
                        ))
                    ELSE NULL
                END AS demotion_queue
            FROM Users u
            LEFT JOIN DemotionQueue d
            ON d.admin_id = u.id
            GROUP BY u.id
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
            }

            if row["demotion_queue"] is not None:
                user["demotion_queue"] = json.loads(row["demotion_queue"])

            users.append(user)

        return json.dumps(users)


def get_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
        SELECT 
            u.*,
            COUNT(s.follower_id) AS subscriber_count
        FROM Users u
        LEFT JOIN Subscriptions s
        ON s.author_id = u.id
        WHERE u.id = ?
        GROUP BY u.id
        """,
            (user_id,),
        )

        user = dict(db_cursor.fetchone())

        if "profile_image" in user:
            del user["profile_image"]

        if "updated_at" in user:
            user["image_version"] = user["updated_at"]

        user["subscriptions"] = json.loads(
            __get_subscriptions__(user_id, db_cursor)["subscriptions"]
        )
        user["subscribers"] = json.loads(
            __get_subscribers__(user_id, db_cursor)["subscribers"]
        )
        return json.dumps(user)


def update_user(user):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            db_cursor = conn.cursor()

            action_payload = user.get("action")
            if action_payload:
                demotion_result = __handle_demotion__(
                    action_payload.get("action"),
                    action_payload.get("user_id"),
                    action_payload.get("approver_id"),
                    db_cursor,
                )

                if not isinstance(demotion_result, dict):
                    return json.dumps(
                        {
                            "ok": False,
                            "error": "Unable to process action request.",
                        }
                    )

                if demotion_result.get("ok") is False:
                    return json.dumps(demotion_result)

            has_new_image = "profile_image" in user and user["profile_image"]
            blob_data = None

            should_update_profile = all(
                key in user
                for key in [
                    "id",
                    "first_name",
                    "last_name",
                    "email",
                    "bio",
                    "username",
                    "password",
                ]
            )

            if should_update_profile:
                if has_new_image and isinstance(user["profile_image"], bytes):
                    blob_data = user["profile_image"]

                if has_new_image:
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
                            profile_image = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            user["first_name"],
                            user["last_name"],
                            user["email"],
                            user["bio"],
                            user["username"],
                            user["password"],
                            blob_data,
                            datetime.now(),
                            user["id"],
                        ),
                    )
                else:
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
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            user["first_name"],
                            user["last_name"],
                            user["email"],
                            user["bio"],
                            user["username"],
                            user["password"],
                            datetime.now(),
                            user["id"],
                        ),
                    )

            target_user_id = (
                action_payload.get("user_id") if action_payload else user.get("id")
            )

            if target_user_id is None:
                return json.dumps({"ok": False, "error": "User id is required."})

            db_cursor.execute(
                """
                SELECT
                    u.*,
                    CASE
                        WHEN d.admin_id IS NOT NULL THEN
                            json_group_array(json_object(
                                'action', d.action,
                                'admin_id', d.admin_id,
                                'approver_one_id', d.approver_one_id
                            ))
                        ELSE NULL
                    END AS demotion_queue
                FROM Users u
                LEFT JOIN DemotionQueue d
                ON d.admin_id = u.id
                WHERE u.id = ?
                GROUP BY u.id
                """,
                (target_user_id,),
            )

            updated_user = db_cursor.fetchone()
            if updated_user is None:
                return json.dumps({"ok": False, "error": "User not found."})

            updated_user_dict = dict(updated_user)

            if "profile_image" in updated_user_dict:
                del updated_user_dict["profile_image"]

            if updated_user_dict.get("demotion_queue") is not None:
                updated_user_dict["demotion_queue"] = json.loads(
                    updated_user_dict["demotion_queue"]
                )
            else:
                updated_user_dict.pop("demotion_queue", None)

            return json.dumps(updated_user_dict)
    except sqlite3.IntegrityError as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def __get_subscriptions__(user_id, db_cursor=None):
    execution = """
            SELECT
                json_group_array(json_object('id', u.id, 'username', u.username)) as subscriptions
            FROM Subscriptions s
            JOIN Users u
            ON s.author_id = u.id
            WHERE s.follower_id = ?
        """
    if db_cursor:
        db_cursor.execute(execution, (user_id,))

    else:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            db_cursor = conn.cursor()

            db_cursor.execute(
                execution,
                (user_id,),
            )

    subscriptions = dict(db_cursor.fetchone())

    return subscriptions


def __get_subscribers__(user_id, db_cursor=None):
    execution = """
        SELECT
            json_group_array(json_object('id', u.id, 'username', u.username)) as subscribers
        FROM Subscriptions s
        JOIN Users u
        ON s.follower_id = u.id
        WHERE s.author_id = ?
    """

    if db_cursor:
        db_cursor.execute(execution, (user_id,))

    else:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            db_cursor = conn.cursor()

            db_cursor.execute(
                execution,
                (user_id,),
            )

    subscribers = dict(db_cursor.fetchone())

    return subscribers


def add_subscription(user_id, sub_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        # Check if subscription already exists
        db_cursor.execute(
            """
            SELECT s.id FROM Subscriptions s
            WHERE s.author_id = ?
            AND s.follower_id = ?
            """,
            (sub_id, user_id),
        )

        existing = db_cursor.fetchone()

        if existing:
            # Return existing subscription
            subscription_id = existing["id"]
        else:
            # Create new subscription
            db_cursor.execute(
                """
                INSERT INTO Subscriptions (follower_id, author_id, created_on)
                VALUES (?, ?, ?)    
                """,
                (user_id, sub_id, datetime.now()),
            )
            subscription_id = db_cursor.lastrowid

        db_cursor.execute(
            """
            SELECT u.id, u.username FROM Subscriptions s
            JOIN Users u
            ON u.id = s.follower_id
            WHERE s.id = ?
            """,
            (subscription_id,),
        )

        subscription = db_cursor.fetchone()

        return json.dumps(dict(subscription))


def delete_subscription(user_id, sub_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            DELETE FROM Subscriptions
            WHERE follower_id = ?
            AND author_id = ?
            """,
            (
                user_id,
                sub_id,
            ),
        )

        return json.dumps({"deleted": "true"})


# views/user.py
def get_user_profile_image(user_id):
    """Returns only the profile image blob"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()
        db_cursor.execute("SELECT profile_image FROM Users WHERE id = ?", (user_id,))
        result = db_cursor.fetchone()
        return result[0] if result and result[0] else None


def __handle_demotion__(action, user_id, approver_id, db_cursor):
    try:
        if not action:
            return {"ok": False, "error": "Action is required."}

        if user_id is None:
            return {"ok": False, "error": "Action user_id is required."}

        if action == "activate":
            db_cursor.execute(
                """
                UPDATE Users
                SET active = 1
                WHERE id = ?
                """,
                (user_id,),
            )
            return {"ok": True}

        if action == "promote":
            db_cursor.execute(
                """
                UPDATE Users
                SET type = 'admin'
                WHERE id = ?
                """,
                (user_id,),
            )
            return {"ok": True}

        if action == "cancel deactivate":
            db_cursor.execute(
                """
                DELETE FROM DemotionQueue
                WHERE admin_id = ?
                AND action = 'deactivate'
                """,
                (user_id,),
            )
            return {"ok": True}

        if action == "cancel demote":
            db_cursor.execute(
                """
                DELETE FROM DemotionQueue
                WHERE admin_id = ?
                AND action = 'demote'
                """,
                (user_id,),
            )
            return {"ok": True}

        db_cursor.execute(
            """
            SELECT u.type
            FROM Users u
            WHERE u.id = ?
            """,
            (user_id,),
        )

        row = db_cursor.fetchone()
        if row is None:
            return {"ok": False, "error": "User not found."}

        user_type = row["type"]

        if user_type == "author" and action == "deactivate":
            db_cursor.execute(
                """
                UPDATE Users
                SET active = 0
                WHERE id = ?
                """,
                (user_id,),
            )
            return {"ok": True}

        db_cursor.execute(
            """
            SELECT * FROM DemotionQueue
            WHERE admin_id = ?
            AND action = ?
            """,
            (user_id, action),
        )

        pending_action = db_cursor.fetchone()

        if pending_action is None:
            db_cursor.execute(
                """
                INSERT INTO DemotionQueue
                (action, admin_id, approver_one_id)
                VALUES (?, ?, ?)
                """,
                (
                    action,
                    user_id,
                    approver_id,
                ),
            )
            return {"ok": True, "pending_approval": True}

        if pending_action["approver_one_id"] == approver_id:
            return {
                "ok": False,
                "error": "Action must be completed by a different admin.",
            }

        if action == "demote":
            db_cursor.execute(
                """
                UPDATE Users
                SET type = 'author'
                WHERE id = ?
                """,
                (user_id,),
            )

            db_cursor.execute(
                """
                DELETE FROM DemotionQueue
                WHERE action = ?
                AND admin_id= ?
                """,
                (
                    action,
                    user_id,
                ),
            )

            return {"ok": True}

        if action == "deactivate":
            db_cursor.execute(
                """
                UPDATE Users
                SET active = 0
                WHERE id = ?
                """,
                (user_id,),
            )

            db_cursor.execute(
                """
                DELETE FROM DemotionQueue
                WHERE admin_id = ?
                """,
                (user_id,),
            )

            return {"ok": True}

        return {"ok": False, "error": f"Unsupported action: {action}"}
    except sqlite3.IntegrityError as exc:
        return {"ok": False, "error": str(exc)}
