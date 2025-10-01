import os
import pdfplumber
from PIL import Image
import pytesseract
import numpy as np
import cv2
from pdf2image import convert_from_path

MEDIA_DIR = "media"


def extract_text(filepath):
    with pdfplumber.open(filepath) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return text


def save_file(file, folder):
    folder_path = os.path.join(MEDIA_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, file.filename)
    file.save(filepath)
    return filepath


def extract_image_text(filepath):
    img = Image.open(filepath)
    cv_img = np.array(img)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang="eng+slk") 

    print("=== OCR TEXT FROM", filepath, "===")
    print(text)
    print("=== END OCR TEXT ===")

    return text


def extract_scanned_pdf_text(filepath):
    pages = convert_from_path(filepath)
    text = ""
    for page in pages:
        cv_img = np.array(page)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        text += pytesseract.image_to_string(gray, lang="eng+slk") + "\n"
    return text
