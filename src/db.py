import sqlite3
import os

DB_PATH = "chatbot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            filetype TEXT,      
            path TEXT,
            last_modified REAL, 
            text TEXT           
        )
    """)
    conn.commit()
    conn.close()


def insert_file(filename, filetype, path, text=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    filename = os.path.basename(filename).lower().strip()
    last_modified = os.path.getmtime(path)  
    cursor.execute("""
        INSERT INTO files (filename, filetype, path, last_modified, text)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(filename) DO UPDATE SET
            filetype = excluded.filetype,
            path = excluded.path,
            last_modified = excluded.last_modified,
            text = excluded.text
    """, (filename, filetype, path, last_modified, text))
    conn.commit()
    conn.close()

def file_exists(filename):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM files WHERE filename = ?", (filename,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def get_last_modified(filename):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT last_modified FROM files WHERE filename = ?", (filename,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_file_text(filename):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT text FROM files WHERE filename = ?", (filename,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_files():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, filetype, path, last_modified, text FROM files")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"filename": r[0], "filetype": r[1], "path": r[2], "last_modified": r[3], "text": r[4]}
        for r in rows
    ]


