from src.core.quiz.store import QuizStore
from src.core.quiz.evaluator import Evaluator
from src.core.user.manager import UserManager


class QuizEngine:
    def __init__(
        self, store: QuizStore, evaluator: Evaluator, user_manager: UserManager
    ):
        self.store = store
        self.evaluator = evaluator
        self.user_manager = user_manager

    def start(self, user_id, quiz_id):
        print(f"starting a quiz for user with id: {user_id}")
        self.offset = 0
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.summary = {"score": 0}
        return self.store.get_question(quiz_id, self.offset)

    def answer(self, question_id: str, user_answer: str):
        correct, feedback, score = self.evaluator.evaluate(
            self.quiz_id, question_id, user_answer
        )

        with self.store._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT topic FROM questions WHERE id=?", (question_id,))
            row = cur.fetchone()
            topic = row[0] if row else "Unknown"

        self.store.save_result(
            quiz_id=self.quiz_id,
            question_id=question_id,
            user_id=self.user_id,
            user_answer=user_answer,
            correct=correct,
            score=score,
        )

        self.user_manager.update_topic_performance(self.user_id, topic, correct)

        self.summary["score"] = int(self.summary.get("score", 0)) + int(score)
        self.offset += 1
        next_q = self.store.get_question(self.quiz_id, self.offset)

        if not next_q:
            summary = self.store.get_summary(self.quiz_id)
            summary["score"] = str(self.summary["score"])
            return {"feedback": feedback, "next": None, "summary": summary}

        return {"feedback": feedback, "next": next_q}
