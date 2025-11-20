import json
import requests
from typing import List, Dict, Any
from requests.auth import HTTPBasicAuth
from src.config.constants import (
    CORRECTNESS_TRESHOLD,
    DEFAULT_RESPONSE_LANGUAGE,
    OLLAMA_API_URL,
    LLM_MODEL,
)
USERNAME = "anna"
PASSWORD = "!LmPF&$4"



def extract_text(chunk):
    if "text" in chunk:
        return chunk["text"]

    if "pages" in chunk:
        return "\n".join(
            "\n".join(page["lines"]) for page in chunk["pages"]
        )

    return ""


def generate_answer(
    query: str,
    context_chunks: List[Dict[str, Any]],
    response_language: str = DEFAULT_RESPONSE_LANGUAGE,
) -> str:

    context_text = "\n\n".join(
        f"[{chunk['file_id']}.{chunk['file_ext']}] {chunk['text']}"
        for chunk in context_chunks
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
            auth=HTTPBasicAuth(USERNAME, PASSWORD)
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
    response_language: str
) -> Dict[str, Any]:

    prompt = f"""
You evaluate how close a student's answer is to the reference answer.

CRITICAL RESTRICTIONS:
- You MUST NOT answer the question.
- You MUST NOT explain the topic.
- You MUST NOT add ANY new information.
- You MUST ONLY compare the student's answer with the reference answer.
- If you answer the question instead of evaluating → return EXACTLY:
{{ "score": 0, "feedback": "Invalid evaluation." }}

Allowed output format (MUST be valid JSON):
{{
  "score": number (0–100),
  "feedback": "text in {response_language}"
}}

REFERENCE ANSWER:
{reference_answer}

STUDENT ANSWER:
{user_answer}

QUESTION (DO NOT ANSWER IT):
{question}

NOW EVALUATE ONLY THE MATCH BETWEEN THE TWO ANSWERS.
RETURN ONLY THE JSON. DO NOT ANSWER THE QUESTION UNDER ANY CIRCUMSTANCES.
""".strip()

    try:
        response = requests.post(
            OLLAMA_API_URL + "/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            auth=HTTPBasicAuth(USERNAME, PASSWORD)
        )
        response.raise_for_status()

        raw = response.json().get("response", "").strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            print("⚠ LLM returned non-JSON, retrying...")
            return {
                "correct": False,
                "score": 0,
                "feedback": "Model returned invalid JSON."
            }

        score = parsed.get("score", 0)
        feedback = parsed.get("feedback", "No feedback.")

        correct = score >= 60  

        return {
            "correct": correct,
            "score": score,
            "feedback": feedback
        }

    except requests.RequestException as e:
        return {
            "correct": False,
            "score": 0,
            "feedback": f"Evaluation error: {e}"
        }


def generate_quiz_questions(
    context_chunks: List[Dict[str, Any]],
    num_questions,
    response_language,
) -> List[Dict[str, Any]]:

    context_text = "\n\n".join(extract_text(chunk) for chunk in context_chunks)

    print(f"generating quiz questions in {response_language}")

    prompt = f"""
You are a teacher.

Using ONLY the context below, generate EXACTLY {num_questions} quiz questions.

REQUIREMENTS:
- Output ONLY a JSON array.
- JSON must be valid.
- Every item MUST have:
    "type": "multiple_choice" or "open_ended"
    "question": string
    "topic": string
    "options": array of 4 strings OR null
    "answer": string
- All values must be written in {response_language}.
- JSON keys must stay in English.
All technical terms must be spelled correctly.
Do not invent new terms. Use only real terminology.
If unsure, choose the closest valid term.
If you cannot generate valid JSON → return [].
Each quiz item MUST include:
- question
- answer
- topic (LLM must classify the question into ONE short topic based ONLY on the context. 
  Topic must be 1–3 words.If unsure → choose the closest valid topic found in context.)

CONTEXT:
{context_text}

CONTEXT START
{context_text}
CONTEXT END

REMEMBER: Respond only in {response_language}. Output only the JSON array. Do NOT translate JSON field names.
"""

    try:
        response = requests.post(
            OLLAMA_API_URL + "/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            auth=HTTPBasicAuth(USERNAME, PASSWORD)
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

    except requests.RequestException as e:
        return [
            {"type": "error", "question": str(e), "options": None, "answer": ""}
        ]

    
    try:
        questions = json.loads(raw)
        if not isinstance(questions, list):
            print("❌ LLM returned non-array JSON:", questions)
            return []
    except Exception:
        print("❌ LLM returned invalid JSON:", raw)
        return []

    
    normalized = []

    for q in questions:
        if not isinstance(q, dict):
            continue

       
        ans = q.get("answer")
        if isinstance(ans, list):
            ans = " ".join(str(x) for x in ans)
        if isinstance(ans, (int, float)):
            ans = str(ans)
        if ans is None:
            ans = ""

       
        opts = q.get("options")
        if isinstance(opts, list):
            opts = [str(x) for x in opts]
        elif opts is None:
            opts = None
        else:
            opts = None

        
        item = {
            "type": q.get("type", "open_ended"),
            "question": q.get("question", "").strip(),
            "topic": q.get("topic", "General"),
            "options": opts,
            "answer": ans.strip(),
        }

     
        if item["question"] == "":
            continue

        normalized.append(item)

    return normalized
