from typing import Optional
from sqlmodel import SQLModel, Field

class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    phone: Optional[str] = None
    source: Optional[str] = None
    status: str = Field(default="new")
    notes: Optional[str] = None

class LeadCreate(SQLModel):
    name: str
    email: str
    phone: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None

class LeadUpdate(SQLModel):
    status: Optional[str] = None
    notes: Optional[str] = None