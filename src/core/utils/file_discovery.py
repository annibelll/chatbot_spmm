from pathlib import Path
from typing import List, Optional


def discover_files(
    upload_dir: Path, allowed_exts: Optional[List[str]] = None
) -> List[Path]:
    """
    Scan a folder and return a list of valid files.
    """
    if allowed_exts is None:
        allowed_exts = ["pdf", "txt", "jpg", "png", "mp3", "mp4","m4a", "wav", "docx"]

    files = [
        f
        for f in upload_dir.iterdir()
        if f.is_file() and f.suffix.lower().lstrip(".") in allowed_exts
    ]
    return files
