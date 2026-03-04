from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_current_user_id
from app.database import get_db
from app.models import User
from app.schemas.user import UserResponse
from app.services.user import UserService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user_svc = UserService(db)
    users = await user_svc.list_users(exclude_id=current_user_id)
    return [UserResponse.model_validate(u) for u in users]
