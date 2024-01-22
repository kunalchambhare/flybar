# db.py
import sqlite3
from flask import g


class DatabaseManager:

    def __init__(self, app):
        self.app = app
        self.init_db()

    def get_db(self):
        if not hasattr(g, 'sqlite_db'):
            g.sqlite_db = sqlite3.connect(self.app.config['DATABASE'])
            g.sqlite_db.row_factory = sqlite3.Row
        return g.sqlite_db

    def init_db(self):
        with self.app.app_context():
            db = self.get_db()
            db.execute('''
                                CREATE TABLE IF NOT EXISTS packaging_order (
                                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                    order_name TEXT,
                                    weight TEXT,
                                    length TEXT,
                                    width TEXT,
                                    height TEXT,
                                    status TEXT,
                                    create_date TEXT,
                                    picking TEXT,
                                    error TEXT,
                                    msg TEXT
                                )
                            ''')

            db.execute('''
                CREATE TABLE IF NOT EXISTS status_boolean_table (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    status BOOLEAN DEFAULT 0
                )
            ''')

            db.commit()

    def close_db(self, error):
        if hasattr(g, 'sqlite_db'):
            g.sqlite_db.close()
