from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user_svc = UserService(db)
    existing = await user_svc.get_by_username(data.username)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = await user_svc.create_user(data.username, data.password)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(data: UserCreate, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user = await auth_service.authenticate(data.username, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = AuthService.create_token(user.id)
    return Token(access_token=token, token_type="bearer")
