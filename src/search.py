from src.utils import extract_text,extract_image_text, extract_scanned_pdf_text
from src.db import get_all_files
import re


def find_answer(question: str):
   
    files = get_all_files()

    for f in files:
        text = f.get("text", "")
        if not text:
            continue

        if re.search(question, text, re.IGNORECASE):
            return f"Found in {f['filename']}: {question}"

    return "Found nothing in any PDF or image."
