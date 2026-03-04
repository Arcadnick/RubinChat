from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.models import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, password: str) -> "User":
        from app.services.user import UserService

        user_service = UserService(self.db)
        return await user_service.create_user(username, password)

    async def authenticate(self, username: str, password: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def create_token(user_id: UUID) -> str:
        return create_access_token(str(user_id))

    @staticmethod
    def decode_token(token: str) -> UUID | None:
        sub = decode_access_token(token)
        if sub is None:
            return None
        try:
            return UUID(sub)
        except ValueError:
            return None
