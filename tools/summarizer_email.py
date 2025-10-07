from __future__ import annotations
import os
import asyncio
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from agents import function_tool
from agents.extensions.models.litellm_model import LitellmModel

load_dotenv()

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

@function_tool
async def summarizer_email(max_emails: int = 10) -> str:
    """
    Retrieve and summarize the latest N emails into short 1–2 line summaries.

    Args:
        max_emails (int): Number of recent emails to summarize (default: 10)

    Returns:
        str: Formatted string with short summaries for each email
    """
    try:
        # Connect to Gmail via IMAP
        with imaplib.IMAP4_SSL('imap.gmail.com', 993) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.select('INBOX')

            # Fetch latest emails
            status, email_ids = server.search(None, 'ALL')
            if status != 'OK':
                return "Failed to retrieve emails."

            email_ids = email_ids[0].split()
            email_count = min(max_emails, len(email_ids))
            emails = []

            for email_id in email_ids[-email_count:]:
                status, msg_data = server.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = msg['subject']
                if subject:
                    subject_parts = decode_header(subject)[0]
                    subject = subject_parts[0]
                    if isinstance(subject, bytes):
                        encoding = subject_parts[1] if subject_parts[1] else 'utf-8'
                        subject = subject.decode(encoding, errors='ignore')
                else:
                    subject = "(No Subject)"

                from_ = msg.get('from', '(No Sender)')
                body = None

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode(part.get_content_charset('utf-8'), errors='ignore')
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode(msg.get_content_charset('utf-8'), errors='ignore')

                body = body or "(No body content)"
                emails.append({
                    "from": from_,
                    "subject": subject,
                    "body": body
                })

        # Summarize each email using the AI model
        model = LitellmModel(model="gemini/gemini-2.0-flash")
        summaries = []
        for i, email_data in enumerate(emails, start=1):
            prompt = (
                f"Summarize this email in 1–2 short sentences.\n"
                f"Focus only on key points (ignore greetings/signatures).\n\n"
                f"From: {email_data['from']}\n"
                f"Subject: {email_data['subject']}\n"
                f"Body:\n{email_data['body']}\n\n"
                f"Summary:"
            )
            result = await model.ainvoke(prompt)
            summaries.append(f"{i}. {result.strip()}")

        if not summaries:
            return "No emails found or summarized."

        return "\n".join(summaries)

    except Exception as e:
        return f"Failed to summarize emails: {str(e)}"
