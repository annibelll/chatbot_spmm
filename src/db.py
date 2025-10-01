import sqlite3
import os

DB_PATH = "chatbot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            filetype TEXT,   -- pdf, image, video, audio
            path TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_file(filename, filetype, path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO files (filename, filetype, path) VALUES (?, ?, ?)",
        (filename, filetype, path)
    )
    conn.commit()
    conn.close()


def get_all_files():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, filetype, path FROM files")
    rows = cursor.fetchall()
    conn.close()
    return [{"filename": r[0], "filetype": r[1], "path": r[2]} for r in rows]


def get_files_by_type(filetype):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, path FROM files WHERE filetype=?", (filetype,))
    rows = cursor.fetchall()
    conn.close()
    return [{"filename": r[0], "path": r[1]} for r in rows]
