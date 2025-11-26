import fitz
import whisper
from pathlib import Path
import pytesseract
from PIL import Image
from docx import Document 

def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix in [".jpg", ".jpeg", ".png"]:
        return _extract_image(file_path)
    elif suffix in [".txt", ".md"]:
        return file_path.read_text(encoding="utf-8")
    elif suffix in [".mp3", ".wav", ".mp4", ".m4a"]:
        return _extract_audio(file_path)
    elif suffix == ".docx":
        return _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

def _extract_pdf(file_path: Path) -> str:
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            page_text = page.get_text("text")
            text += (page_text if isinstance(page_text, str) else str(page_text)) + "\n"
    return text.strip()

def _extract_image(file_path: Path) -> str:
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img, lang="eng+slk")
    return text.strip()

def _extract_audio(file_path: Path) -> str:
    import subprocess
    import tempfile

    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_wav_path = temp_wav.name
    temp_wav.close()

    # Конвертуємо через ffmpeg — тепер шлях точно валідний
    cmd = [
        "ffmpeg", "-y",
        "-i", str(file_path),
        "-ac", "1",
        "-ar", "16000",
        temp_wav_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    model = whisper.load_model("base")
    result = model.transcribe(temp_wav_path)

    return result.get("text", "").strip()


def _extract_docx(file_path: Path) -> str:
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()

