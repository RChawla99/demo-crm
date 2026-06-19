from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    closed = "closed"


class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    email: str = Field(unique=True, index=True)
    phone: Optional[str] = None
    source: Optional[str] = None
    status: LeadStatus = Field(default=LeadStatus.new)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ai_score: Optional[int] = None
    ai_summary: Optional[str] = None
    
class LeadCreate(SQLModel):
    name: str
    email: str
    phone: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    business_name: Optional[str] = None
    hashed_password: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    email: str
    password: str
    business_name: Optional[str] = None


class UserPublic(SQLModel):
    id: int
    email: str