from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt accepts at most 72 bytes
_BCRYPT_MAX_PASSWORD_BYTES = 72


def _truncate_password_for_bcrypt(password: str) -> bytes:
    """Truncate to 72 bytes UTF-8 so bcrypt does not raise ValueError."""
    encoded = password.encode("utf-8")
    if len(encoded) <= _BCRYPT_MAX_PASSWORD_BYTES:
        return encoded
    encoded = encoded[:_BCRYPT_MAX_PASSWORD_BYTES]
    while encoded and (encoded[-1] & 0xC0) == 0x80:
        encoded = encoded[:-1]
    return encoded


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        _truncate_password_for_bcrypt(plain_password),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        _truncate_password_for_bcrypt(password),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
