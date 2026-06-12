from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI()

# --- Database helpers ---

def get_db():
    conn = sqlite3.connect("leads.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with open("schema.sql") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

# --- Data model ---

class Lead(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

# --- API endpoints ---

@app.on_event("startup")
def startup():
    init_db()

@app.post("/leads")
def create_lead(lead: Lead):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO leads (name, email, phone) VALUES (?, ?, ?)",
            (lead.name, lead.email, lead.phone)
        )
        conn.commit()
        lead_id = cursor.lastrowid
        return {"success": True, "lead_id": lead_id, "message": f"Lead created for {lead.name}"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "A lead with this email already exists"}
    finally:
        conn.close()

@app.get("/leads")
def get_leads(status: Optional[str] = None):
    conn = get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return {"leads": [dict(row) for row in rows]}

@app.put("/leads/{lead_id}/status")
def update_status(lead_id: int, status: str):
    conn = get_db()
    conn.execute(
        "UPDATE leads SET status = ? WHERE id = ?",
        (status, lead_id)
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Lead #{lead_id} status updated to {status}"}