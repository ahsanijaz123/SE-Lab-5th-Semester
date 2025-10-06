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
def retrieve_emails(max_emails: int = 10) -> str:
    """Retrieve a specified number of emails from the inbox using Gmail's IMAP server, including sender, subject, date, and body."""
    import imaplib
    import email
    from email.header import decode_header
    try:
        
        with imaplib.IMAP4_SSL('imap.gmail.com', 993) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.select('INBOX')

       
            status, email_ids = server.search(None, 'ALL')
            if status != 'OK':
                return "Failed to retrieve emails: Unable to search inbox"

            email_ids = email_ids[0].split()
            email_count = min(max_emails, len(email_ids))
            emails = []

            
            for email_id in email_ids[-email_count:]:
                status, msg_data = server.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    emails.append(f"Email ID {email_id.decode()}: Failed to fetch email")
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

            
                date_ = msg.get('date', '(No Date)')

              
                body = None
                debug_info = []
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        disposition = str(part.get('Content-Disposition', '')).lower()
                        charset = part.get_content_charset('utf-8')
                        if 'attachment' in disposition:
                            debug_info.append(f"Skipped part: {content_type} (attachment)")
                            continue
                        if content_type in ['text/plain', 'text/html']:
                            try:
                                payload = part.get_payload(decode=True)
                                if payload is None:
                                    debug_info.append(f"Skipped part: {content_type} (no payload)")
                                    continue
                                body_text = payload.decode(charset, errors='ignore')
                                if content_type == 'text/plain':
                                    body = body_text
                                    break  
                                elif content_type == 'text/html' and body is None:
                                    body = body_text  
                            except Exception as e:
                                debug_info.append(f"Error in part {content_type}: {str(e)}")
                        else:
                            debug_info.append(f"Skipped part: {content_type} (non-text)")
                else:
                    try:
                        charset = msg.get_content_charset('utf-8')
                        payload = msg.get_payload(decode=True)
                        body = payload.decode(charset, errors='ignore') if payload else "(No body content)"
                    except Exception as e:
                        debug_info.append(f"Error decoding single-part: {str(e)}")

                if not body:
                    body = f"(No body content available. Debug: {'; '.join(debug_info)})" if debug_info else "(No body content available)"

                
                emails.append(f"From: {from_}\nSubject: {subject}\nDate: {date_}\nBody: {body}\n")

            if not emails:
                return "No emails found in the inbox."

            return "\n".join(emails)
    except Exception as e:
        return f"Failed to retrieve emails: {str(e)}"

