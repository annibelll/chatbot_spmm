import os
import pdfplumber
from PIL import Image
import pytesseract
import numpy as np
import cv2

from src.db import insert_file, init_db


def import_pdf(filepath):
    text = ""
    with pdfplumber.open(filepath) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if not text.strip():
        from pdf2image import convert_from_path
        pages = convert_from_path(filepath)
        for page in pages:
            cv_img = np.array(page)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            text += pytesseract.image_to_string(gray, lang="eng+ukr") + "\n"

    insert_file(os.path.basename(filepath), "pdf", filepath, text)
    return text


def import_image(filepath):
    img = Image.open(filepath)
    cv_img = np.array(img)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang="eng+ukr")

    insert_file(os.path.basename(filepath), "image", filepath, text)
    return text


def import_file(filepath, filetype):
    if filetype == "pdf":
        return import_pdf(filepath)
    elif filetype == "image":
        return import_image(filepath)
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
            
            
            if folder == "pdf":
                text = import_pdf(filepath)
            elif folder == "images":
                text = import_image(filepath)
            else:
                text = "" 

            print(f"Imported {filename} ({folder})")
            if text:
                print("Text preview:", text[:200])



if __name__ == "__main__":
    
    import_all_files()
