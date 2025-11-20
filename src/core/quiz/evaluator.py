from src.core.user.manager import UserManager
from src.core.quiz.store import QuizStore
from src.core.llm import evaluate_open_answer
from src.config.constants import DEFAULT_RESPONSE_LANGUAGE


class Evaluator:
    def __init__(self, store: QuizStore, user_manager: UserManager):
        self.store = store
        self.user_manager = user_manager

    def evaluate(self, quiz_id, question_id, user_answer, user_id):
        with self.store._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT question, type, options, answer, topic
                FROM questions WHERE id=? AND quiz_id=?
                """,
                (question_id, quiz_id),
            )
            q = cur.fetchone()
            if not q:
                return False, "Question not found", 0

        question_text = q[0]
        q_type = q[1]
        correct_answer = q[3]
        topic = q[4] or "General"

        if q_type == "multiple_choice":
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            feedback = "Correct!" if is_correct else f"Wrong. Correct answer: {correct_answer}"

            self.user_manager.update_topic_performance(user_id, topic, is_correct)
            return is_correct, feedback, 1 if is_correct else 0

        eval_result = evaluate_open_answer(
            question_text, correct_answer, user_answer, DEFAULT_RESPONSE_LANGUAGE
        )

        is_correct = eval_result["correct"]
        self.user_manager.update_topic_performance(user_id, topic, is_correct)

        score = eval_result["score"] / 100
        return is_correct, eval_result["feedback"], score

