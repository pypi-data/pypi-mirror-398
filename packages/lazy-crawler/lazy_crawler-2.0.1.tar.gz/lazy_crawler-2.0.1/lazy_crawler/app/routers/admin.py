from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from lazy_crawler.app import config
from lazy_crawler.app.auth import get_current_superuser
from lazy_crawler.app.database import get_session, User
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional
from lazy_crawler.app.database.models import ContactSubmission

router = APIRouter(prefix="/admin", tags=["admin"])

# Template Engine
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)


@router.get("/contacts")
async def admin_contacts(
    request: Request,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Admin page to view contact messages"""
    statement = select(ContactSubmission).order_by(ContactSubmission.created_at.desc())
    results = await session.exec(statement)
    contacts = results.all()

    return templates.TemplateResponse(
        "admin_contacts.html",
        {
            "request": request,
            "active_page": "admin_contacts",
            "user": current_user,
            "contacts": contacts,
        },
    )
