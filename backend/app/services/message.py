from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto import CryptoProvider
from app.models import Message, User
from app.services.user import UserService


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crypto = CryptoProvider()
        self.user_service = UserService(db)

    async def send(self, sender_id: UUID, receiver_id: UUID, payload: str) -> Message:
        sender = await self.user_service.get_by_id(sender_id)
        receiver = await self.user_service.get_by_id(receiver_id)
        if sender is None or receiver is None:
            raise ValueError("Sender or receiver not found")

        payload_bytes = payload.encode("utf-8")
        nonce = self.crypto.generate_nonce()
        sender_nonce = self.crypto.generate_nonce()

        private_key = await self.user_service.get_decrypted_private_key(sender)
        receiver_enc_key = await self.user_service.get_decrypted_encryption_key(receiver)
        sender_enc_key = await self.user_service.get_decrypted_encryption_key(sender)

        signature = await self.crypto.sign(private_key, payload_bytes)
        encrypted = await self.crypto.encrypt(receiver_enc_key, payload_bytes, nonce)
        sender_encrypted = await self.crypto.encrypt(sender_enc_key, payload_bytes, sender_nonce)

        msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            encrypted_payload=encrypted.hex(),
            sender_encrypted_payload=sender_encrypted.hex(),
            signature=signature.hex(),
            nonce=nonce.hex(),
            sender_nonce=sender_nonce.hex(),
        )
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def get_for_user(
        self, user_id: UUID, with_user_id: UUID | None = None
    ) -> list[tuple[Message, str, bool]]:
        """Returns list of (message, decrypted_payload_or_placeholder, signature_valid)."""
        q = select(Message).where(
            (Message.sender_id == user_id) | (Message.receiver_id == user_id)
        ).order_by(Message.timestamp)
        if with_user_id is not None:
            q = q.where(
                ((Message.sender_id == user_id) & (Message.receiver_id == with_user_id))
                | ((Message.receiver_id == user_id) & (Message.sender_id == with_user_id))
            )
        result = await self.db.execute(q)
        messages = list(result.scalars().all())
        out = []
        for msg in messages:
            receiver_id = msg.receiver_id
            sender_id = msg.sender_id
            receiver = await self.user_service.get_by_id(receiver_id)
            sender = await self.user_service.get_by_id(sender_id)
            if receiver is None or sender is None:
                continue
            if receiver_id == user_id:
                enc_key = await self.user_service.get_decrypted_encryption_key(receiver)
                ciphertext = bytes.fromhex(msg.encrypted_payload)
                nonce_bytes = bytes.fromhex(msg.nonce)
                sig = bytes.fromhex(msg.signature)
            else:
                if not msg.sender_encrypted_payload or not msg.sender_nonce:
                    payload_str = "[sent]"
                    valid = True
                    out.append((msg, payload_str, valid))
                    continue
                enc_key = await self.user_service.get_decrypted_encryption_key(sender)
                ciphertext = bytes.fromhex(msg.sender_encrypted_payload)
                nonce_bytes = bytes.fromhex(msg.sender_nonce)
                sig = bytes.fromhex(msg.signature)
            try:
                plain = await self.crypto.decrypt(enc_key, ciphertext, nonce_bytes)
                payload_str = plain.decode("utf-8")
                pub_key = bytes.fromhex(sender.public_key)
                valid = await self.crypto.verify(pub_key, plain, sig)
            except Exception:
                payload_str = "[decryption error]"
                valid = False
            out.append((msg, payload_str, valid))
        return out
