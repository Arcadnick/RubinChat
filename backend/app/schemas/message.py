from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    receiver_id: UUID
    payload: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    payload: str
    signature_valid: bool
    timestamp: datetime

    model_config = {"from_attributes": True}


class MessageInDB(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    encrypted_payload: str
    signature: str
    nonce: str
    timestamp: datetime

    model_config = {"from_attributes": True}
