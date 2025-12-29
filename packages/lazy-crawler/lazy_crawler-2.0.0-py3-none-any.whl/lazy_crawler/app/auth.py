from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from lazy_crawler.app.database import get_session, User
from sqlmodel import select
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "changethiskey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


import hashlib
import base64


def _pre_hash(password: str) -> str:
    """
    Pre-hash the password to handle bcrypt's 72 byte limit.
    Using SHA256 + Base64 encoding.
    """
    return base64.b64encode(hashlib.sha256(password.encode()).digest()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_pre_hash(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(_pre_hash(password))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    request: Request = None,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check if token is in cookie if not in header
    if not token and request:
        cookie_auth = request.cookies.get("access_token")
        if cookie_auth:
            # Format: "Bearer <token>"
            valid = cookie_auth.startswith("Bearer ")
            if valid:
                token = cookie_auth.split(" ")[1]

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    # Check if token is in cookie if not in header
    if not token and request:
        cookie_auth = request.cookies.get("access_token")
        if cookie_auth:
            # Format: "Bearer <token>"
            valid = cookie_auth.startswith("Bearer ")
            if valid:
                token = cookie_auth.split(" ")[1]

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.first()
    return user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
