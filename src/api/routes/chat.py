from fastapi import APIRouter, HTTPException, File, UploadFile
from src.core.utils.file_discovery import discover_files
from src.core.llm import generate_answer
from .dependency import get_processor, get_retriever
from src.config.constants import UPLOAD_DIR
from fastapi import APIRouter, HTTPException
from src.core.embeddings import EmbeddingManager
from pydantic import BaseModel
from pathlib import Path
import shutil


class ChatRequest(BaseModel):
    query: str
    language: str


class ChatResponse(BaseModel):
    answer: str


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        upload_path = Path(UPLOAD_DIR)
        files = discover_files(upload_path)
        if not files:
            raise HTTPException(status_code=404, detail="No files uploaded yet.")

        await get_processor().process_files(files)
        retriever = get_retriever()
        chunks = retriever.retrieve(req.query, top_k=5)
        if not chunks:
            raise HTTPException(status_code=404, detail="No relevant context found.")

        answer = generate_answer(req.query, chunks, req.language)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")
@router.delete("/clear_embeddings")
def clear_embeddings():
    try:
        embedder = EmbeddingManager()
        embedder.clear_database() 
        return {"status": "ok", "message": "Embedding database cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/files/{filename}")
def delete_file(filename: str):
    """
    Delete a single uploaded file by its name.
    """
    try:
        file_path = Path(UPLOAD_DIR) / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        file_path.unlink()  
        return {"status": "ok", "message": f"File '{filename}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {e}")
    
@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        upload_dir = Path(UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        embedder = EmbeddingManager()
        text = ""
        if file_path.suffix.lower() == ".txt":
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        elif file_path.suffix.lower() == ".docx":
            from docx import Document
            doc = Document(file_path)
            text = "\n".join(p.text for p in doc.paragraphs)
        elif file_path.suffix.lower() == ".pdf":
            import fitz
            with fitz.open(file_path) as pdf:
                for page in pdf:
                    text += page.get_text()

        if text.strip():
            chunks = [{"file_id": file_path.stem, "file_ext": file_path.suffix.lstrip('.'), "text": text}]
            embedder.encode_and_store_chunks(chunks)

        return {"status": "ok", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


     
@router.get("/files")
def list_files():
    from pathlib import Path
    from fastapi import HTTPException
    from src.config.constants import UPLOAD_DIR

    try:
        upload_dir = Path(UPLOAD_DIR)
        if not upload_dir.exists():
            return {"files": []}
        files = [f.name for f in upload_dir.iterdir() if f.is_file()]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {e}")
    

@router.delete("/files/clear_all")    
def clear_all_files():
    try:
        upload_dir = Path(UPLOAD_DIR)
        if upload_dir.exists():
            for f in upload_dir.iterdir():
                if f.is_file():
                    f.unlink()
        embedder = EmbeddingManager()
        embedder.clear_database()
        return {"status": "ok", "message": "All files and embeddings deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing files: {e}")



