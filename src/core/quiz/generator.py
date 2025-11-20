import uuid
from src.core.llm import generate_quiz_questions
from src.core.retriever import Retriever
from src.core.quiz.store import QuizStore
from src.config.constants import NUMBER_OF_QUIZ_CHUNKS
def is_valid_quiz_item(item):
 
    if not isinstance(item, dict):
        return False

    required = ["question", "answer"]
    if not all(k in item for k in required):
        return False

   
    if not item["question"] or item["question"].strip() == "":
        return False

    if not item["answer"] or item["answer"].strip() == "":
        return False

    return True


class QuizGenerator:
    def __init__(self, retriever: Retriever, store: QuizStore):
        self.retriever = retriever
        self.store = store

    async def generate_general(
        self,
        num_questions: int,
        response_language: str,
        retries: int = 0,
    ):
        chunks = self.retriever.retrieve(query="", top_k=NUMBER_OF_QUIZ_CHUNKS)
        llm_response = generate_quiz_questions(
            chunks, num_questions=num_questions, response_language=response_language
        )

        print(f"Generated quiz questions by LLM are: {llm_response}")
        valid_items = [item for item in llm_response if is_valid_quiz_item(item)]

        if len(valid_items) == 0:
            if retries >= 2:
                print("❌ LLM failed after retries. Returning empty quiz.")
                quiz_id = self.store.create_quiz([])
                return quiz_id, 0

            print("❌ Invalid quiz format. Retrying...")
            return await self.generate_general(num_questions, response_language, retries + 1)

        llm_response = valid_items

        questions = []
        for q in llm_response:
            answer = q.get("answer") or q.get("definition") or "No answer provided"

            if isinstance(answer, list):
                if all(isinstance(a, str) for a in answer):
                    answer = " ".join(answer)
                elif all(isinstance(a, dict) for a in answer):
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
                    "topic": q.get("topic") or "General",
                    "options": q.get("options", []) or [],
                    "answer": answer,
                }
            )

        
        quiz_id = self.store.create_quiz(questions)
        total = len(questions)
       
        
        return quiz_id, total
