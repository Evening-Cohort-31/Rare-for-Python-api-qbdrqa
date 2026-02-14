import sqlite3


def get_all_posts():
    with sqlite3.connect("./db.sqlite3") as conn:
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
