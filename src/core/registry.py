import sqlite3, hashlib, time
from pathlib import Path
from config.constants import SQL3_PATH


class FileRegistry:
    def __init__(self, db_path: str = SQL3_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            """
        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            path TEXT,
            ext TEXT,
            hash TEXT,
            modified_at REAL,
            chunk_count INTEGER,
            processed_at REAL
        )"""
        )
        self.conn.commit()

    def compute_hash(self, file_path: Path) -> str:
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def has_changed(self, file_path: Path) -> bool:
        file_id = file_path.stem
        cur = self.conn.execute(
            "SELECT hash, modified_at FROM files WHERE file_id=?", (file_id,)
        )
        row = cur.fetchone()
        if not row:
            return True  # new file

        stored_hash, stored_mtime = row
        current_hash = self.compute_hash(file_path)
        current_mtime = file_path.stat().st_mtime
        return stored_hash != current_hash or stored_mtime != current_mtime

    def upsert(self, file_path: Path, chunk_count: int):
        file_id = file_path.stem
        file_hash = self.compute_hash(file_path)
        mtime = file_path.stat().st_mtime
        ext = file_path.suffix.lstrip(".")
        now = time.time()
        self.conn.execute(
            """
        INSERT INTO files (file_id, path, ext, hash, modified_at, chunk_count, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(file_id) DO UPDATE SET
            hash=excluded.hash,
            modified_at=excluded.modified_at,
            chunk_count=excluded.chunk_count,
            processed_at=excluded.processed_at
        """,
            (file_id, str(file_path), ext, file_hash, mtime, chunk_count, now),
        )
        self.conn.commit()
