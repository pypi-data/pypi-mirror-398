from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: Optional[str] = Field(default=None)
    full_name: Optional[str] = None
    provider: str = Field(default="email")  # "email" or "google"
    profile_picture: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DatasetMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sync_id: str = Field(index=True, unique=True)
    filename: str
    file_type: str
    file_size: int
    mongo_collection_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")


class ContactSubmission(SQLModel, table=True):
    __tablename__ = "contact_us"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(index=True)
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
