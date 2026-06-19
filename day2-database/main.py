from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from contextlib import asynccontextmanager

from models import Lead, LeadCreate, LeadUpdate, LeadStatus, User, UserCreate, UserPublic
from database import create_db_and_tables, get_session
from email_service import send_new_lead_notification
from ai_service import score_lead
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_user_by_email,
    get_current_user
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="CRM Leads API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# —— AUTH ROUTES ————————————————————————————

@app.post("/auth/register", response_model=UserPublic)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    existing = get_user_by_email(user_data.email, session)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        business_name=user_data.business_name,
        hashed_password=hash_password(user_data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    user = get_user_by_email(form_data.username, session)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


# —— LEAD ROUTES (protected) ————————————————————————————

@app.post("/leads", response_model=Lead)
def create_lead(
    lead_data: LeadCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    lead = Lead(
        **lead_data.model_dump(),
        user_id=current_user.id
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


@app.get("/leads/stats")
def get_lead_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    leads = session.exec(
        select(Lead).where(Lead.user_id == current_user.id)
    ).all()

    stats = {status.value: 0 for status in LeadStatus}

    for lead in leads:
        stats[lead.status.value] += 1

    stats["total"] = sum(stats.values())

    return stats


@app.get("/leads", response_model=List[Lead])
def get_leads(
    status: Optional[LeadStatus] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    query = select(Lead).where(Lead.user_id == current_user.id)

    if status:
        query = query.where(Lead.status == status)

    leads = session.exec(query).all()
    return leads


@app.get("/leads/{lead_id}", response_model=Lead)
def get_lead(
    lead_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")
    return lead


@app.patch("/leads/{lead_id}", response_model=Lead)
def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    update_data = lead_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lead, key, value)

    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


@app.delete("/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    session.delete(lead)
    session.commit()
    return {"message": "Lead deleted"}
# —— WEBHOOK ROUTES ————————————————————————————

class WebhookLeadData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    business_email: str


@app.post("/webhook/lead")
def webhook_create_lead(
    data: WebhookLeadData,
    session: Session = Depends(get_session)
):
    business = get_user_by_email(data.business_email, session)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    lead = Lead(
        name=data.name,
        email=data.email,
        phone=data.phone,
        source=data.source,
        notes=data.notes,
        user_id=business.id
    )

    session.add(lead)
    session.commit()
    session.refresh(lead)
    ai_result = score_lead(data.name, data.email, data.phone, data.source, data.notes)
    if ai_result:
        lead.ai_score = ai_result["score"]
        lead.ai_summary = ai_result["summary"]
        session.add(lead)
        session.commit()
        session.refresh(lead)
    send_new_lead_notification(
        business_email=data.business_email,
        lead_name=data.name,
        lead_email=data.email or "Not provided",
        lead_phone=data.phone,
        lead_company=None,
    )
    return {"message": "Lead created", "lead_id": lead.id}