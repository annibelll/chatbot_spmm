import uuid
from core.llm import generate_quiz_questions
from core.retriever import Retriever
from core.quiz.store import QuizStore
from config.constants import NUMBER_OF_QUIZ_CHUNKS


class QuizGenerator:
    def __init__(self, retriever: Retriever, store: QuizStore):
        self.retriever = retriever
        self.store = store

    async def generate_general(
        self,
        num_questions: int,
        response_language: str,
    ):
        chunks = self.retriever.retrieve(query="", top_k=NUMBER_OF_QUIZ_CHUNKS)

        llm_response = generate_quiz_questions(
            chunks, num_questions=num_questions, response_language=response_language
        )

        print(f"Generated quiz questions by LLM are: {llm_response}")

        questions = []
        for q in llm_response:
            questions.append(
                {
                    "id": str(uuid.uuid4())[:8],
                    "type": q["type"],
                    "question": q["question"],
                    "topic": q.get("topic"),
                    "options": q.get("options"),
                    "answer": q.get("answer"),
                }
            )

        quiz_id = self.store.create_quiz(questions)
        return quiz_id
