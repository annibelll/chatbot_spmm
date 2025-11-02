from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from core.user.manager import UserManager


class UserRequest(BaseModel):
    name: str


class UserResponse(BaseModel):
    user_id: str
    name: str


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse)
def register_user(req: UserRequest):
    user_id = user_manager.get_or_create_user(req.name)
    return UserResponse(user_id=user_id, name=req.name)


@router.get("/{user_id}")
def get_user_profile(user_id: str):
    profile = user_manager.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found.")
    return profile
