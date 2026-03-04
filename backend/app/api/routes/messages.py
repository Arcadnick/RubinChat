from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.database import get_db
from app.schemas.message import MessageCreate, MessageOut
from app.services.message import MessageService
from app.websocket import connection_manager

router = APIRouter()


@router.post("", status_code=201)
async def create_message(
    data: MessageCreate,
    sender_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    msg_svc = MessageService(db)
    try:
        msg = await msg_svc.send(sender_id, data.receiver_id, data.payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await connection_manager.send_to_user(
        data.receiver_id,
        {"type": "new_message", "message_id": str(msg.id), "sender_id": str(sender_id)},
    )
    return {"id": str(msg.id), "timestamp": msg.timestamp.isoformat()}


@router.get("", response_model=list[MessageOut])
async def list_messages(
    current_user_id: UUID = Depends(get_current_user_id),
    with_user: UUID | None = Query(None, description="Filter by conversation partner"),
    db: AsyncSession = Depends(get_db),
):
    msg_svc = MessageService(db)
    rows = await msg_svc.get_for_user(current_user_id, with_user_id=with_user)
    return [
        MessageOut(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            payload=payload,
            signature_valid=valid,
            timestamp=msg.timestamp,
        )
        for msg, payload, valid in rows
    ]
