"""
Twilio Voice & AI Call Escalation Service
Handles outbound phone call triggers to HOD Assistants when faculty exit requests remain pending.
"""

import os
from datetime import datetime
from db_setup import get_connection

# Load Twilio config from environment
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "").strip()
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:5000").rstrip("/")

def is_twilio_configured():
    """Check if Twilio credentials are fully configured."""
    return bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)

def trigger_ai_escalation_call(request_id, faculty_name, department, assistant_name, assistant_phone, pending_minutes=15):
    """
    Trigger an outbound Twilio AI call to the HOD Assistant's mobile phone.
    Returns (success: bool, message_or_sid: str)
    """
    if not assistant_phone:
        return False, "No Assistant Phone number configured."

    # Standardize phone number format (ensure + format for international/Twilio calls)
    formatted_phone = assistant_phone.strip()
    if not formatted_phone.startswith("+"):
        # Assume Indian country code (+91) if 10 digits provided
        if len(formatted_phone) == 10 and formatted_phone.isdigit():
            formatted_phone = "+91" + formatted_phone

    print(f"[AI-CALL] Attempting escalation call for Request #{request_id} to Assistant {assistant_name} ({formatted_phone})...")

    if not is_twilio_configured():
        print("[AI-CALL-MOCK] Twilio credentials not set in .env. Mocking call success for testing.")
        log_ai_call(request_id, department, faculty_name, assistant_name, formatted_phone, "MOCK_CALL_SID", "Mock Triggered (No Twilio Keys)")
        update_request_ai_status(request_id, "MOCK_CALL_SID", "Mock Sent")
        return True, "MOCK_CALL_SID"

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        webhook_url = f"{PUBLIC_BASE_URL}/api/twilio/voice-webhook?request_id={request_id}"
        status_callback_url = f"{PUBLIC_BASE_URL}/api/twilio/call-status"

        call = client.calls.create(
            to=formatted_phone,
            from_=TWILIO_PHONE_NUMBER,
            url=webhook_url,
            status_callback=status_callback_url,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )

        print(f"[AI-CALL-SUCCESS] Call SID {call.sid} dispatched to {formatted_phone}.")
        
        # Log to DB
        log_ai_call(request_id, department, faculty_name, assistant_name, formatted_phone, call.sid, "Dispatched")
        update_request_ai_status(request_id, call.sid, "Dispatched")

        return True, call.sid

    except Exception as e:
        error_msg = str(e)
        print(f"[AI-CALL-ERROR] Failed to dispatch call: {error_msg}")
        log_ai_call(request_id, department, faculty_name, assistant_name, formatted_phone, None, f"Failed: {error_msg[:40]}")
        update_request_ai_status(request_id, None, "Failed")
        return False, error_msg


def log_ai_call(request_id, department, faculty_name, assistant_name, assistant_phone, call_sid, call_status):
    """Save call event to ai_call_logs table."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_call_logs (request_id, department, faculty_name, assistant_name, assistant_phone, call_sid, call_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (request_id, department, faculty_name, assistant_name or 'HOD Assistant', assistant_phone, call_sid, call_status))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB-ERROR] Failed to insert ai_call_logs: {e}")


def update_request_ai_status(request_id, call_sid, call_status):
    """Update faculty_requests table with call metadata."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE faculty_requests 
            SET ai_call_sent = 1, ai_call_sid = %s, ai_call_status = %s, ai_call_timestamp = NOW()
            WHERE request_id = %s
        """, (call_sid, call_status, request_id))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB-ERROR] Failed to update faculty_requests AI status: {e}")
