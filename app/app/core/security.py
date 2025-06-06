from datetime import datetime, timedelta, UTC
from typing import Any, Union

from itsdangerous.exc import BadSignature
from itsdangerous.url_safe import URLSafeSerializer
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_value_secret_key(value: str, salt: str) -> str | None:
    s1 = URLSafeSerializer(settings.SECRET_KEY, salt=salt)
    return str(s1.dumps(value))


def get_value_from_secret_key(secret_key: str, salt: str) -> str | None:
    try:
        s1 = URLSafeSerializer(settings.SECRET_KEY, salt=salt)
        return str(s1.loads(secret_key))
    except BadSignature:
        return None
