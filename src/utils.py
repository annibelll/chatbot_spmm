import os
import pdfplumber
from PIL import Image
import pytesseract
import numpy as np
import cv2
import whisper
import subprocess
from pdf2image import convert_from_path
from transformers import BlipProcessor, BlipForConditionalGeneration


whisper_model = whisper.load_model("base")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

MEDIA_DIR = "media"


def save_file(file, folder):
    folder_path = os.path.join(MEDIA_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, file.filename)
    file.save(filepath)
    return filepath

def extract_pdf_text(filepath):
    text = ""
    with pdfplumber.open(filepath) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if not text.strip():
        pages = convert_from_path(filepath)
        for page in pages:
            cv_img = np.array(page)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            text += pytesseract.image_to_string(gray, lang="eng+sk") + "\n"

    return text.strip() or "[No text detected]"


def extract_image_data(filepath):
    try:
   
        img = Image.open(filepath)
        cv_img = np.array(img)

 
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)


        ocr_text = pytesseract.image_to_string(gray, lang="eng+ukr").strip()

   
        raw_image = img.convert("RGB")
        inputs = blip_processor(raw_image, return_tensors="pt")
        out = blip_model.generate(**inputs)
        caption = blip_processor.decode(out[0], skip_special_tokens=True)

  
        full_text = (
            f" Description: {caption}\n"
            f" Detected text: {ocr_text or '[No text detected]'}"
        )
       

        return full_text

    except Exception as e:
        print(f"Error while processing image {filepath}: {e}")
        return "[Error during image analysis]"
    
def clean_audio(filepath):
    fixed_path = "temp_fixed.wav"
    subprocess.run([
        "ffmpeg", "-i", filepath,
        "-ac", "1",       
        "-ar", "16000",    
        fixed_path, "-y"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return fixed_path
def extract_audio_text(filepath):
    fixed_audio = clean_audio(filepath)
    result = whisper_model.transcribe(fixed_audio, language="en")  
    os.remove(fixed_audio)
    return result["text"].strip() or "[No speech detected]"


def extract_video_data(filepath):
    audio_path = "temp_audio.wav"

    subprocess.run([
        "ffmpeg", "-i", filepath,
        "-q:a", "0", "-map", "a", audio_path, "-y"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    audio_text = extract_audio_text(audio_path)
    os.remove(audio_path)

    out_dir = "frames_temp"
    os.makedirs(out_dir, exist_ok=True)

    subprocess.run([
        "ffmpeg", "-i", filepath,
        "-vf", "select='not(mod(t,5))'",
        "-vsync", "vfr",
        os.path.join(out_dir, "frame_%04d.jpg"),
        "-hide_banner", "-loglevel", "error"
    ])

    frame_texts = []
    for frame_file in sorted(os.listdir(out_dir)):
        frame_path = os.path.join(out_dir, frame_file)
        frame_texts.append(extract_image_data(frame_path))
        os.remove(frame_path)

    os.rmdir(out_dir)

    return f"Audio transcript:\n{audio_text}\n\nFrames:\n" + "\n\n".join(frame_texts)
