from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from src.core.utils.file_discovery import discover_files
from src.config.constants import QUIZ_QUESTIONS_NUMBER, UPLOAD_DIR
from .dependency import get_processor, get_quiz_generator, get_quiz_engine


class QuizCreateRequest(BaseModel):
    num_questions: int
    language: str


class QuizCreateResponse(BaseModel):
    quiz_id: str
    total_questions: int = QUIZ_QUESTIONS_NUMBER


class QuizQuestionResponse(BaseModel):
    id: str
    question: str
    type: str
    options: Optional[List[str]] = None


class QuizAnswerRequest(BaseModel):
    quiz_id: str
    question_id: str
    user_id: str
    user_answer: str


class QuizAnswerResponse(BaseModel):
    correct: bool
    feedback: str
    score: float
    next_question: Optional[QuizQuestionResponse] = None
    summary: Optional[dict] = None


router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.post("/create", response_model=QuizCreateResponse)
async def create_quiz(req: QuizCreateRequest):
    upload_dir = Path(UPLOAD_DIR)
    files = discover_files(upload_dir)
    if not files:
        raise HTTPException(status_code=404, detail="No documents found.")

    await get_processor().process_files(files)

    quiz_id = await get_quiz_generator().generate_general(
        num_questions=req.num_questions,
        response_language=req.language,
    )

    return QuizCreateResponse(
        quiz_id=quiz_id,
    )


@router.get("/{quiz_id}/start", response_model=QuizQuestionResponse)
def start_quiz(quiz_id: str, user_id: str = Query(...)):
    q = get_quiz_engine().start(user_id, quiz_id)

    if not q:
        raise HTTPException(status_code=404, detail="No questions found.")

    if "question" not in q:
        q["question"] = q.get("term") or "Unknown question"

    if "id" not in q or not q["id"]:
        q["id"] = str(uuid.uuid4())

    return QuizQuestionResponse(**q)


@router.post("/answer", response_model=QuizAnswerResponse)
def answer_quiz(req: QuizAnswerRequest):
    result = get_quiz_engine().answer(
        req.question_id,
        req.user_answer,
    )

    next_q = result.get("next")

    return QuizAnswerResponse(
        correct=result.get("correct", False),
        feedback=result.get("feedback", ""),
        score=result.get("score", 0),
        next_question=next_q,
        summary=result.get("summary"),
    )
