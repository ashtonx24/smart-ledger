import sqlite3
from utils.config import DB_PATH

def add_transaction(data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (date, item_name, amount, category, payment_method, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['date'], data['item_name'], data['amount'],
        data['category'], data['payment_method'], data.get('notes')
    ))
    conn.commit()
    conn.close()

def get_all_transactions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions')
    rows = cursor.fetchall()
    conn.close()
    return rows
