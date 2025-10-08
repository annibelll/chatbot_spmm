from flask import Flask, request, jsonify
import os


from src.utils import save_file, extract_image_data, extract_pdf_text,extract_audio_text,extract_video_data
from src.db import insert_file, init_db
from src.search import find_answer
from src.importer import import_all_files, import_pdf, import_image, import_audio, import_video

app = Flask(__name__)

def upload_file():

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

 
    ext = file.filename.split(".")[-1].lower()
    if ext == "pdf":
        folder = "pdf"
    elif ext in ["jpg", "jpeg", "png"]:
        folder = "images"
    elif ext in ["mp3", "wav"]:
        folder = "audio"
    elif ext in ["mp4", "avi", "mov", "mkv"]:
        folder = "video"
    else:
        folder = "other"


    filepath = save_file(file, folder)

 
    text = ""
    if folder == "pdf":
        text = import_pdf(filepath)
    elif folder == "images":
        text = import_image(filepath)
    elif folder == "audio":
        text = import_audio(filepath)
    elif folder == "video":
        text = import_video(filepath)
    else:
        text = "[Unsupported file type]"

    return jsonify({
        "message": f"{file.filename} saved and processed successfully",
        "path": filepath,
        "type": folder,
        "text_preview": text[:300] if text else None
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
    app.run(debug=False)  
