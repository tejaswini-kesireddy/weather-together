import sqlite3


class DB:
    def __init__(self):
        self.connection = sqlite3.connect(database="datastore.db")
        self.connection.execute("CREATE TABLE IF NOT EXISTS container ('email_address', 'zipcode', 'report_time', 'frequency')")


db = DB()


def get_existing_info():
    data = db.connection.execute("SELECT * FROM container")
    print(data.fetchall())
