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
            filetype TEXT,      -- pdf, image, video, audio
            path TEXT,
            last_modified REAL, -- час останньої зміни файлу
            text TEXT           -- витягнутий текст
        )
    """)
    conn.commit()
    conn.close()


def insert_file(filename, filetype, path, text=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    last_modified = os.path.getmtime(path)  # час зміни файлу
    cursor.execute("""
        INSERT OR REPLACE INTO files (filename, filetype, path, last_modified, text)
        VALUES (?, ?, ?, ?, ?)
    """, (filename, filetype, path, last_modified, text))
    conn.commit()
    conn.close()


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


def get_files_by_type(filetype):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, path, text FROM files WHERE filetype=?", (filetype,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {"filename": r[0], "path": r[1], "text": r[2]}
        for r in rows
    ]

