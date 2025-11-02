from fastapi import APIRouter, HTTPException
from core.utils.file_discovery import discover_files
from core.llm import generate_answer
from .dependency import get_processor, get_retriever
from config.constants import UPLOAD_DIR
from pydantic import BaseModel
from pathlib import Path


class ChatRequest(BaseModel):
    query: str
    language: str = "en"


class ChatResponse(BaseModel):
    answer: str


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Ask a question about uploaded documents."""
    upload_path = Path(UPLOAD_DIR)
    files = discover_files(upload_path)
    if not files:
        raise HTTPException(
            status_code=404, detail="No files found to retrieve context."
        )

    await get_processor().process_files(files)
    chunks = get_retriever().retrieve(req.query, top_k=5)
    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant context found.")

    answer = generate_answer(req.query, chunks, req.language)
    return ChatResponse(answer=answer)
