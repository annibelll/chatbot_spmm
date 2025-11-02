import json
import requests
from typing import List, Dict, Any
from config.constants import DEFAULT_RESPONSE_LANGUAGE, OLLAMA_API_URL, LLM_MODEL


def generate_answer(
    query: str,
    context_chunks: List[Dict[str, Any]],
    response_language: str = DEFAULT_RESPONSE_LANGUAGE,
) -> str:
    context_text = "\n\n".join(
        [
            f"[{chunk['file_id']}.{chunk['file_ext']}] {chunk['text']}"
            for chunk in context_chunks
        ]
    )

    prompt = f"""
Use only the provided context to answer the question.
- Do NOT hallucinate or add information not present in the context.
- If the context contains even a single mention of the term in the question, report it literally and cite the source.
- Respond in {response_language}, even if the sources are in a different language.
- If the context contains no relevant information, respond with: "The context does not contain information to answer this question."

Context:
{context_text}

Question: {query}
Answer:
    """

    try:
        response = requests.post(
            OLLAMA_API_URL + "/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "").strip()
    except requests.RequestException as e:
        answer = f"Error generating answer: {e}"

    if not answer:
        answer = "The context does not contain information to answer this question"

    return answer


def evaluate_open_answer(
    question: str,
    reference_answer: str,
    user_answer: str,
    response_language: str = DEFAULT_RESPONSE_LANGUAGE,
) -> Dict[str, Any]:
    prompt = f"""
You are a fair teacher grading a student's open-ended answer.
Evaluate how closely the student's answer matches the reference answer.

Grading scale:
- 0-4 points: mostly incorrect or irrelevant
- 5-7 points: partially correct or incomplete
- 8-10 points: accurate and complete

Question: {question}

Reference Answer: {reference_answer}
Student Answer: {user_answer}

Respond STRICTLY in JSON:
{{
  "score": int (0-10),
  "feedback": "{response_language} text feedback"
}}
"""

    try:
        response = requests.post(
            OLLAMA_API_URL + "/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"score": 0, "feedback": raw}

        score = int(parsed.get("score", 0))
        feedback = parsed.get("feedback", "No feedback.")
        correct = score >= 6  # threshold for marking as "correct"

        return {"correct": correct, "score": score, "feedback": feedback}

    except requests.RequestException as e:
        return {"correct": False, "score": 0, "feedback": f"Evaluation error: {e}"}


def generate_quiz_questions(
    context_chunks: List[Dict[str, Any]],
    num_questions: int = 3,
    response_language: str = DEFAULT_RESPONSE_LANGUAGE,
) -> List[Dict[str, Any]]:

    context_text = "\n\n".join(
        f"[{chunk['file_id']}.{chunk['file_ext']}] {chunk['text']}"
        for chunk in context_chunks
    )

    prompt = f"""
You are a teacher preparing a quiz strictly from the provided context.
Do not use external knowledge.
Create exactly {num_questions} questions (mix of multiple-choice and open-ended).
Prefer concise phrasing and factual correctness.
For each question, include the correct answer.
The questions and answers must be in {response_language}.

Output JSON list:
[
  {{
    "type": "multiple_choice" | "open_ended",
    "question": "string",
    "options": ["A", "B", "C", "D"] or null,
    "answer": "string"
  }}
]

Context:
{context_text}
"""

    try:
        response = requests.post(
            OLLAMA_API_URL + "/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

        try:
            questions = json.loads(raw)
        except json.JSONDecodeError:
            print(raw)
            questions = []
    except requests.RequestException as e:
        questions = [
            {"type": "error", "question": str(e), "options": None, "answer": ""}
        ]

    return questions
