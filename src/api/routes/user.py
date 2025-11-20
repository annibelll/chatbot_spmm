from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from src.api.routes.dependency import get_user_manager, get_quiz_store



class UserRequest(BaseModel):
    name: str


class UserResponse(BaseModel):
    user_id: str
    name: str


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse)
def register_user(req: UserRequest):
    user_id = get_user_manager().get_or_create_user(req.name)
    return UserResponse(user_id=user_id, name=req.name)


@router.get("/{user_id}")
def get_user_profile(user_id: str):
    profile = get_user_manager().get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found.")
    return profile

@router.get("/weak_topics/{user_id}")
def get_weak_topics(user_id: str):
    manager = get_user_manager()
    store = get_quiz_store()

    user = manager.get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    weak_topics = manager.get_weak_topics(user_id)
    last_quizzes = store.get_last_quizzes(user_id, limit=3)
    summary = manager.get_user_summary(user_id)

    return {
        "user": user,
        "weak_topics": weak_topics,
        "last_quizzes": last_quizzes,
        "summary": summary
    }
