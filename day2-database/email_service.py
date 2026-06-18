import resend
import os
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


def send_new_lead_notification(
    business_email: str,
    lead_name: str,
    lead_email: str,
    lead_phone: str = None,
    lead_company: str = None,
):
    phone_line = f"<p><strong>Phone:</strong> {lead_phone}</p>" if lead_phone else ""
    company_line = f"<p><strong>Company:</strong> {lead_company}</p>" if lead_company else ""

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">New Lead Received</h2>
        <p>A new lead just came in through your website.</p>
        
        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p><strong>Name:</strong> {lead_name}</p>
            <p><strong>Email:</strong> {lead_email}</p>
            {phone_line}
            {company_line}
        </div>
        
        <p>Log in to your dashboard to view and manage this lead.</p>
    </div>
    """

    try:
        response = resend.Emails.send({
            "from": "CRM Notifications <onboarding@resend.dev>",
            "to": [business_email],
            "subject": f"New Lead: {lead_name}",
            "html": html_body,
        })
        print(f"Email sent successfully. ID: {response['id']}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False