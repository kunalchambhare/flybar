# celery_task.py
from celery import Celery
import sqlite3
from selenium_tasks import SeleniumProcesses
from datetime import datetime

celery = Celery(
    'celery_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
)
from config import DATABASE


@celery.task
def process_pending_tasks():
    db = sqlite3.connect(DATABASE)

    cursor = db.execute('SELECT * FROM packaging_order WHERE status = ? ORDER BY create_date ASC LIMIT 1', ('pending',))
    pending_task = cursor.fetchone()

    if pending_task:
        log = []
        start_time = datetime.now()
        task_id = pending_task[0]
        cursor.execute('UPDATE packaging_order SET status = ? WHERE ID = ?', ('processing', task_id))
        db.commit()
        log.append(f'<p>Process started at {str(start_time)}.<p>')
        try:
            cursor = db.execute('SELECT * FROM packaging_order WHERE ID = ?', (task_id,))
            user_row = cursor.fetchone()
            columns = [col[0] for col in cursor.description]
            user_dict = dict(zip(columns, user_row))
            selenium = SeleniumProcesses()
            selenium.log = list(log)
            success, exceptt, msg = selenium.process_order(user_dict)
            selenium.log.append(f"<p>Process completed at {str(datetime.now())}</p>")
            if success:
                cursor.execute('UPDATE packaging_order SET status = ?, log = ? WHERE ID = ?',
                               ('completed', " ".join(selenium.log), task_id))
                db.commit()
                print(exceptt, msg)
            else:
                cursor.execute('UPDATE packaging_order SET error = ?, msg = ?, log = ? WHERE ID = ?',
                               (str(exceptt), str(msg), " ".join(selenium.log), task_id))
                db.commit()
                print(exceptt, msg)
                raise exceptt
        except Exception as e:
            print("Ex", e)
            cursor.execute('UPDATE packaging_order SET status = ? WHERE ID = ?', ('failed', task_id))
            db.commit()

        db.commit()
        cursor = db.execute('SELECT * FROM packaging_order WHERE status = ? ORDER BY create_date ASC LIMIT 1',
                            ('pending',))
        pending_task = cursor.fetchone()

        if pending_task:
            process_pending_tasks.delay()
        else:
            cursor.execute('UPDATE status_boolean_table SET status = ? WHERE ID = ?', (False, 1))
            db.commit()


if __name__ == '__main__':
    celery.start()
