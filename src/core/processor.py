from pathlib import Path
import fitz
import pytesseract
from PIL import Image
import whisper


def extract_text(file_path: Path) -> str:
    """Extracts text from supported files (PDF, image, audio/video, txt)."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix in [".jpg", ".jpeg", ".png"]:
        return _extract_image(file_path)
    elif suffix in [".txt", ".md"]:
        return file_path.read_text(encoding="utf-8")
    elif suffix in [".mp3", ".wav", ".mp4"]:
        return _extract_audio(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _extract_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    text: str = ""

    with fitz.open(file_path) as pdf:
        for page in pdf:
            page_text = page.get_text("text")
            if not isinstance(page_text, str):
                page_text = str(page_text)
            text += page_text + "\n"

    return text.strip()


def _extract_image(file_path: Path) -> str:
    """Extract text from an image using OCR"""
    img: Image.Image = Image.open(file_path)
    text: str = pytesseract.image_to_string(img, lang="eng+slk")
    return text.strip()


def _extract_audio(file_path: Path) -> str:
    """Transcribe audio/video file using Whisper model."""
    model = whisper.load_model("base")  # "tiny", "small", etc.
    result: dict = model.transcribe(str(file_path))
    text: str = result.get("text", "")
    return text.strip()
