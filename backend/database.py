import sqlite3
from datetime import datetime


def initialize_db():
    with sqlite3.connect("pdfs.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                upload_date TEXT NOT NULL,
                content TEXT  
            )
        """)
        conn.commit()


def insert_pdf(filename, content=""):
    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect("pdfs.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pdf WHERE filename = ?", (filename,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute(
                "UPDATE pdf SET upload_date = ?, content = ? WHERE filename = ?",
                (upload_date, content, filename)
            )
        else:
            cursor.execute(
                "INSERT INTO pdf (filename, upload_date, content) VALUES (?, ?, ?)",
                (filename, upload_date, content)
            )
        conn.commit()


def get_pdf():
    with sqlite3.connect("pdfs.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename FROM pdf")
        return [row[0] for row in cursor.fetchall()]


def get_pdf_content(filename):
    with sqlite3.connect("pdfs.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM pdf WHERE filename = ?", (filename,))
        result = cursor.fetchone()
        return result[0] if result else None
