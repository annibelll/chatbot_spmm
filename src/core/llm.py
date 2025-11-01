import re
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
            OLLAMA_API_URL,
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            # timeout=30
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "").strip()
    except requests.RequestException as e:
        answer = f"Error generating answer: {e}"

    if not answer:
        answer = "The context does not contain information to answer this question"

    return answer


def format_answer_with_citations(answer: str) -> str:
    pattern = r"\[([^\[\]]+\.(?:pdf|txt|jpg|png|mp3|mp4))\]"
    cited_files = set(re.findall(pattern, answer))
    return f"{answer}\n\nCited documents: {', '.join(cited_files) if cited_files else 'None'}"
