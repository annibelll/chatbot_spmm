from src.config.constants import DEFAULT_RESPONSE_LANGUAGE
from src.core.llm import evaluate_open_answer
from src.core.quiz.store import QuizStore


class Evaluator:
    def __init__(self, store: QuizStore):
        self.store = store

    def evaluate(self, quiz_id, question_id, user_answer):
        with self.store._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT question, type, options, answer
                FROM questions WHERE id=? AND quiz_id=?
            """,
                (question_id, quiz_id),
            )
            q = cur.fetchone()
            if not q:
                return False, "Question not found", 0

        q_type, correct_answer = q[1], q[3]

        if q_type == "multiple_choice":
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            feedback = (
                "Correct!" if is_correct else f"Wrong. Correct answer: {correct_answer}"
            )
            score = 1 if is_correct else 0
            return is_correct, feedback, score

        # Open-ended → LLM is used for semantic comparison
        eval_result = evaluate_open_answer(q[0], correct_answer, user_answer, DEFAULT_RESPONSE_LANGUAGE)
        return eval_result["correct"], eval_result["feedback"], eval_result["score"]
