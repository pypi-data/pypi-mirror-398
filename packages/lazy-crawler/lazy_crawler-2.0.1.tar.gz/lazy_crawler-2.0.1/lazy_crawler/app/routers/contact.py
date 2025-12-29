from fastapi import APIRouter, HTTPException, Depends, Request
from lazy_crawler.app.database.models import ContactSubmission
from pydantic import BaseModel, EmailStr
from lazy_crawler.app.limiter import limiter
from fastapi import APIRouter, Request, Depends
from lazy_crawler.app import config
from lazy_crawler.app.database import User
from typing import Optional
import os
from lazy_crawler.app.database import get_session, User
from sqlmodel.ext.asyncio.session import AsyncSession


router = APIRouter(prefix="/contact", tags=["contact"])


class ContactForm(BaseModel):
    full_name: str
    email: EmailStr
    message: str


@router.post("")
@limiter.limit("5/minute")
async def submit_contact_form(
    request: Request, form: ContactForm, session: AsyncSession = Depends(get_session)
):
    """
    Handles contact form submission and saves to database.
    """
    try:
        # Create new contact submission
        contact = ContactSubmission(
            full_name=form.full_name,
            email=form.email,
            message=form.message,
        )

        # Save to database
        session.add(contact)
        await session.commit()
        await session.refresh(contact)

        return {"message": "Thank you! Your message has been received."}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
