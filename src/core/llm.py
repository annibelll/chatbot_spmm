import json
import requests
from typing import List, Dict, Any
from config.constants import (
    CORRECTNESS_TRESHOLD,
    DEFAULT_RESPONSE_LANGUAGE,
    OLLAMA_API_URL,
    LLM_MODEL,
)


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
    response_language: str,
) -> Dict[str, Any]:

    print(f"evaluating user answer in {response_language}")

    prompt = f"""
You are a fair teacher grading a student's open-ended answer.

Your steps:
1. Compare the student's answer to the reference answer.
2. Assign a score in this scale:
   - 0-4: mostly incorrect or irrelevant
   - 5-7: partially correct or incomplete
   - 8-10: accurate and complete
3. Write feedback in {response_language}.

Question: {question}
Reference Answer: {reference_answer}
Student Answer: {user_answer}

IMPORTANT:
- Respond ONLY with a valid JSON object.
- Write all feedback text ONLY in {response_language}.
- If you cannot follow these rules, respond with `{{
  "score": 0,
  "feedback": "Erreur."
}}`.

EXAMPLE OUTPUT: 
{{
  "score": 8,
  "feedback": "La réponse de l'étudiant est complète et précise."
}}

Now grade according to instructions.
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
        correct = score >= CORRECTNESS_TRESHOLD

        return {"correct": correct, "score": score, "feedback": feedback}

    except requests.RequestException as e:
        return {"correct": False, "score": 0, "feedback": f"Evaluation error: {e}"}


def generate_quiz_questions(
    context_chunks: List[Dict[str, Any]],
    num_questions,
    response_language,
) -> List[Dict[str, Any]]:

    context_text = "\n\n".join(
        f"[{chunk['file_id']}.{chunk['file_ext']}] {chunk['text']}"
        for chunk in context_chunks
    )

    print(f"generating quiz questions in {response_language}")

    prompt = f"""
You are an expert teacher creating a quiz STRICTLY and EXCLUSIVELY from the provided CONTEXT below.

DO NOT use any outside information—ONLY the context!

YOUR TASK:
1. Generate EXACTLY {num_questions} quiz questions (mix multiple-choice and open-ended).
2. ALL questions and answers MUST be based SOLELY on the context provided—NO exceptions.
3. Each question must be factual, concise, and answerable from the context only.
4. Each question must have a short topic string.

LANGUAGE IMPORTANT:
- Write ALL values in {response_language}: "question", "topic", "options", "answer".
- JSON field names ("type", "question", "topic", "options", "answer") must stay ENGLISH.
- For multiple-choice, do NOT translate "multiple_choice", for open-ended do NOT translate "open_ended".
- If you cannot follow these language rules, return ONLY '[]'.

FORMAT IMPORTANT:
- Output ONLY a JSON array, nothing else.
- Each item must match this EXACT structure.

EXAMPLE OUTPUT:
[
  {{
    "type": "multiple_choice",
    "question": "Quelle est la couleur principale de l'objet X?",
    "topic": "Couleur",
    "options": ["rouge", "vert", "bleu", "jaune"],
    "answer": "bleu"
  }},
  {{
    "type": "open_ended",
    "question": "Décrivez les deux étapes du processus Y.",
    "topic": "Étapes",
    "options": null,
    "answer": "Ajouter les ingrédients et cuire pendant 10 minutes."
  }}
]

CONTEXT START
{context_text}
CONTEXT END
REMEMBER: Respond only in {response_language}. Output only the JSON array. Do NOT translate JSON field names.
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
