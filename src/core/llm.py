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
        correct = score >= CORRECTNESS_TRESHOLD

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
You are an expert teacher creating a quiz STRICTLY and EXCLUSIVELY from the provided CONTEXT below.
You must NOT use any external knowledge, guesses, or creative rewrite. ONLY leverage the text verbatim.

YOUR TASK:
- Generate EXACTLY {num_questions} quiz questions, mixing multiple-choice and open-ended.
- ALL questions and answers MUST be based SOLELY on the context provided—NO exceptions.
- Every question MUST be factual, concise, and answerable ONLY from the context.
- Each question should have a short topic string summarizing what it's about.

LANGUAGE:
- Write ALL questions, answers, and topics ONLY in {response_language}.
- Do not use any other language.

OUTPUT FORMAT:
- Your output MUST be a JSON array ONLY.
- Do NOT include any explanation, comment, markdown, extra text, labels, or formatting—JUST the JSON.
- Each array item must have this exact structure:

[
  {{
    "type": "multiple_choice" or "open_ended",
    "question": "string",       // Clear and concise question based only on context
    "topic": "string",          // Short topic summary (from context)
    "options": ["option1", "option2", "option3", "option4"] OR null, // For MC: 4 plain answer texts, NO labels. For open-ended: null.
    "answer": "string"          // For MC: MUST be EXACTLY one of options. For open-ended: factual answer from context.
  }},
  {{ ... }},
  {{ ... }}
]

IMPORTANT RULES:
- For multiple-choice, provide EXACTLY 4 answer texts, with NO "A/B/C/D" or numbering.
- For multiple-choice, "answer" must be EXACTLY one of the 4 options.
- For open-ended, "options" must be null.
- NEVER include explanations, comments, formatting, markdown, metadata, or repeated text.
- NEVER use any knowledge outside the provided context.
- Do NOT invent, speculate, or generalize beyond the context.

EXAMPLE OUTPUT STRUCTURE:
[
  {{
    "type": "multiple_choice",
    "question": "What is the main ingredient in soup X?",
    "topic": "Ingredients",
    "options": ["rice", "potato", "chicken", "beans"],
    "answer": "chicken"
  }},
  {{
    "type": "open_ended",
    "question": "List the two steps for process Y.",
    "topic": "Steps",
    "options": null,
    "answer": "Mix ingredients and cook for 10 minutes."
  }},
  ...
]

CONTEXT START
{context_text}
CONTEXT END
PLEASE RETURN ONLY A JSON ARRAY OF QUESTIONS WITH NO EXTRA TEXT.
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
