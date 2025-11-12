import uuid
from src.core.llm import generate_quiz_questions
from src.core.retriever import Retriever
from src.core.quiz.store import QuizStore
from src.config.constants import NUMBER_OF_QUIZ_CHUNKS


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
            answer = q.get("answer") or q.get("definition") or "No answer provided"

            # 🔧 Обробка випадків, коли answer — список
            if isinstance(answer, list):
                if all(isinstance(a, str) for a in answer):
                    answer = " ".join(answer)
                elif all(isinstance(a, dict) for a in answer):
                    # перетворюємо список словників у текст
                    parts = []
                    for a in answer:
                        part = ", ".join(f"{k}: {v}" for k, v in a.items())
                        parts.append(part)
                    answer = " | ".join(parts)
                else:
                    answer = str(answer)

            questions.append(
                {
                    "id": str(uuid.uuid4())[:8],
                    "type": q.get("type", "open"),
                    "question": q.get("question") or q.get("term") or "Unknown question",
                    "topic": q.get("topic"),
                    "options": q.get("options", []),
                    "answer": answer,
                }
            )

        quiz_id = self.store.create_quiz(questions)
        return quiz_id
