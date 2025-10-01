from flask import Flask, request, jsonify
import os
import pdfplumber
from src.db import init_db, insert_file, get_all_files, get_files_by_type

app = Flask(__name__)
init_db()

MEDIA_DIR = "media"

def extract_text(filepath):
   
    with pdfplumber.open(filepath) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        print("=== PDF TEXT START ===")
        print(text[:300])  
        print("=== PDF TEXT END ===")
        return text


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    ext = file.filename.split(".")[-1].lower()
    if ext in ["pdf"]:
        folder = "pdf"
    elif ext in ["jpg", "jpeg", "png"]:
        folder = "images"
    elif ext in ["mp4", "avi"]:
        folder = "video"
    elif ext in ["mp3", "wav"]:
        folder = "audio"
    else:
        folder = "other"

    folder_path = os.path.join(MEDIA_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)

    filepath = os.path.join(folder_path, file.filename)
    file.save(filepath)

    insert_file(file.filename, folder, filepath)

    return jsonify({"message": f"{file.filename} saved", "path": filepath, "type": folder})


@app.route("/api/chat", methods=["POST"])
def chat_api():
    """
    Пошук відповіді по PDF-файлам з БД
    """
    data = request.json
    question = data.get("question", "")
    answer = find_answer(question)
    return jsonify({"question": question, "answer": answer})


def find_answer(question):
   
    pdf_files = get_files_by_type("pdf")  
    for f in pdf_files:
        text = extract_text(f["path"])  
        for line in text.split("\n"):
            if question.lower() in line.lower():
                return f"Found in {f['filename']}: {line}"
    return "Found nothing in any PDF."


if __name__ == "__main__":
    app.run(debug=True)
