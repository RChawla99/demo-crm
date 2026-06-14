from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List
from contextlib import asynccontextmanager

from models import Lead, LeadCreate, LeadUpdate, User, UserCreate, UserPublic
from database import create_db_and_tables, get_session
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


# ─── AUTH ROUTES ─────────────────────────────────────────────────

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


# ─── LEAD ROUTES (protected) ─────────────────────────────────────

@app.post("/leads", response_model=Lead)
def create_lead(
    lead_data: LeadCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    lead = Lead.model_validate(lead_data)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


@app.get("/leads", response_model=List[Lead])
def get_leads(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    leads = session.exec(select(Lead)).all()
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
    session.delete(lead)
    session.commit()
    return {"message": f"Lead {lead_id} deleted"}