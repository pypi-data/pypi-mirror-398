from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from lazy_crawler.app.database import get_session, User
from lazy_crawler.app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from lazy_crawler.app import config
import httpx
from pydantic import BaseModel
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["authentication"])


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str = None


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.email == user_in.email)
    result = await session.exec(statement)
    existing_user = result.first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        provider="email",
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    statement = select(User).where(User.email == form_data.username)
    result = await session.exec(statement)
    user = result.first()

    if (
        not user
        or not user.hashed_password
        or not verify_password(form_data.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/google")
async def login_google():
    """Redirect to Google OAuth consent screen"""
    if not config.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID in environment variables.",
        )

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={config.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={config.GOOGLE_REDIRECT_URI}"
        f"&scope=openid%20profile%20email"
        f"&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str, session: AsyncSession = Depends(get_session)):
    """Handle Google OAuth callback and create/update user"""
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        access_token_data = response.json()

        if "error" in access_token_data:
            raise HTTPException(
                status_code=400,
                detail=f"Google Error: {access_token_data.get('error_description')}",
            )

        google_token = access_token_data["access_token"]

        # Get user info from Google
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_token}"},
        )
        user_info = user_info_response.json()

    email = user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=400, detail="Could not get email from Google profile"
        )

    # Check if user exists
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        # Create new user
        user = User(
            email=email,
            full_name=user_info.get("name"),
            profile_picture=user_info.get("picture"),
            provider="google",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # Create Local JWT token
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Redirect to dashboard with token in cookie
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/?message=Logged out successfully")
    response.delete_cookie("access_token")
    return response


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
