import sqlite3
import os

def initialize_database(db_path):
    """
    Initialize the SQLite database and create the 'transactions' table if it doesn't exist.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            item_name TEXT NOT NULL,
            company TEXT,
            amount REAL NOT NULL,
            type TEXT CHECK(type IN ('credit', 'debit')) NOT NULL,
            notes TEXT
        )
    ''')

    conn.commit()
    conn.close()
