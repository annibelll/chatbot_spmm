from flask import Flask, request, jsonify
import os

# модулі
from src.utils import save_file, extract_image_text, extract_text
from src.db import insert_file, init_db
from src.search import find_answer
from src.importer import import_all_files   

app = Flask(__name__)

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

    filepath = save_file(file, folder)


    text = ""
    if folder == "pdf":
        text = extract_text(filepath)
    elif folder == "images":
        text = extract_image_text(filepath)

    
    insert_file(file.filename, folder, filepath, text)

    return jsonify({
        "message": f"{file.filename} saved",
        "path": filepath,
        "type": folder,
        "text_preview": text[:200] if text else None
    })


@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.json
    question = data.get("question", "")
    answer = find_answer(question)
    return jsonify({"question": question, "answer": answer})


if __name__ == "__main__":
    init_db()           
    import_all_files()   
    app.run(debug=True)  
