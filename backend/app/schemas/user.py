from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class UserPublic(BaseModel):
    id: UUID
    username: str
    public_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserInDB(UserPublic):
    password_hash: str
    private_key_encrypted: str
    encryption_key_encrypted: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    public_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
