import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.crypto import CryptoProvider
from app.crypto.provider import GOST28147_KEYSIZE
from app.models import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crypto = CryptoProvider()

    def _master_key_bytes(self) -> bytes:
        raw = settings.MASTER_KEY.strip()
        if len(raw) != 64 or not all(c in "0123456789abcdefABCDEF" for c in raw):
            raise ValueError("MASTER_KEY must be 64 hex characters (32 bytes)")
        return bytes.fromhex(raw)

    async def create_user(self, username: str, password: str) -> User:
        private_key, public_key_bytes = await self.crypto.generate_keypair()
        encryption_key = os.urandom(GOST28147_KEYSIZE)

        master = self._master_key_bytes()
        private_enc = await self.crypto.encrypt_key_with_master(master, private_key)
        encryption_enc = await self.crypto.encrypt_key_with_master(master, encryption_key)

        user = User(
            username=username,
            password_hash=get_password_hash(password),
            public_key=public_key_bytes.hex(),
            private_key_encrypted=private_enc,
            encryption_key_encrypted=encryption_enc,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def list_users(self, exclude_id: UUID | None = None) -> list[User]:
        q = select(User).order_by(User.username)
        if exclude_id is not None:
            q = q.where(User.id != exclude_id)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_decrypted_private_key(self, user: User) -> bytes:
        master = self._master_key_bytes()
        return await self.crypto.decrypt_key_with_master(master, user.private_key_encrypted)

    async def get_decrypted_encryption_key(self, user: User) -> bytes:
        master = self._master_key_bytes()
        return await self.crypto.decrypt_key_with_master(master, user.encryption_key_encrypted)
