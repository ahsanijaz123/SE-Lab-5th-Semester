from __future__ import annotations
import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

load_dotenv()

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

@function_tool
def send_email(recipient: str, subject: str, body: str) -> str:
    """Send an email using Gmail's SMTP server."""
    try:
       
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_EMAIL
        msg['To'] = recipient

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_EMAIL, recipient, msg.as_string())
        
        return f"Email sent successfully to {recipient}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

