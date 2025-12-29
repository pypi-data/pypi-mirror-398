"""
Page routes - template rendering for web pages
"""

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, FileResponse
from lazy_crawler.app import config
from lazy_crawler.app.auth import get_current_user_optional
from lazy_crawler.app.database import User
from typing import Optional
import os

router = APIRouter(tags=["pages"])

# Template Engine
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)


@router.get("/")
def read_root(
    request: Request, current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Home page"""
    return templates.TemplateResponse(
        "index.html", {"request": request, "active_page": "home", "user": current_user}
    )


@router.get("/login")
def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register")
def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/dashboard")
def read_dashboard(
    request: Request, current_user: Optional[User] = Depends(get_current_user_optional)
):
    """User dashboard"""
    if not current_user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "active_page": "dashboard", "user": current_user},
    )


@router.get("/about")
def read_about(
    request: Request, current_user: Optional[User] = Depends(get_current_user_optional)
):
    """About page"""
    return templates.TemplateResponse(
        "about.html", {"request": request, "active_page": "about", "user": current_user}
    )


@router.get("/contact")
def read_contact(
    request: Request, current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Contact page"""
    return templates.TemplateResponse(
        "contact.html",
        {"request": request, "active_page": "contact", "user": current_user},
    )


@router.get("/privacy")
def read_privacy(
    request: Request, current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Privacy policy page"""
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request, "active_page": "privacy", "user": current_user},
    )


@router.get("/faq")
def read_faq(
    request: Request, current_user: Optional[User] = Depends(get_current_user_optional)
):
    """FAQ page"""
    return templates.TemplateResponse(
        "faq.html", {"request": request, "active_page": "faq", "user": current_user}
    )


@router.get("/company")
def read_company(
    request: Request, current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Company page (Teams + Careers)"""
    team_members = [
        {
            "name": "Alex Morgan",
            "role": "Founder & CEO",
            "image": "https://ui-avatars.com/api/?name=Alex+Morgan&background=4a154b&color=fff",
        },
        {
            "name": "Sarah Chen",
            "role": "CTO",
            "image": "https://ui-avatars.com/api/?name=Sarah+Chen&background=1264a3&color=fff",
        },
        {
            "name": "James Wilson",
            "role": "Head of Product",
            "image": "https://ui-avatars.com/api/?name=James+Wilson&background=2eb67d&color=fff",
        },
        {
            "name": "Emily Rodriguez",
            "role": "VP of Sales",
            "image": "https://ui-avatars.com/api/?name=Emily+R&background=e01e5a&color=fff",
        },
        {
            "name": "James Wilson",
            "role": "Data aquistion Lead",
            "image": "https://ui-avatars.com/api/?name=James+Wilson&background=2eb67d&color=fff",
        },
        {
            "name": "William Lee",
            "role": "Lead Data Scientist",
            "image": "https://ui-avatars.com/api/?name=Emily+R&background=e01e5a&color=fff",
        },
    ]

    job_openings = [
        {
            "title": "Senior Python Engineer",
            "department": "Engineering",
            "location": "Remote (Global)",
            "tags": ["Full-time", "Senior"],
        },
        {
            "title": "Data Solutions Architect",
            "department": "Solutions",
            "location": "Sydney / Remote",
            "tags": ["Full-time", "Mid-Senior"],
        },
        {
            "title": "Product Designer (UI/UX)",
            "department": "Design",
            "location": "New York / Remote",
            "tags": ["Contract", "Mid-Level"],
        },
    ]

    return templates.TemplateResponse(
        "company.html",
        {
            "request": request,
            "active_page": "company",
            "user": current_user,
            "team_members": team_members,
            "job_openings": job_openings,
        },
    )


@router.get("/sitemap.xml")
def get_sitemap():
    """Sitemap for SEO"""
    return FileResponse(os.path.join(config.STATIC_DIR, "sitemap.xml"))


@router.get("/robots.txt")
def get_robots():
    """Robots.txt for search engines"""
    return FileResponse(os.path.join(config.STATIC_DIR, "robots.txt"))
