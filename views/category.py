import sqlite3
import json

def get_all_categories():
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT * FROM Categories
            """,
        )

        categories = db_cursor.fetchall()

        return json.dumps([dict(row) for row in categories])
    
def get_category_by_id(id):
    with sqlite3.connect("./db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            SELECT * FROM Categories
            WHERE id = ?
            """,
            (id,),
        )

        category = db_cursor.fetchone()

        return json.dumps(dict(category))

def create_category(category):
    with sqlite3.connect("./db/sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        db_cursor = conn.cursor()

        db_cursor.execute(
            """
            INSERT INTO Categories
            (label)
            VALUES (?) 
            """,
            (category["label"],),
        )

        categoryId = db_cursor.lastrowid

        db_cursor.execute(
            """
            SELECT * FROM Categories
            WHERE id = ?
            """, (
                categoryId,
            ),
        )

        category = db_cursor.fetchone()
        

        return json.dumps(dict(category))