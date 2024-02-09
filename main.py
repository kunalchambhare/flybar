# main.py
from flask import Flask, request, jsonify
from db import DatabaseManager
from celery_task import process_cron
import jwt
from datetime import datetime
import os
from config import JWT_SECRET_KEY, DATABASE
import logging
import json

_logger = logging.getLogger(__name__)


class FlybarAutomation:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.logger.setLevel(logging.INFO)
        self.app.config['SECRET_KEY'] = JWT_SECRET_KEY
        self.app.config['DATABASE'] = DATABASE
        auth_token = jwt.encode({'sub': 'user123'}, JWT_SECRET_KEY, algorithm='HS256')
        self.app.logger.info(f"AUTH TOKEN: {auth_token}")
        self.db_manager = DatabaseManager(self.app)
        self.register_routes()
        self.app.logger.info("FLASK INITIALIZED")

    def register_routes(self):
        self.app.route('/')(self.home)
        self.app.route('/flybar/test', methods=['GET'])(self.test_route)
        self.app.route('/flybar/post/packaging_data', methods=['POST'])(self.post_resource)

    def run(self):
        self.app.run(host='0.0.0.0', port=5000)

    def home(self):
        return 'Welcome to the FLYBAR SERVER!'

    def test_route(self):
        received_token = request.headers.get('Authorization')
        access_status = self.check_access(received_token)
        self.app.logger.info("FLASK TEST")
        if access_status.get('status') == 200:
            return jsonify({'message': 'Authorized'}), 200
        else:
            return jsonify({'message': 'Unauthorized'}), 200

    def get_cron_counts(self):
        db = self.db_manager.get_db()
        cursor = db.cursor()
        cron_list = ['cron_1', 'cron_2']
        in_clause = ', '.join(['?' for _ in cron_list])

        cursor.execute(f"""
            SELECT cron, COUNT(*) as count
            FROM packaging_order
            WHERE status = 'pending' AND cron IN ({in_clause})
            GROUP BY cron;
        """, cron_list)

        counts = {row[0]: row[1] for row in cursor.fetchall()}
        return counts

    def get_cron_with_min_count(self, cron_counts):
        if not cron_counts:
            return None
        min_count = min(cron_counts.values())
        min_keys = [key for key, count in cron_counts.items() if count == min_count]
        return min(min_keys, key=lambda x: x)

    def add_row_to_table(self, data):
        db = self.db_manager.get_db()
        order_name = data.get('order_name')
        weight = data.get('weight')
        length = data.get('length')
        width = data.get('width')
        height = data.get('height')
        picking = data.get('picking')
        main_operation_type = data.get('main_operation_type')
        line_json_data = json.dumps(data.get('line_json_data'))
        cron_count = self.get_cron_counts()
        cron = self.get_cron_with_min_count(cron_count)
        print(cron, cron_count)
        cursor = db.execute("""
            INSERT INTO packaging_order 
            (order_name, weight, length, width, height, status, create_date, picking, main_operation_type, line_json_data, cron) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_name, weight, length, width, height, 'pending', datetime.now(), picking, main_operation_type,
              line_json_data, cron))

        new_row_id = cursor.lastrowid
        db.commit()

        return new_row_id, cron

    def post_resource(self):
        try:
            received_token = request.headers.get('Authorization')
            response = self.check_access(received_token)
            if response['status'] == 200:

                data = json.loads(request.json)
                order_name = data.get('order_name')
                new_row_id, cron = self.add_row_to_table(data)
                db = self.db_manager.get_db()
                cursor = db.cursor()

                cron_db_id = int(cron.split('_')[1])

                cursor.execute('SELECT * FROM status_boolean_table WHERE ID = ?', (cron_db_id,))
                existing_row = cursor.fetchone()

                if not existing_row:
                    cursor.execute('INSERT INTO status_boolean_table (ID, status) VALUES (?, ?)', (cron_db_id, False))
                    db.commit()

                cursor.execute('SELECT * FROM status_boolean_table WHERE ID = ?', (cron_db_id,))
                existing_row = cursor.fetchone()

                if not existing_row[1]:
                    cursor.execute('UPDATE status_boolean_table SET status = ? WHERE ID = ?', (True, cron_db_id))
                    db.commit()
                    process_cron.delay(cron)

                result = {'message': f'Order: {order_name} Added to Queue',
                          "Ref": f'{new_row_id}'}
                logging.info(f'Order: {order_name} added to the queue with ref {new_row_id}')
                return jsonify(result), 200
            else:
                return jsonify(message=str(response['message']), status=401), 401
        except Exception as e:
            logging.error(f'An error occurred: {e}', exc_info=True)
            return jsonify(message=str(e), status=401), 401

    def check_access(self, received_token):
        try:
            decoded_token = jwt.decode(received_token, self.app.config['SECRET_KEY'], algorithms=['HS256'])
            if decoded_token:
                return {'status': 200, 'message': "Authorization successful"}
        except jwt.ExpiredSignatureError:
            return {'status': 401, 'message': "Token has expired"}
        except jwt.InvalidTokenError:
            return {'status': 401, 'message': "Unauthorized"}
        except Exception as e:
            return {'status': 401, 'message': str(e)}


if __name__ == '__main__':
    my_app = FlybarAutomation()
    my_app.run()
