# utils/db_setup.py

import sqlite3
import os

def initialize_database(db_path):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Sample table for transactions (customize later)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            item TEXT NOT NULL,
            company TEXT,
            amount REAL NOT NULL,
            type TEXT CHECK(type IN ('credit', 'debit')) NOT NULL,
            notes TEXT
        )
    ''')

    conn.commit()
    conn.close()
