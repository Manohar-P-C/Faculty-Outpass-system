"""
Background Escalation Scheduler
Periodically checks for pending HOD requests that have exceeded the escalation timeout
and triggers automated AI Voice Calls to HOD Assistants.
"""

import time
import threading
from datetime import datetime
from db_setup import get_connection
from twilio_service import trigger_ai_escalation_call

SCHEDULER_INTERVAL_SECONDS = 60  # Check every 60 seconds

def check_and_escalate_pending_requests():
    """Find un-acted Pending HOD requests and dispatch AI calls."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Query pending requests with department HOD assistant details
        query = """
            SELECT 
                r.request_id,
                r.faculty_name,
                r.department,
                r.description,
                r.slot,
                r.created_at,
                TIMESTAMPDIFF(MINUTE, r.created_at, NOW()) AS pending_minutes,
                h.name AS hod_name,
                h.assistant_name,
                h.assistant_phone,
                COALESCE(h.escalation_timeout_mins, 15) AS escalation_timeout_mins,
                COALESCE(h.ai_call_enabled, 1) AS ai_call_enabled
            FROM faculty_requests r
            LEFT JOIN hods h ON r.department = h.department
            WHERE r.status = 'Pending HOD'
              AND (r.ai_call_sent = 0 OR r.ai_call_sent IS NULL)
        """
        cursor.execute(query)
        pending_requests = cursor.fetchall()
        cursor.close()
        conn.close()

        if not pending_requests:
            return

        for req in pending_requests:
            pending_mins = req.get("pending_minutes") or 0
            timeout_thresh = req.get("escalation_timeout_mins") or 15
            ai_enabled = req.get("ai_call_enabled") == 1
            assistant_phone = req.get("assistant_phone")

            if pending_mins >= timeout_thresh and ai_enabled and assistant_phone:
                print(f"[SCHEDULER] Request #{req['request_id']} has been pending for {pending_mins} mins (Threshold: {timeout_thresh} mins). Initiating AI Call...")
                trigger_ai_escalation_call(
                    request_id=req['request_id'],
                    faculty_name=req['faculty_name'],
                    department=req['department'],
                    assistant_name=req.get('assistant_name') or 'HOD Assistant',
                    assistant_phone=assistant_phone,
                    pending_minutes=pending_mins
                )

    except Exception as e:
        print(f"[SCHEDULER-ERROR] Error checking pending requests: {e}")


def _scheduler_loop():
    print("[SCHEDULER] AI Call Escalation Scheduler active. Checking every 60s...")
    while True:
        try:
            check_and_escalate_pending_requests()
        except Exception as e:
            print(f"[SCHEDULER-LOOP-ERROR] {e}")
        time.sleep(SCHEDULER_INTERVAL_SECONDS)


def start_escalation_scheduler():
    """Start the escalation scheduler daemon thread."""
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()
    return thread
