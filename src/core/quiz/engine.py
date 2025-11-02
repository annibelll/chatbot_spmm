from core.quiz.store import QuizStore
from core.quiz.evaluator import Evaluator


class QuizEngine:
    def __init__(self, store: QuizStore, evaluator: Evaluator):
        self.store = store
        self.evaluator = evaluator

    def start(self, quiz_id):
        self.offset = 0
        self.quiz_id = quiz_id
        self.summary = {"score": 0}
        return self.store.get_question(quiz_id, self.offset)

    def answer(self, question_id, user_answer):
        correct, feedback, score = self.evaluator.evaluate(
            self.quiz_id, question_id, user_answer
        )
        self.store.save_result(self.quiz_id, question_id, user_answer, correct, score)
        self.summary["score"] += score

        self.offset += 1
        next_q = self.store.get_question(self.quiz_id, self.offset)
        if not next_q:
            summary = self.store.get_summary(self.quiz_id)
            summary["score"] = self.summary["score"]
            return {"feedback": feedback, "next": None, "summary": summary}
        return {"feedback": feedback, "next": next_q}
