import sqlite3
from datetime import datetime
import os

class DBService:
    def __init__(self, db_name="nexus.db"):
        self.db_name = db_name
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        conn.execute('''CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, pan TEXT, amount REAL, status TEXT, 
            pdf_url TEXT, created_at TIMESTAMP)''')
        conn.commit()
        conn.close()

    def check_user_history(self, name):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loans WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1", (f"%{name}%",))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"exists": True, "name": row["name"], "last_amount": row["amount"]}
        return {"exists": False}

    def save_loan(self, name, pan, amount, pdf_url):
        conn = self._get_connection()
        conn.execute('INSERT INTO loans (name, pan, amount, status, pdf_url, created_at) VALUES (?, ?, ?, ?, ?, ?)',(name, pan, amount, "APPROVED", pdf_url, datetime.now()))
        conn.commit()
        conn.close()