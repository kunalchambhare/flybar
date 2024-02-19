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
                                    error_odoo_update TEXT,
                                    msg TEXT,
                                    msg_odoo_update TEXT,
                                    main_operation_type TEXT,
                                    line_json_data TEXT,
                                    log TEXT,
                                    status_updated_to_odoo BOOLEAN,
                                    odoo_response_message TEXT,
                                    cron TEXT,
                                    celery_error TEXT
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
