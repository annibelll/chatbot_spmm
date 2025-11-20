import uuid
import json
import sqlite3
from src.config.constants import SQL3_PATH


class QuizStore:
    def __init__(self, db_path: str = SQL3_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.executescript(
                """
            CREATE TABLE IF NOT EXISTS quizzes (
                quiz_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                quiz_id TEXT,
                question TEXT,
                type TEXT,
                options TEXT,
                answer TEXT,
                topic TEXT
            );

            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id TEXT,
                question_id TEXT,
                user_id TEXT,
                user_answer TEXT,
                correct INTEGER,
                score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            )
            conn.commit()

    def create_quiz(self, questions):
        quiz_id = f"quiz_{uuid.uuid4().hex[:8]}"
        quiz_topic = self.detect_quiz_topic(questions)
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO quizzes (quiz_id) VALUES (?)", (quiz_id,))
            for q in questions:
                cur.execute(
                    """
                    INSERT INTO questions (id, quiz_id, question, type, options, answer, topic)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        q["id"],
                        quiz_id,
                        q["question"],
                        q["type"],
                        json.dumps(q.get("options")),
                        q["answer"],
                        q.get("topic", quiz_topic),
                    ),
                )
            conn.commit()
        return quiz_id

    def get_question(self, quiz_id, offset):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, question, type, options
                FROM questions
                WHERE quiz_id=?
                LIMIT 1 OFFSET ?
                """,
                (quiz_id, offset),
            )
            row = cur.fetchone()

            if not row:
                return None

            return {
                "id": row[0],
                "question": row[1],
                "type": row[2],
                "options": json.loads(row[3]) if row[3] else None,
            }

    def save_result(self, quiz_id, question_id, user_id, user_answer, correct, score):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO results (quiz_id, question_id, user_id, user_answer, correct, score)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    quiz_id,
                    question_id,
                    user_id,
                    user_answer,
                    int(correct),
                    score
                ),
            )
            conn.commit()

    def get_summary(self, quiz_id):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*), SUM(correct)
                FROM results
                WHERE quiz_id=?
                """,
                (quiz_id,),
            )
            total, correct = cur.fetchone()

        return {
            "total": total or 0,
            "correct": correct or 0
        }
    def detect_quiz_topic(self, questions):
        topics = [q.get("topic") for q in questions if q.get("topic")]
        if not topics:
            return "General"
        return max(set(topics), key=topics.count)

    def get_last_quizzes(self, user_id, limit=3):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
            """
            SELECT 
                q.quiz_id,
                AVG(r.score) AS avg_score,
                q.created_at
            FROM quizzes q
            JOIN results r ON q.quiz_id = r.quiz_id
            WHERE r.user_id = ?
            GROUP BY q.quiz_id
            ORDER BY q.created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()

        return [
            {
                "quiz_id": quiz_id,
                "average_score": avg_score,
                "created_at": created_at
            }
            for quiz_id, avg_score, created_at in rows
        ]
