from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from contextlib import asynccontextmanager

from models import Lead, LeadCreate, LeadUpdate
from database import create_db_and_tables, get_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="CRM Leads API", lifespan=lifespan)

@app.post("/leads", response_model=Lead)
def create_lead(lead_data: LeadCreate, session: Session = Depends(get_session)):
    lead = Lead.model_validate(lead_data)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead

@app.get("/leads", response_model=List[Lead])
def get_leads(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    return leads

@app.get("/leads/{lead_id}", response_model=Lead)
def get_lead(lead_id: int, session: Session = Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.patch("/leads/{lead_id}", response_model=Lead)
def update_lead(lead_id: int, lead_data: LeadUpdate, session: Session = Depends(get_session)):
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
def delete_lead(lead_id: int, session: Session = Depends(get_session)):
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    session.delete(lead)
    session.commit()
    return {"message": f"Lead {lead_id} deleted"}