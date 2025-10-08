import os
import pdfplumber
import pytesseract
import numpy as np
import cv2
import whisper
from src.db import insert_file, init_db,file_exists,get_file_text, get_last_modified
from src.utils import (
    extract_pdf_text,
    extract_image_data,
    extract_audio_text,
    extract_video_data
)
from src.db import insert_file
import os


def import_pdf(filepath):
    text = extract_pdf_text(filepath)
    insert_file(os.path.basename(filepath), "pdf", filepath, text)
    return text


def import_image(filepath):
    text = extract_image_data(filepath)
    insert_file(os.path.basename(filepath), "image", filepath, text)
    return text


def import_audio(filepath):
    text = extract_audio_text(filepath)
    insert_file(os.path.basename(filepath), "audio", filepath, text)
    return text


def import_video(filepath):
    text = extract_video_data(filepath)
    insert_file(os.path.basename(filepath), "video", filepath, text)
    return text

def import_file(filepath, filetype):
    if filetype == "pdf":
        return import_pdf(filepath)
    elif filetype == "image":
        return import_image(filepath)
    elif filetype == "audio":
        return import_audio(filepath)
    elif filetype == "video":
        return import_video(filepath)
    else:
        return None


def import_all_files(media_dir="media"):
    init_db()
    for folder in ["pdf", "images", "audio", "video"]:
        folder_path = os.path.join(media_dir, folder)
        if not os.path.exists(folder_path):
            continue

        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            fs_time = os.path.getmtime(filepath)
            db_time = get_last_modified(filename)

            
            if db_time and fs_time <= db_time:
                text = get_file_text(filename)
                print(f"{filename} already processed, loaded from DB.")
                if text:
                    print("Text preview:", text[:200])
                continue

            
            if folder == "pdf":
                text = import_pdf(filepath)
            elif folder == "images":
                text = import_image(filepath)
            elif folder == "audio":
                text = import_audio(filepath)
            elif folder == "video":
                text = import_video(filepath)
            else:
                text = ""

            print(f"Processed {filename} ({folder})")
            if text:
                print("Text preview:", text[:200])

if __name__ == "__main__":
    
    import_all_files()
