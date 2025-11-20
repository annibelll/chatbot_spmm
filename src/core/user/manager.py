import uuid
import sqlite3
from typing import Dict, List
from src.config.constants import SQL3_PATH


class UserManager:
    def __init__(self, db_path: str = SQL3_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_topic_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    topic TEXT,
                    attempts INTEGER DEFAULT 0,
                    correct INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
                """
            )
            conn.commit()

    def get_or_create_user(self, name: str) -> str:
        
        self._init_db()

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE name=?", (name,))
            row = cur.fetchone()
            if row:
                return row[0]

            user_id = f"user_{uuid.uuid4().hex[:8]}"
            cur.execute(
                "INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, name)
            )
            conn.commit()
            return user_id

    def update_topic_performance(self, user_id: str, topic: str, correct: bool):
        
        self._init_db()

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT attempts, correct FROM user_topic_stats WHERE user_id=? AND topic=?",
                (user_id, topic),
            )
            row = cur.fetchone()

            if row:
                attempts, correct_count = row
                cur.execute(
                    """
                    UPDATE user_topic_stats
                    SET attempts=?, correct=?
                    WHERE user_id=? AND topic=?
                    """,
                    (attempts + 1, correct_count + int(correct), user_id, topic),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO user_topic_stats (user_id, topic, attempts, correct)
                    VALUES (?, ?, 1, ?)
                    """,
                    (user_id, topic, int(correct)),
                )
            conn.commit()

    def get_user_profile(self, user_id: str) -> Dict:
        self._init_db()

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name, created_at FROM users WHERE user_id=?", (user_id,)
            )
            user = cur.fetchone()
            if not user:
                return {}

            cur.execute(
                "SELECT topic, attempts, correct FROM user_topic_stats WHERE user_id=?",
                (user_id,),
            )
            topics = cur.fetchall()

            return {
                "user_id": user_id,
                "name": user[0],
                "joined": user[1],
                "topics": [
                    {
                        "topic": t[0],
                        "attempts": t[1],
                        "correct": t[2],
                        "accuracy": round(t[2] / t[1] * 100, 2) if t[1] else 0,
                    }
                    for t in topics
                ],
            }

    def get_weak_topics(self, user_id: str, threshold: float = 70.0) -> List[str]:
        self._init_db()

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT topic, attempts, correct FROM user_topic_stats WHERE user_id=?
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            print(f"rows in weak_topics: {rows}")
            return [r[0] for r in rows if r[1] >= 1 and (r[2] / r[1] * 100) < threshold]

    def get_user_summary(self, user_id: str) -> Dict:
        self._init_db()

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT SUM(attempts), SUM(correct)
                FROM user_topic_stats
                WHERE user_id=?
                """,
                (user_id,),
            )
            total_attempts, total_correct = cur.fetchone() or (0, 0)

        if not total_attempts:
            return {"attempts": 0, "correct": 0, "accuracy": 0}

        return {
            "attempts": total_attempts,
            "correct": total_correct,
            "accuracy": round(total_correct / total_attempts * 100, 2),
        }
    def get_topic_difficulty(self, user_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
            """
            SELECT topic, attempts, correct
            FROM user_topic_stats
            WHERE user_id=?
            """,
            (user_id,)
        )
        rows = cur.fetchall()

        difficulty = []
        for topic, attempts, correct in rows:
            if attempts == 0:
                continue
            accuracy = correct / attempts * 100
            difficulty.append((topic, accuracy))
        difficulty.sort(key=lambda x: x[1]) 
        return difficulty
    def get_recommendations(self, user_id: str):
        difficulties = self.get_topic_difficulty(user_id)

        if not difficulties:
            return "No data yet ❗"

        weak = [t for t, acc in difficulties if acc < 70] 

        if not weak:
            return "No weak topics 🎉 You're doing great!"

        return "You should repeat: " + ", ".join(weak)