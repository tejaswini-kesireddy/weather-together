import sqlite3

from modules.accessories import user_data


class DB:
    def __init__(self):
        self.connection = sqlite3.connect(database="datastore.db")
        self.connection.execute(f"CREATE TABLE IF NOT EXISTS container {user_data.user_input}")


db = DB()


def get_existing_info():
    with db.connection:
        cursor = db.connection.cursor()
        retrieve = cursor.execute(
            "SELECT * FROM container"
        ).fetchall()
    return retrieve
