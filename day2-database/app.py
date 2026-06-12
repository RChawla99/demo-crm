import sqlite3

# --- Database setup ---

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
    print("Database ready.")

# --- CRUD operations ---

def create_lead(name, email, phone=None):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO leads (name, email, phone) VALUES (?, ?, ?)",
            (name, email, phone)
        )
        conn.commit()
        lead_id = cursor.lastrowid
        print(f"Created lead #{lead_id}: {name}")
        return lead_id
    except sqlite3.IntegrityError:
        print(f"Error: a lead with email {email} already exists.")
        return None
    finally:
        conn.close()

def get_leads(status=None):
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
    return [dict(row) for row in rows]

def update_lead_status(lead_id, new_status):
    conn = get_db()
    conn.execute(
        "UPDATE leads SET status = ? WHERE id = ?",
        (new_status, lead_id)
    )
    conn.commit()
    conn.close()
    print(f"Lead #{lead_id} status → {new_status}")

def delete_lead(lead_id):
    conn = get_db()
    conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    print(f"Deleted lead #{lead_id}")

# --- Run it ---

if __name__ == "__main__":
    init_db()

    # Create some leads
    create_lead("Priya Sharma", "priya@gmail.com", "9876543210")
    create_lead("Rahul Verma", "rahul@gmail.com", "9123456789")
    create_lead("Priya Sharma", "priya@gmail.com")  # duplicate — should fail

    # Read all leads
    leads = get_leads()
    print(f"\nAll leads ({len(leads)} total):")
    for lead in leads:
        print(f"  #{lead['id']} {lead['name']} — {lead['status']}")

    # Update one
    update_lead_status(1, "contacted")

    # Read only new leads
    new_leads = get_leads(status="new")
    print(f"\nNew leads: {len(new_leads)}")
    