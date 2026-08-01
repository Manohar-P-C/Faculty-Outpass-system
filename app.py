from flask import Flask, render_template, request, redirect, session, flash, jsonify
from datetime import datetime, timedelta, date
import threading
import time as _time
import uuid
import smtplib
from email.message import EmailMessage
import random
import re
import os
import mysql.connector
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "svit_secret_key")
app.permanent_session_lifetime = timedelta(days=30)

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_photo(req_files, field_name="photo"):
    if field_name in req_files:
        file = req_files[field_name]
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if filename == '':
                # secure_filename can return empty string for non-ASCII filenames
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
                import time
                filename = f"photo_{int(time.time())}.{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return filename
    return None

if os.environ.get("VERCEL"):
    UPLOAD_FOLDER = "/tmp"
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    except Exception:
        UPLOAD_FOLDER = "/tmp"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -----------------------
# MYSQL DATABASE CONFIG
# -----------------------
def get_db():
    """Get a MySQL database connection dynamically from environment variables."""
    host = os.environ.get("DB_HOST", "localhost")
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASSWORD", "manohar2129")
    name = os.environ.get("DB_NAME", "college_db")
    port = int(os.environ.get("DB_PORT", 3306))
    ssl_val = str(os.environ.get("DB_SSL", "false")).lower()
    ssl_enabled = ssl_val in ("true", "1", "required")

    config = {
        'host': host,
        'user': user,
        'password': password,
        'database': name,
        'port': port,
    }
    if ssl_enabled:
        config['ssl_disabled'] = False
        config['ssl_verify_cert'] = False
    return mysql.connector.connect(**config)

@app.errorhandler(500)
def internal_error(e):
    import traceback
    return f"<h2>500 Internal Server Error</h2><pre>{traceback.format_exc()}</pre>", 500

# -----------------------
# DB HELPER FUNCTIONS
# -----------------------
def db_get_user(table, email):
    """Get a user by email from a given table."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table} WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close(); conn.close()
    return user

def db_get_all(table, where_clause="", params=(), order_by=""):
    """Get all rows from a table with optional WHERE and ORDER BY."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM {table}"
    if where_clause:
        query += f" WHERE {where_clause}"
    if order_by:
        query += f" ORDER BY {order_by}"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows

def db_update_password(table, email, new_password):
    """Update password for a user in database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table} SET password = %s WHERE email = %s", (new_password, email))
    conn.commit(); cursor.close(); conn.close()

# -----------------------
# DB HELPERS FOR FACULTY REQUESTS
# -----------------------

def parse_slot_start(slot_str, req_date):
    """Parse the slot string (e.g. '12:30 PM (1h)' or '12:30 (1h)') and request_date
    into a datetime representing the slot start time.
    Handles both 12-hour and 24-hour time formats.
    Returns a datetime object, or None if parsing fails."""
    try:
        if not slot_str:
            return None
        # Extract time part before the parentheses
        time_part = slot_str.split("(")[0].strip()
        if not time_part:
            return None

        # Try 12-hour format first: "2:30 PM", "12:30 AM"
        parsed_time = None
        for fmt in ["%I:%M %p", "%H:%M"]:
            try:
                parsed_time = datetime.strptime(time_part, fmt)
                break
            except ValueError:
                continue

        if parsed_time is None:
            print(f"[SLOT PARSE ERROR] Could not parse time '{time_part}' from slot '{slot_str}'")
            return None

        start_hour = parsed_time.hour
        start_minute = parsed_time.minute

        if req_date:
            if isinstance(req_date, str):
                req_date = datetime.strptime(req_date, "%Y-%m-%d").date()
            slot_start_dt = datetime.combine(req_date, datetime.min.time()).replace(
                hour=start_hour, minute=start_minute
            )
        else:
            now = datetime.now()
            slot_start_dt = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

        return slot_start_dt
    except Exception as e:
        print(f"[SLOT PARSE ERROR] Failed to parse slot '{slot_str}' with date '{req_date}': {e}")
        return None


def db_insert_request(req_data):
    """Insert a faculty request into the database and return it."""
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("""INSERT INTO faculty_requests 
        (request_id, faculty_email, faculty_name, department, description, slot, duration_hours, status, proof, request_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (req_data["id"], req_data["email"], req_data["name"], req_data["department"],
         req_data["description"], req_data["slot"], req_data.get("duration_hours", 1), req_data["status"], req_data.get("proof"), req_data.get("request_date")))
    conn.commit(); cursor.close(); conn.close()

def db_get_all_requests():
    """Get all faculty requests from the database."""
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM faculty_requests ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    # Map DB columns to the dict keys used in templates
    results = []
    for r in rows:
        results.append({
            "id": r["request_id"],
            "name": r["faculty_name"],
            "email": r["faculty_email"],
            "department": r["department"],
            "description": r["description"],
            "slot": r["slot"],
            "duration_hours": r.get("duration_hours", 1),
            "status": r["status"],
            "deadline": r.get("deadline"),
            "hod_approved_by": r.get("hod_approved_by"),
            "hod_approved_at": r.get("hod_approved_at"),
            "principal_approved_at": r.get("principal_approved_at"),
            "created_at": r["created_at"],
            "proof": r.get("proof"),
            "request_date": r.get("request_date"),
            "exit_scan_time": r.get("exit_scan_time"),
            "entry_scan_time": r.get("entry_scan_time"),
            "scanned_by_exit": r.get("scanned_by_exit"),
            "scanned_by_entry": r.get("scanned_by_entry"),
            "reminder_sent": r.get("reminder_sent", 0),
            "rejection_reason": r.get("rejection_reason")
        })
    return results

def is_pass_expired(req):
    """Check if an approved request's QR pass is expired (more than 1 day past its approved deadline/timing)."""
    if not req or req.get("status") != "Approved":
        return True
    now = datetime.now()

    # 1. Check approved deadline
    deadline = req.get("deadline")
    if deadline:
        if isinstance(deadline, str):
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    deadline = datetime.strptime(deadline, fmt)
                    break
                except ValueError:
                    continue
        if isinstance(deadline, datetime):
            return now > (deadline + timedelta(days=1))

    # 2. Fallback to request_date
    req_date = req.get("request_date")
    if req_date:
        if isinstance(req_date, str):
            try:
                req_date = datetime.strptime(req_date, "%Y-%m-%d").date()
            except ValueError:
                pass
        if isinstance(req_date, datetime):
            req_date = req_date.date()
        if isinstance(req_date, date):
            end_of_req_day = datetime.combine(req_date, datetime.max.time())
            return now > (end_of_req_day + timedelta(days=1))

    # 3. Fallback to created_at
    created_at = req.get("created_at")
    if created_at:
        if isinstance(created_at, str):
            try:
                created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        if isinstance(created_at, datetime):
            return now > (created_at + timedelta(days=1))

    return False

def db_update_request(req_id, updates):
    """Update a faculty request in the database."""
    set_clauses = []
    values = []
    for key, val in updates.items():
        # Map dict keys to DB column names
        col_map = {"status": "status", "deadline": "deadline",
                    "hod_approved_by": "hod_approved_by", "hod_approved_at": "hod_approved_at",
                    "principal_approved_at": "principal_approved_at",
                    "exit_scan_time": "exit_scan_time", "entry_scan_time": "entry_scan_time",
                    "scanned_by_exit": "scanned_by_exit", "scanned_by_entry": "scanned_by_entry",
                    "reminder_sent": "reminder_sent", "warning_sent": "warning_sent",
                    "rejection_reason": "rejection_reason"}
        if key in col_map:
            set_clauses.append(f"{col_map[key]}=%s")
            values.append(val)
    if set_clauses:
        values.append(req_id)
        conn = get_db(); cursor = conn.cursor()
        cursor.execute(f"UPDATE faculty_requests SET {', '.join(set_clauses)} WHERE request_id=%s", values)
        conn.commit(); cursor.close(); conn.close()

def db_get_month_hours_used(email):
    """Get the total hours a faculty/HOD has used this month (sum of duration_hours).
    Rejected requests do NOT count toward the quota."""
    now = datetime.now()
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("""SELECT COALESCE(SUM(duration_hours), 0) FROM faculty_requests 
        WHERE faculty_email=%s AND MONTH(created_at)=%s AND YEAR(created_at)=%s
        AND status NOT IN ('Rejected', 'Rejected by HOD')""",
        (email, now.month, now.year))
    hours = cursor.fetchone()[0]
    cursor.close(); conn.close()
    return hours

# -----------------------
# DB HELPERS FOR LATE WARNINGS
# -----------------------

def db_get_warning_count(email):
    """Get the total number of late warnings for a faculty/HOD."""
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM late_warnings WHERE faculty_email=%s", (email,))
    count = cursor.fetchone()[0]
    cursor.close(); conn.close()
    return count

def db_insert_warning(faculty_email, faculty_name, department, request_id, slot, deadline, entry_time, minutes_late):
    """Insert a late warning record and return the new total warning count."""
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("""INSERT INTO late_warnings
        (faculty_email, faculty_name, department, request_id, slot, deadline, entry_time, minutes_late, notified_principal)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)""",
        (faculty_email, faculty_name, department, request_id, slot, deadline, entry_time, minutes_late))
    conn.commit()
    # Get total warning count
    cursor.execute("SELECT COUNT(*) FROM late_warnings WHERE faculty_email=%s", (faculty_email,))
    total = cursor.fetchone()[0]
    cursor.close(); conn.close()
    print(f"[WARNING] Late warning #{total} recorded for {faculty_name} ({faculty_email}) — {minutes_late} min late")
    return total

def db_get_all_warnings():
    """Get all late warnings from the database, newest first."""
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM late_warnings ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows

otps = {}  # {email: {"otp": str, "expires": float}}


def store_otp(email, otp):
    """Store OTP with 5-minute expiry."""
    otps[email] = {"otp": otp, "expires": _time.time() + 300}


def verify_otp_code(email, entered_otp):
    """Verify OTP and check expiry. Returns True if valid."""
    if email not in otps:
        return False
    record = otps[email]
    if _time.time() > record["expires"]:
        del otps[email]
        return False
    return record["otp"] == entered_otp


def clear_otp(email):
    """Remove OTP after successful use."""
    otps.pop(email, None)


def hash_pw(password):
    """Hash a password for storage."""
    return generate_password_hash(password)


def verify_pw(stored_hash, password):
    """Verify a password against its hash.
    Supports both hashed and legacy plain-text passwords for
    backward compatibility with existing database records."""
    if not stored_hash or not password:
        return False
    if isinstance(stored_hash, str) and stored_hash.startswith(('pbkdf2:', 'scrypt:')):
        return check_password_hash(stored_hash, password)
    return str(stored_hash) == str(password)


# Email config — uses environment variables (no hardcoded fallbacks for security)
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

# Keep backward-compatible aliases (all point to the same sender)
FACULTY_SENDER_EMAIL = SENDER_EMAIL
FACULTY_APP_PASSWORD = SENDER_PASSWORD
PRINCIPAL_SENDER_EMAIL = SENDER_EMAIL
PRINCIPAL_APP_PASSWORD = SENDER_PASSWORD
SECURITY_SENDER_EMAIL = SENDER_EMAIL
SECURITY_APP_PASSWORD = SENDER_PASSWORD
HOD_SENDER_EMAIL = SENDER_EMAIL
HOD_APP_PASSWORD = SENDER_PASSWORD
NOTIFICATION_SENDER_EMAIL = SENDER_EMAIL
NOTIFICATION_APP_PASSWORD = SENDER_PASSWORD


def send_email(to_email, subject, body):
    """Send an email using Gmail SMTP (port 587 + STARTTLS).
    If SMTP credentials are not configured, prints email to terminal (dev/testing mode)."""
    sender_email = os.environ.get("SENDER_EMAIL", SENDER_EMAIL)
    sender_password = os.environ.get("SENDER_PASSWORD", SENDER_PASSWORD)

    if not sender_email or not sender_password:
        print("\n" + "=" * 60)
        print(f"[DEV MODE EMAIL - NO SMTP CREDENTIALS SET]")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Content:\n{body}")
        print("=" * 60 + "\n")
        return True

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()
    return True


def db_get_email_template(template_name):
    """Fetch an email template from the database by its name."""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM email_templates WHERE template_name = %s", (template_name,))
        tpl = cursor.fetchone()
        cursor.close()
        conn.close()
        return tpl
    except Exception:
        return None


def render_email_template(template_name, replacements):
    """Fetch a template from DB and replace placeholder tags with actual values.
    Returns (subject, body) tuple. Falls back to simple strings if DB fails."""
    tpl = db_get_email_template(template_name)
    if tpl:
        subject = tpl["subject_template"]
        body = tpl["body_template"]
        for tag, value in replacements.items():
            subject = subject.replace(tag, str(value))
            body = body.replace(tag, str(value))
        return subject, body
    # Fallback if template not found
    return "Faculty Exit Notification", "\n".join(f"{k}: {v}" for k, v in replacements.items())


def send_hod_notification_email(faculty_name, department, description, slot, request_date):
    """Send an email notification to the HOD when a faculty submits an exit request."""
    try:
        # Look up the HOD for this department
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email, name FROM hods WHERE department = %s", (department,))
        hod = cursor.fetchone()
        cursor.close()
        conn.close()

        if not hod:
            print(f"[NOTIFY] No HOD found for department: {department}")
            return

        hod_email = hod["email"]
        hod_name = hod["name"]

        # Build the notification email from DB template
        replacements = {
            "[FacultyName]": faculty_name,
            "[Department]": department,
            "[Description]": description,
            "[Slot]": slot,
            "[Date]": str(request_date) if request_date else "Not specified",
            "[HODName]": hod_name,
        }
        subject, body = render_email_template("hod_notification", replacements)

        send_email(hod_email, subject, body)

        print(f"[NOTIFY] Email notification sent to HOD {hod_name} ({hod_email}) for request by {faculty_name}")

    except Exception as e:
        # Don't block the request submission if email fails
        print(f"[NOTIFY ERROR] Failed to send HOD notification email: {e}")


def send_principal_notification_email(faculty_name, department, description, slot, request_date, hod_name, hod_email):
    """Send an email notification to all Principals/Vice Principals when an HOD approves a faculty exit request."""
    try:
        # Look up all Principals from the database
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email, name FROM principal")
        principals = cursor.fetchall()
        cursor.close()
        conn.close()

        if not principals:
            print("[NOTIFY] No Principals found in database.")
            return

        for principal in principals:
            principal_email = principal["email"]
            principal_name = principal["name"]

            # Build the notification email from DB template
            replacements = {
                "[FacultyName]": faculty_name,
                "[Department]": department,
                "[Description]": description,
                "[Slot]": slot,
                "[Date]": str(request_date) if request_date else "Not specified",
                "[PrincipalName]": principal_name,
                "[ApprovedBy]": f"{hod_name} ({hod_email})",
            }
            subject, body = render_email_template("principal_notification", replacements)

            send_email(principal_email, subject, body)

            print(f"[NOTIFY] Email notification sent to Principal {principal_name} ({principal_email}) for HOD-approved request by {faculty_name}")

    except Exception as e:
        # Don't block the approval if email fails
        print(f"[NOTIFY ERROR] Failed to send Principal notification email: {e}")


def send_faculty_notification_email(faculty_email, faculty_name, department, slot, request_date, deadline):
    """Send an email notification to the Faculty when the Principal approves their exit request."""
    try:
        # Format deadline for display
        deadline_str = deadline.strftime("%d %B %Y, %I:%M %p") if deadline else "Not specified"

        # Build the notification email from DB template
        replacements = {
            "[FacultyName]": faculty_name,
            "[Department]": department,
            "[Slot]": slot,
            "[Date]": str(request_date) if request_date else "Not specified",
            "[Deadline]": deadline_str,
        }
        subject, body = render_email_template("faculty_approval", replacements)

        send_email(faculty_email, subject, body)

        print(f"[NOTIFY] Approval email sent to Faculty {faculty_name} ({faculty_email})")

    except Exception as e:
        # Don't block the approval if email fails
        print(f"[NOTIFY ERROR] Failed to send Faculty approval notification email: {e}")



def send_return_reminder_email(faculty_email, faculty_name, department, slot, request_date, deadline):
    """Send a reminder email to the Faculty/HOD 10 minutes before their deadline."""
    try:
        # Format deadline for display
        deadline_str = deadline.strftime("%d %B %Y, %I:%M %p") if deadline else "Not specified"

        # Build the notification email from DB template
        replacements = {
            "[FacultyName]": faculty_name,
            "[Department]": department,
            "[Slot]": slot,
            "[Date]": str(request_date) if request_date else "Not specified",
            "[Deadline]": deadline_str,
        }
        subject, body = render_email_template("return_reminder", replacements)

        send_email(faculty_email, subject, body)

        print(f"[REMINDER] Return reminder email sent to {faculty_name} ({faculty_email}) — deadline: {deadline_str}")

    except Exception as e:
        print(f"[REMINDER ERROR] Failed to send return reminder email to {faculty_email}: {e}")


def send_late_warning_email(faculty_name, department, slot, deadline, entry_time, minutes_late, total_warnings):
    """Send a late-return warning email to all Principals."""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email, name FROM principal")
        principals = cursor.fetchall()
        cursor.close(); conn.close()

        if not principals:
            print("[WARNING EMAIL] No Principals found in database.")
            return

        deadline_str = deadline.strftime("%d %B %Y, %I:%M %p") if deadline else "N/A"
        entry_str = entry_time.strftime("%d %B %Y, %I:%M %p") if entry_time else "N/A"

        for principal in principals:
            replacements = {
                "[FacultyName]": faculty_name,
                "[Department]": department,
                "[Slot]": slot or "N/A",
                "[Deadline]": deadline_str,
                "[EntryTime]": entry_str,
                "[MinutesLate]": str(minutes_late),
                "[TotalWarnings]": str(total_warnings),
                "[PrincipalName]": principal["name"],
            }
            subject, body = render_email_template("late_warning", replacements)

            send_email(principal["email"], subject, body)

            print(f"[WARNING EMAIL] Late warning sent to Principal {principal['name']} ({principal['email']}) for {faculty_name}")

    except Exception as e:
        print(f"[WARNING EMAIL ERROR] Failed to send late warning email: {e}")


def process_late_return(req, entry_time):
    """Check if entry is late and issue warning + email if so. Called at entry scan."""
    if not req.get("deadline"):
        return
    deadline = req["deadline"]
    if entry_time > deadline:
        minutes_late = int((entry_time - deadline).total_seconds() / 60)
        total = db_insert_warning(
            req["email"], req["name"], req["department"],
            req["id"], req.get("slot", ""), deadline, entry_time, minutes_late
        )
        # Mark request so we don't duplicate
        db_update_request(req["id"], {"warning_sent": 1})
        # Email principal in background
        threading.Thread(target=send_late_warning_email, args=(
            req["name"], req["department"], req.get("slot", ""),
            deadline, entry_time, minutes_late, total
        ), daemon=True).start()


# -----------------------
# BACKGROUND REMINDER SCHEDULER
# -----------------------
def reminder_scheduler():
    """Background thread that checks every 30 seconds for approved requests
    whose deadline is within 10 minutes, sends an email reminder, and marks
    the request so it is not re-sent."""
    print("[REMINDER] Background reminder scheduler started.")
    while True:
        try:
            now = datetime.now()
            reminder_window = now + timedelta(minutes=10)

            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            # Find approved requests where:
            #   - deadline is within the next 10 minutes (but not already past)
            #   - reminder has not been sent yet
            #   - the faculty hasn't already returned (entry_scan_time is NULL)
            cursor.execute("""
                SELECT * FROM faculty_requests
                WHERE status = 'Approved'
                  AND deadline IS NOT NULL
                  AND deadline > %s
                  AND deadline <= %s
                  AND reminder_sent = 0
                  AND entry_scan_time IS NULL
            """, (now, reminder_window))
            requests_to_remind = cursor.fetchall()
            cursor.close()
            conn.close()

            for req in requests_to_remind:
                send_return_reminder_email(
                    faculty_email=req["faculty_email"],
                    faculty_name=req["faculty_name"],
                    department=req["department"],
                    slot=req.get("slot", ""),
                    request_date=req.get("request_date"),
                    deadline=req["deadline"]
                )
                # Mark reminder as sent
                db_update_request(req["request_id"], {"reminder_sent": 1})

            if requests_to_remind:
                print(f"[REMINDER] Sent {len(requests_to_remind)} reminder(s).")

        except Exception as e:
            print(f"[REMINDER ERROR] Scheduler error: {e}")

        _time.sleep(30)  # Check every 30 seconds


# -----------------------
# BACKGROUND AUTO-RESET SCHEDULER
# -----------------------
def auto_reset_scheduler():
    """Background thread that checks once a minute whether today's day
    matches the configured monthly auto-reset day. If it does, it clears
    all exit requests and late_warnings. Uses a 'last_auto_reset' key
    to avoid resetting more than once on the same day."""
    print("[AUTO-RESET] Background auto-reset scheduler started.")
    while True:
        try:
            now = datetime.now()
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key='auto_reset_day'")
            row = cursor.fetchone()
            
            # Also check when we last reset to avoid duplicate resets on the same day
            cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key='last_auto_reset'")
            last_reset_row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row and row["setting_value"]:
                reset_day = int(row["setting_value"])
                today_str = now.strftime("%Y-%m-%d")
                already_reset = (last_reset_row and last_reset_row["setting_value"] == today_str)

                if now.day == reset_day and not already_reset:
                    # Perform the reset
                    conn2 = get_db()
                    cursor2 = conn2.cursor()
                    cursor2.execute("DELETE FROM faculty_requests")
                    cursor2.execute("DELETE FROM late_warnings")
                    # Mark that we've already reset today
                    cursor2.execute("""
                        INSERT INTO system_settings (setting_key, setting_value)
                        VALUES ('last_auto_reset', %s)
                        ON DUPLICATE KEY UPDATE setting_value = %s
                    """, (today_str, today_str))
                    conn2.commit()
                    cursor2.close()
                    conn2.close()
                    print(f"[AUTO-RESET] Monthly reset completed on {today_str} (day {reset_day}).")
        except Exception as e:
            print(f"[AUTO-RESET ERROR] {e}")

        _time.sleep(60)  # Check every 60 seconds


# Start the reminder scheduler in a daemon thread
# Guard against Flask debug reloader spawning duplicate threads
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    _reminder_thread = threading.Thread(target=reminder_scheduler, daemon=True)
    _reminder_thread.start()
    _auto_reset_thread = threading.Thread(target=auto_reset_scheduler, daemon=True)
    _auto_reset_thread.start()

# -----------------------
# ERROR HANDLERS
# -----------------------
@app.errorhandler(500)
def internal_error(error):
    """Log the actual error and show a user-friendly page."""
    import traceback
    print(f"[500 ERROR] {error}")
    traceback.print_exc()
    return render_template("500.html") if os.path.exists(os.path.join(app.root_path, "templates", "500.html")) else (
        f"<h1>Something went wrong</h1><p>The server encountered an error. Please try again later.</p><p><a href='/'>Go Home</a></p>", 500
    )


@app.errorhandler(404)
def page_not_found(error):
    """Show a user-friendly 404 page."""
    return f"<h1>Page Not Found</h1><p>The page you are looking for does not exist.</p><p><a href='/'>Go Home</a></p>", 404


# -----------------------
# HOME
# -----------------------
@app.route("/")
def home():
    # Auto-redirect logged-in users to their dashboard
    if session.get("principal"):
        return redirect("/principal_dashboard")
    if session.get("hod"):
        return redirect("/hod_dashboard")
    if session.get("faculty_email"):
        return redirect("/faculty_dashboard")
    if session.get("security"):
        return redirect("/security_dashboard")

    # Show intro video on first visit; skip if already seen this session
    # or if redirected back after intro completes (?skip_intro=1)
    if request.args.get("skip_intro") == "1":
        session["intro_seen"] = True

    if not session.get("intro_seen"):
        return render_template("intro.html")

    return render_template("main.html")


# =======================
# LOGIN ROUTES
# =======================

@app.route("/principal_login", methods=["GET", "POST"])
def principal_login():
    # If already logged in on GET request, go to dashboard
    if request.method == "GET" and session.get("principal"):
        return redirect("/principal_dashboard")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = db_get_user("principal", email)
        if not user:
            return render_template("principal_login.html", error="Wrong Email")
        elif not verify_pw(user["password"], password):
            return render_template("principal_login.html", error="Wrong Password")
        else:
            session.permanent = True
            session["principal"] = True
            session["principal_email"] = email
            return redirect("/principal_dashboard")
    return render_template("principal_login.html")


@app.route("/principal_forgot_password", methods=["GET", "POST"])
def principal_forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        if db_get_user("principal", email):
            otp = str(random.randint(100000, 999999))
            store_otp(email, otp)
            
            try:
                send_email(email, 'Principal Password Reset OTP', f'Your password reset OTP is: {otp}')
                session["principal_reset_email"] = email
                return redirect("/principal_verify_otp")
            except Exception as e:
                return render_template("forgot_password.html", error=f"Failed to send email. Error: {e}")
        else:
            return render_template("forgot_password.html", error="Email not found.")
            
    return render_template("forgot_password.html")


@app.route("/principal_verify_otp", methods=["GET", "POST"])
def principal_verify_otp():
    if "principal_reset_email" not in session:
        return redirect("/principal_login")
        
    email = session["principal_reset_email"]
    
    if request.method == "POST":
        otp_entered = request.form.get("otp")
        new_password = request.form.get("new_password")
        
        if verify_otp_code(email, otp_entered):
            db_update_password("principal", email, hash_pw(new_password))
            clear_otp(email)
            session.pop("principal_reset_email", None)
            return redirect("/principal_login")
        else:
            return render_template("verify_otp.html", error="Invalid OTP", email=email)
            
    return render_template("verify_otp.html", email=email)


@app.route("/security_login", methods=["GET", "POST"])
def security_login():
    # If already logged in on GET request, go to dashboard
    if request.method == "GET" and session.get("security"):
        return redirect("/security_dashboard")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = db_get_user("security", email)
        if not user:
            return render_template("security_login.html", error="Wrong Email")
        elif not verify_pw(user["password"], password):
            return render_template("security_login.html", error="Wrong Password")
        else:
            session.permanent = True
            session["security"] = True
            session["security_email"] = email
            return redirect("/security_dashboard")
    return render_template("security_login.html")


@app.route("/security_forgot_password", methods=["GET", "POST"])
def security_forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        if db_get_user("security", email):
            otp = str(random.randint(100000, 999999))
            store_otp(email, otp)
            
            try:
                send_email(email, 'Security Password Reset OTP', f'Your password reset OTP is: {otp}')
                session["security_reset_email"] = email
                return redirect("/security_verify_otp")
            except Exception as e:
                return render_template("forgot_password.html", error=f"Failed to send email. Error: {e}")
        else:
            return render_template("forgot_password.html", error="Email not found.")
            
    return render_template("forgot_password.html")


@app.route("/security_verify_otp", methods=["GET", "POST"])
def security_verify_otp():
    if "security_reset_email" not in session:
        return redirect("/security_login")
        
    email = session["security_reset_email"]
    
    if request.method == "POST":
        otp_entered = request.form.get("otp")
        new_password = request.form.get("new_password")
        
        if verify_otp_code(email, otp_entered):
            db_update_password("security", email, hash_pw(new_password))
            clear_otp(email)
            session.pop("security_reset_email", None)
            return redirect("/security_login")
        else:
            return render_template("verify_otp.html", error="Invalid OTP", email=email)
            
    return render_template("verify_otp.html", email=email)


@app.route("/faculty_login", methods=["GET","POST"])
def faculty_login():
    # If already logged in on GET request, go to dashboard
    if request.method == "GET" and session.get("faculty_email"):
        return redirect("/faculty_dashboard")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db_get_user("faculty", email)
        if not user:
            return render_template("faculty_login.html", error="Wrong Email")
        elif not verify_pw(user["password"], password):
            return render_template("faculty_login.html", error="Wrong Password")
        else:
            session.permanent = True
            session["faculty_email"] = email
            session["faculty_name"] = user["name"]
            session["department"] = user["department"]
            session["faculty_designation"] = user.get("designation", "")
            return redirect("/faculty_dashboard")

    return render_template("faculty_login.html")


# =======================
# HOD LOGIN ROUTES
# =======================

@app.route("/hod_login", methods=["GET", "POST"])
def hod_login():
    # If already logged in on GET request, go to dashboard
    if request.method == "GET" and session.get("hod"):
        return redirect("/hod_dashboard")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = db_get_user("hods", email)
        if not user:
            return render_template("hod_login.html", error="Wrong Email")
        elif not verify_pw(user["password"], password):
            return render_template("hod_login.html", error="Wrong Password")
        else:
            session.permanent = True
            session["hod"] = True
            session["hod_email"] = email
            session["hod_department"] = user["department"]
            return redirect("/hod_dashboard")
    return render_template("hod_login.html")


@app.route("/hod_forgot_password", methods=["GET", "POST"])
def hod_forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        if db_get_user("hods", email):
            otp = str(random.randint(100000, 999999))
            store_otp(email, otp)
            
            try:
                send_email(email, 'HOD Password Reset OTP', f'Your HOD password reset OTP is: {otp}')
                session["hod_reset_email"] = email
                return redirect("/hod_verify_otp")
            except Exception as e:
                return render_template("forgot_password.html", error=f"Failed to send email. Error: {e}")
        else:
            return render_template("forgot_password.html", error="Email not found.")
            
    return render_template("forgot_password.html")


@app.route("/hod_verify_otp", methods=["GET", "POST"])
def hod_verify_otp():
    if "hod_reset_email" not in session:
        return redirect("/hod_login")
        
    email = session["hod_reset_email"]
    
    if request.method == "POST":
        otp_entered = request.form.get("otp")
        new_password = request.form.get("new_password")
        
        if verify_otp_code(email, otp_entered):
            db_update_password("hods", email, hash_pw(new_password))
            clear_otp(email)
            session.pop("hod_reset_email", None)
            return redirect("/hod_login")
        else:
            return render_template("verify_otp.html", error="Invalid OTP", email=email)
            
    return render_template("verify_otp.html", email=email)


# -----------------------
# FORGOT PASSWORD
# -----------------------
@app.route("/faculty_forgot_password", methods=["GET", "POST"])
def faculty_forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        if db_get_user("faculty", email):
            otp = str(random.randint(100000, 999999))
            store_otp(email, otp)
            
            try:
                send_email(email, 'Password Reset OTP', f'Your password reset OTP is: {otp}')
                session["reset_email"] = email
                return redirect("/verify_otp")
            except Exception as e:
                return render_template("forgot_password.html", error=f"Failed to send email. Error: {e}")
        else:
            return render_template("forgot_password.html", error="Email not found.")
            
    return render_template("forgot_password.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "reset_email" not in session:
        return redirect("/faculty_login")
        
    email = session["reset_email"]
    
    if request.method == "POST":
        otp_entered = request.form["otp"]
        new_password = request.form["new_password"]
        
        if verify_otp_code(email, otp_entered):
            db_update_password("faculty", email, hash_pw(new_password))
            clear_otp(email)
            session.pop("reset_email", None)
            return redirect("/faculty_login")
        else:
            return render_template("verify_otp.html", error="Invalid OTP", email=email)
            
    return render_template("verify_otp.html", email=email)



# -----------------------
# FACULTY DASHBOARD
# -----------------------
@app.route("/faculty_dashboard", methods=["GET","POST"])
def faculty_dashboard():

    email = session.get("faculty_email")
    dept = session.get("department")
    name = session.get("faculty_name", "Faculty")
    designation = session.get("faculty_designation", "")

    if not email:
        return redirect("/faculty_login")

    hours_used = db_get_month_hours_used(email)
    hours_remaining = max(0, 3 - hours_used)
    banned = hours_remaining <= 0  # Limit: 3 hours per month

    if request.method == "POST":

        if banned:
            return render_template(
                "faculty_dashboard.html",
                hours_used=hours_used,
                hours_remaining=0,
                banned=True,
                department=dept,
                name=name,
                designation=designation
            )

        name = request.form["name"]
        desc = request.form["description"]
        out_time = request.form.get("out_time", "")
        duration_hours = int(request.form.get("duration_hours", 1))
        request_date = request.form.get("request_date")
        proof_filename = save_photo(request.files, "proof")

        # Validate duration doesn't exceed remaining hours
        if duration_hours > hours_remaining:
            flash(f"You only have {hours_remaining} hour(s) remaining this month.")
            return redirect("/faculty_dashboard")

        # Validate college hours and past time
        now = datetime.now()
        req_date_obj = datetime.strptime(request_date, "%Y-%m-%d").date() if request_date else now.date()
        try:
            out_time_dt = datetime.strptime(out_time, "%H:%M")
            total_mins = out_time_dt.hour * 60 + out_time_dt.minute
            
            if total_mins < 480:
                flash("Out time must be after 8:00 AM (college hours).")
                return redirect("/faculty_dashboard")
                
            if total_mins + (duration_hours * 60) > 960:
                flash("Must return by 4:00 PM (college hours).")
                return redirect("/faculty_dashboard")
                
            if req_date_obj == now.date():
                if total_mins < (now.hour * 60 + now.minute):
                    flash("For today, you cannot select a past time.")
                    return redirect("/faculty_dashboard")
        except ValueError:
            pass

        # Convert out_time to 12-hour format for the slot string
        try:
            out_time_dt = datetime.strptime(out_time, "%H:%M")
            out_time_12h = out_time_dt.strftime("%I:%M %p").lstrip("0")
        except:
            out_time_12h = out_time

        # Build slot string from out_time and duration
        slot = f"{out_time_12h} ({duration_hours}h)"

        # NEW WORKFLOW: Faculty request goes to HOD first (status = "Pending HOD")
        req_data = {
            "id": str(uuid.uuid4())[:8],  # short id
            "name": name,
            "email": email,
            "department": dept,
            "description": desc,
            "slot": slot,
            "duration_hours": duration_hours,
            "status": "Pending HOD",
            "proof": proof_filename,
            "request_date": request_date
        }
        db_insert_request(req_data)

        # Send email notification to the HOD of this department (async)
        threading.Thread(target=send_hod_notification_email, args=(name, dept, desc, slot, request_date), daemon=True).start()

        return redirect("/faculty_dashboard")

    # Re-fetch hours after potential POST
    hours_used = db_get_month_hours_used(email)
    hours_remaining = max(0, 3 - hours_used)
    banned = hours_remaining <= 0  # Limit: 3 hours per month

    # Fetch photo for dashboard
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT photo FROM faculty WHERE email=%s", (email,))
    user_db = cursor.fetchone()
    cursor.close()
    conn.close()
    photo = user_db["photo"] if user_db else None

    # 🔥 SEND DEADLINE ONLY AFTER APPROVAL
    deadline = None
    pass_generated = False
    qr_code = ""
    qr_code_entry = ""
    last = None

    # Find the latest request from this faculty (from DB)
    all_requests = db_get_all_requests()
    for req in all_requests:
        if req["email"] == email:
            last = req
            break

    slot_start = None
    if last and last["status"] == "Approved" and not is_pass_expired(last):
        deadline = last["deadline"].strftime("%Y-%m-%dT%H:%M:%S") if last["deadline"] else None
        pass_generated = True
        qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=EXIT-{last['id']}"
        qr_code_entry = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ENTRY-{last['id']}"

        # Calculate slot start time using the robust parser
        slot_start_dt = parse_slot_start(last.get("slot", ""), last.get("request_date"))
        if slot_start_dt:
            slot_start = slot_start_dt.strftime("%Y-%m-%dT%H:%M:%S")
            print(f"[DEBUG] Faculty slot_start = {slot_start}, deadline = {deadline}")
        else:
            print(f"[DEBUG] Faculty slot_start could not be parsed from slot='{last.get('slot')}', date='{last.get('request_date')}'")

    warning_count = db_get_warning_count(email)

    return render_template(
        "faculty_dashboard.html",
        hours_used=hours_used,
        hours_remaining=hours_remaining,
        banned=banned,
        department=dept,
        name=name,
        designation=designation,
        deadline=deadline,
        slot_start=slot_start,
        pass_generated=pass_generated,
        qr_code=qr_code,
        qr_code_entry=qr_code_entry if pass_generated else "",
        photo=photo,
        status=(last["status"] if last else None),
        rejection_reason=last.get("rejection_reason") if last else None,
        exit_scan_time=last.get("exit_scan_time") if last else None,
        entry_scan_time=last.get("entry_scan_time") if last else None,
        warning_count=warning_count
    )

@app.route("/upload_profile_photo", methods=["POST"])
def upload_profile_photo():
    email = session.get("faculty_email")
    if not email:
        return redirect("/faculty_login")
        
    try:
        photo = save_photo(request.files, "photo")
        if photo:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE faculty SET photo=%s WHERE email=%s", (photo, email))
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error uploading photo: {e}")
        
    return redirect("/faculty_dashboard")

@app.route("/faculty_history")
def faculty_history():
    email = session.get("faculty_email")
    if not email:
        return redirect("/faculty_login")

    all_requests = db_get_all_requests()
    faculty_requests = [req for req in all_requests if req["email"] == email]
    
    for req in faculty_requests:
        req["start_time"] = req["created_at"]

    return render_template("faculty_history.html", requests=faculty_requests)

@app.route("/download_pass")
def download_pass():
    import qrcode
    import io
    from flask import send_file
    
    email = session.get("faculty_email")
    if not email:
        email = session.get("hod_email")
        if not email:
            return redirect("/")

    # Get the latest approved request
    all_requests = db_get_all_requests()
    last = None
    for req in all_requests:
        if req["email"] == email:
            last = req
            break

    if not last or last["status"] != "Approved" or is_pass_expired(last):
        return "Pass expired or no approved pass available", 404

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"EXIT-{last['id']}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = io.BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f"exit_pass_{last['id']}.png")

@app.route("/download_entry_pass")
def download_entry_pass():
    import qrcode
    import io
    from flask import send_file
    
    email = session.get("faculty_email")
    if not email:
        email = session.get("hod_email")
        if not email:
            return redirect("/")

    all_requests = db_get_all_requests()
    last = None
    for req in all_requests:
        if req["email"] == email:
            last = req
            break

    if not last or last["status"] != "Approved" or is_pass_expired(last):
        return "Pass expired or no approved pass available", 404

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"ENTRY-{last['id']}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = io.BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f"entry_pass_{last['id']}.png")

# -----------------------
# HOD DASHBOARD
# -----------------------
@app.route("/hod_dashboard", methods=["GET", "POST"])
def hod_dashboard():

    if not session.get("hod"):
        return redirect("/hod_login")

    hod_dept = session.get("hod_department", "Unknown")
    hod_email = session.get("hod_email", "")

    # Get HOD name from DB
    hod_user = db_get_user("hods", hod_email)
    hod_name = hod_user["name"] if hod_user else "HOD"

    # Check HOD's own monthly request count
    hod_hours_used = db_get_month_hours_used(hod_email)
    hod_hours_remaining = max(0, 3 - hod_hours_used)
    hod_banned = hod_hours_remaining <= 0  # Limit: 3 hours per month

    # Handle HOD's own exit request submission
    if request.method == "POST":
        if not hod_banned:
            desc = request.form.get("description", "")
            out_time = request.form.get("out_time", "")
            duration_hours = int(request.form.get("duration_hours", 1))
            request_date = request.form.get("request_date")
            proof_filename = save_photo(request.files, "proof")

            # Validate duration doesn't exceed remaining hours
            if duration_hours > hod_hours_remaining:
                flash(f"You only have {hod_hours_remaining} hour(s) remaining this month.")
                return redirect("/hod_dashboard")

            # Validate college hours and past time
            now = datetime.now()
            req_date_obj = datetime.strptime(request_date, "%Y-%m-%d").date() if request_date else now.date()
            try:
                out_time_dt = datetime.strptime(out_time, "%H:%M")
                total_mins = out_time_dt.hour * 60 + out_time_dt.minute
                
                if total_mins < 480:
                    flash("Out time must be after 8:00 AM (college hours).")
                    return redirect("/hod_dashboard")
                    
                if total_mins + (duration_hours * 60) > 960:
                    flash("Must return by 4:00 PM (college hours).")
                    return redirect("/hod_dashboard")
                    
                if req_date_obj == now.date():
                    if total_mins < (now.hour * 60 + now.minute):
                        flash("For today, you cannot select a past time.")
                        return redirect("/hod_dashboard")
            except ValueError:
                pass

            # Convert out_time to 12-hour format for the slot string
            try:
                out_time_dt = datetime.strptime(out_time, "%H:%M")
                out_time_12h = out_time_dt.strftime("%I:%M %p").lstrip("0")
            except:
                out_time_12h = out_time

            # Build slot string from out_time and duration
            slot = f"{out_time_12h} ({duration_hours}h)"

            req_data = {
                "id": str(uuid.uuid4())[:8],
                "name": hod_name,
                "email": hod_email,
                "department": hod_dept,
                "description": desc,
                "slot": slot,
                "duration_hours": duration_hours,
                "status": "Pending Principal",  # Skip HOD approval
                "proof": proof_filename,
                "request_date": request_date
            }
            db_insert_request(req_data)

            # Auto-set HOD approved fields
            db_update_request(req_data["id"], {
                "hod_approved_by": hod_email + " (Self - HOD)",
                "hod_approved_at": datetime.now()
            })

        return redirect("/hod_dashboard")

    # Re-fetch hours after potential POST
    hod_hours_used = db_get_month_hours_used(hod_email)
    hod_hours_remaining = max(0, 3 - hod_hours_used)
    hod_banned = hod_hours_remaining <= 0  # Limit: 3 hours per month

    # Get all requests for this HOD's department
    all_requests = db_get_all_requests()
    dept_requests = [r for r in all_requests if r["department"] == hod_dept]

    # Find the first pending HOD request to show as the main card
    data = None
    for r in dept_requests:
        if r["status"] == "Pending HOD":
            data = r
            break

    # Find HOD's own latest request for timer/QR
    hod_deadline = None
    hod_slot_start = None
    hod_pass_generated = False
    hod_qr_code = ""
    hod_last = None
    hod_status = None

    for req in all_requests:
        if req["email"] == hod_email:
            hod_last = req
            break

    hod_qr_code_entry = ""
    if hod_last and hod_last["status"] == "Approved" and not is_pass_expired(hod_last):
        hod_deadline = hod_last["deadline"].strftime("%Y-%m-%d %H:%M:%S") if hod_last["deadline"] else None
        hod_pass_generated = True
        hod_qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=EXIT-{hod_last['id']}"
        hod_qr_code_entry = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ENTRY-{hod_last['id']}"
        hod_status = "Approved"

        # Calculate slot start time using the robust parser
        hod_slot_start_dt = parse_slot_start(hod_last.get("slot", ""), hod_last.get("request_date"))
        if hod_slot_start_dt:
            hod_slot_start = hod_slot_start_dt.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[DEBUG] HOD slot_start = {hod_slot_start}, deadline = {hod_deadline}")
        else:
            print(f"[DEBUG] HOD slot_start could not be parsed from slot='{hod_last.get('slot')}', date='{hod_last.get('request_date')}'")
    elif hod_last:
        hod_status = hod_last["status"]

    warning_count = db_get_warning_count(hod_email)

    return render_template(
        "hod_dashboard.html",
        data=data,
        pending_requests=dept_requests,
        hod_department=hod_dept,
        hod_name=hod_name,
        hod_hours_used=hod_hours_used,
        hod_hours_remaining=hod_hours_remaining,
        hod_banned=hod_banned,
        hod_deadline=hod_deadline,
        hod_slot_start=hod_slot_start,
        hod_pass_generated=hod_pass_generated,
        hod_qr_code=hod_qr_code,
        hod_qr_code_entry=hod_qr_code_entry if hod_pass_generated else "",
        hod_status=hod_status,
        hod_exit_scan_time=hod_last.get("exit_scan_time") if hod_last else None,
        hod_entry_scan_time=hod_last.get("entry_scan_time") if hod_last else None,
        hod_rejection_reason=hod_last.get("rejection_reason") if hod_last else None,
        warning_count=warning_count
    )


# -----------------------
# HOD VIEW SPECIFIC REQUEST
# -----------------------
@app.route("/hod_view_request/<req_id>")
def hod_view_request(req_id):

    if not session.get("hod"):
        return redirect("/hod_login")

    hod_dept = session.get("hod_department", "Unknown")

    # Find the specific request
    all_requests = db_get_all_requests()
    data = None
    for r in all_requests:
        if r["id"] == req_id and r["department"] == hod_dept:
            data = r
            break

    dept_requests = [r for r in all_requests if r["department"] == hod_dept]

    # Re-calculate all context needed for the dashboard
    hod_email = session.get("hod_email", "")
    hod_user = db_get_user("hods", hod_email)
    hod_name = hod_user["name"] if hod_user else "HOD"
    hod_hours_used = db_get_month_hours_used(hod_email)
    hod_hours_remaining = max(0, 3 - hod_hours_used)
    
    hod_deadline = None
    hod_slot_start = None
    hod_pass_generated = False
    hod_qr_code = ""
    hod_qr_code_entry = ""
    hod_last = None
    hod_status = None

    for req in all_requests:
        if req["email"] == hod_email:
            hod_last = req
            break

    if hod_last and hod_last["status"] == "Approved":
        hod_deadline = hod_last["deadline"].strftime("%Y-%m-%dT%H:%M:%S") if hod_last["deadline"] else None
        hod_pass_generated = True
        hod_qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=EXIT-{hod_last['id']}"
        hod_qr_code_entry = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ENTRY-{hod_last['id']}"
        hod_status = "Approved"
        # Calculate slot start time using the robust parser
        hod_slot_start_dt = parse_slot_start(hod_last.get("slot", ""), hod_last.get("request_date"))
        if hod_slot_start_dt:
            hod_slot_start = hod_slot_start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    elif hod_last:
        hod_status = hod_last["status"]

    hod_qr_code_entry = hod_qr_code_entry if hod_pass_generated else ""

    warning_count = db_get_warning_count(hod_email)

    return render_template(
        "hod_dashboard.html",
        data=data,
        pending_requests=dept_requests,
        hod_department=hod_dept,
        hod_name=hod_name,
        hod_hours_used=hod_hours_used,
        hod_hours_remaining=hod_hours_remaining,
        hod_banned=hod_hours_remaining <= 0,
        hod_deadline=hod_deadline,
        hod_slot_start=hod_slot_start,
        hod_pass_generated=hod_pass_generated,
        hod_qr_code=hod_qr_code,
        hod_qr_code_entry=hod_qr_code_entry,
        hod_status=hod_status,
        hod_exit_scan_time=hod_last.get("exit_scan_time") if hod_last else None,
        hod_entry_scan_time=hod_last.get("entry_scan_time") if hod_last else None,
        hod_rejection_reason=hod_last.get("rejection_reason") if hod_last else None,
        warning_count=warning_count
    )


# -----------------------
# HOD APPROVE (Forward to Principal)
# -----------------------
@app.route("/hod_approve/<req_id>")
def hod_approve(req_id):

    if not session.get("hod"):
        return redirect("/hod_login")

    db_update_request(req_id, {
        "status": "Pending Principal",
        "hod_approved_by": session.get("hod_email"),
        "hod_approved_at": datetime.now()
    })

    # Fetch request details and send notification to Principal
    all_requests = db_get_all_requests()
    req = None
    for r in all_requests:
        if r["id"] == req_id:
            req = r
            break

    if req:
        hod_email = session.get("hod_email", "")
        hod_user = db_get_user("hods", hod_email)
        hod_name = hod_user["name"] if hod_user else "HOD"
        # Send notification to Principal (async)
        threading.Thread(target=send_principal_notification_email, args=(
            req["name"], req["department"], req["description"],
            req["slot"], req.get("request_date"), hod_name, hod_email
        ), daemon=True).start()

    return redirect("/hod_dashboard")


# -----------------------
# HOD DECLINE
# -----------------------
@app.route("/hod_decline/<req_id>", methods=["POST"])
def hod_decline(req_id):

    if not session.get("hod"):
        return redirect("/hod_login")

    reason = request.form.get("rejection_reason", "").strip()
    if not reason:
        reason = "No reason provided"

    db_update_request(req_id, {"status": "Rejected by HOD", "rejection_reason": reason})

    return redirect("/hod_dashboard")


# -----------------------
# PRINCIPAL DASHBOARD
# -----------------------
def generate_ai_summary(description):
    if not description:
        return "No description provided."
        
    desc = description.lower()
    
    # 1. Identify Reason
    reason = "personal matters"
    if any(word in desc for word in ["hospital", "medical", "health", "doctor", "sick", "illness", "treatment"]):
        reason = "a medical emergency/health issue"
    elif any(word in desc for word in ["wedding", "ceremony", "marriage", "function"]):
        reason = "a family function/wedding"
    elif any(word in desc for word in ["bank", "financial", "transaction"]):
        reason = "time-sensitive bank work"
    elif any(word in desc for word in ["government", "office", "documentation", "verification"]):
        reason = "official government work/documentation"
    elif any(word in desc for word in ["legal", "property", "court"]):
        reason = "legal or property-related matters"
    elif any(word in desc for word in ["vehicle", "mechanic", "repair", "service center"]):
        reason = "vehicle repair/maintenance"
    elif any(word in desc for word in ["certification", "program", "training"]):
        reason = "an external certification program"
    elif any(word in desc for word in ["meeting", "academic", "coordination"]):
        reason = "an external academic/administrative meeting"
    elif any(word in desc for word in ["examination", "duty", "center"]):
        reason = "official examination duty at another center"
    elif any(word in desc for word in ["submit", "submission", "deadline", "document"]):
        reason = "time-sensitive document submission"
    elif any(word in desc for word in ["family", "relative", "home"]):
        reason = "urgent family responsibilities"
    elif any(word in desc for word in ["personal", "private"]):
        reason = "an urgent personal situation"

    # 2. Identify Urgency
    urgency = "Standard request."
    if any(word in desc for word in ["urgent", "emergency", "immediately", "earliest"]):
        urgency = "Urgent request requiring immediate attention."

    # 3. Identify Work Management
    work_status = "Faculty will resume duties upon return."
    if any(word in desc for word in ["managed", "planned", "arranged", "no disruption"]):
        work_status = "Academic responsibilities have been managed to avoid disruption."
        
    return f"Faculty is requesting an exit for {reason}. {urgency} {work_status}"

@app.route("/principal_dashboard")
def principal_dashboard():

    if not session.get("principal"):
        return redirect("/principal_login")

    all_requests = db_get_all_requests()

    # Principal no longer auto-sees the first pending request on load.
    # They must click REQUESTS -> Department to view them.
    data = None

    # Get pending requests for the sidebar
    pending_list = [r for r in all_requests if r["status"] == "Pending Principal"]

    ai_summary_text = "No request selected."

    # Calculate department-wise PENDING request counts for REQUESTS button
    pending_dept_counts = {}
    for r in pending_list:
        dept = r.get("department", "Unknown")
        pending_dept_counts[dept] = pending_dept_counts.get(dept, 0) + 1

        # Check urgency
        slot_start_dt = parse_slot_start(r.get("slot", ""), r.get("request_date"))
        r["is_urgent"] = False
        if slot_start_dt and r.get("created_at"):
            if isinstance(r["created_at"], str):
                created_at_dt = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S")
            else:
                created_at_dt = r["created_at"]
            
            # Urgent if requested within 1 hour of slot start
            diff = slot_start_dt - created_at_dt
            if timedelta(0) <= diff <= timedelta(hours=1):
                r["is_urgent"] = True

    # If no specific data is selected, show the first urgent request on load
    if not data:
        for r in pending_list:
            if r.get("is_urgent"):
                data = r
                break
                
    if data and "description" in data:
        ai_summary_text = generate_ai_summary(data["description"])

    # Calculate department-wise ALL request counts for Manage Requests view
    dept_counts = {}
    for r in all_requests:
        dept = r.get("department", "Unknown")
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    # Fetch scheduled auto-reset day (of the month)
    auto_reset_date = None
    try:
        conn_s = get_db()
        cursor_s = conn_s.cursor(dictionary=True)
        cursor_s.execute("SELECT setting_value FROM system_settings WHERE setting_key='auto_reset_day'")
        row_s = cursor_s.fetchone()
        if row_s and row_s["setting_value"]:
            auto_reset_date = row_s["setting_value"]
        cursor_s.close()
        conn_s.close()
    except:
        pass

    return render_template(
        "principal_dashboard.html", 
        data=data, 
        pending_requests=pending_list,
        ai_summary=ai_summary_text,
        all_requests=all_requests,
        dept_counts=dept_counts,
        total_requests=len(all_requests),
        pending_dept_counts=pending_dept_counts,
        total_pending=len(pending_list),
        auto_reset_date=auto_reset_date
    )

# -----------------------
# PRINCIPAL RESET & AUTO-RESET ROUTES
# -----------------------

@app.route("/reset_all_requests", methods=["POST"])
def reset_all_requests():
    if not session.get("principal"):
        return redirect("/principal_login")

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM faculty_requests")
        cursor.execute("DELETE FROM late_warnings")
        conn.commit()
        cursor.close()
        conn.close()
        flash("All exit requests and warnings have been reset successfully!")
    except Exception as e:
        flash(f"Reset failed: {e}")

    return redirect("/principal_dashboard")


@app.route("/set_auto_reset", methods=["POST"])
def set_auto_reset():
    if not session.get("principal"):
        return redirect("/principal_login")

    reset_day = request.form.get("auto_reset_day", "")
    try:
        day = int(reset_day)
        if day < 1 or day > 31:
            raise ValueError
    except (ValueError, TypeError):
        flash("Please enter a valid day (1-31).")
        return redirect("/principal_dashboard")

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_settings (setting_key, setting_value)
            VALUES ('auto_reset_day', %s)
            ON DUPLICATE KEY UPDATE setting_value = %s
        """, (str(day), str(day)))
        conn.commit()
        cursor.close()
        conn.close()
        flash(f"Monthly auto-reset set for the {day}{'st' if day == 1 else 'nd' if day == 2 else 'rd' if day == 3 else 'th'} of every month.")
    except Exception as e:
        flash(f"Failed to set auto-reset: {e}")

    return redirect("/principal_dashboard")


@app.route("/cancel_auto_reset", methods=["POST"])
def cancel_auto_reset():
    if not session.get("principal"):
        return redirect("/principal_login")

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM system_settings WHERE setting_key='auto_reset_day'")
        conn.commit()
        cursor.close()
        conn.close()
        flash("Monthly auto-reset has been cancelled.")
    except Exception as e:
        flash(f"Failed to cancel: {e}")

    return redirect("/principal_dashboard")


# -----------------------
# PRINCIPAL MANAGEMENT ROUTES
# -----------------------

@app.route("/manage_principals")
def manage_principals():
    if not session.get("principal"):
        return redirect("/principal_login")
        
    principals = db_get_all("principal")
    return render_template("manage_principals.html", principals=principals)

@app.route("/add_principal", methods=["POST"])
def add_principal():
    if not session.get("principal"):
        return redirect("/principal_login")
        
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    phone = request.form.get("phone", "")
    
    # Check if email already exists
    existing = db_get_user("principal", email)
    if existing:
        principals = db_get_all("principal")
        return render_template("manage_principals.html", principals=principals, error=f"Email '{email}' is already in use.")
        
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO principal (name, email, password, phone)
            VALUES (%s, %s, %s, %s)
        """, (name, email, hash_pw(password), phone))
        conn.commit()
        cursor.close()
        conn.close()
        
        principals = db_get_all("principal")
        return render_template("manage_principals.html", principals=principals, success=f"Successfully added {name}.")
    except Exception as e:
        principals = db_get_all("principal")
        return render_template("manage_principals.html", principals=principals, error=f"Database error: {e}")

@app.route("/delete_principal/<int:pid>")
def delete_principal(pid):
    if not session.get("principal"):
        return redirect("/principal_login")
        
    # Prevent self-deletion
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email FROM principal WHERE id = %s", (pid,))
        user = cursor.fetchone()
        
        if user and user["email"] == session.get("principal_email"):
            cursor.close()
            conn.close()
            principals = db_get_all("principal")
            return render_template("manage_principals.html", principals=principals, error="You cannot remove your own account.")
            
        cursor.execute("DELETE FROM principal WHERE id = %s", (pid,))
        conn.commit()
        cursor.close()
        conn.close()
        
        principals = db_get_all("principal")
        return render_template("manage_principals.html", principals=principals, success="Account removed successfully.")
    except Exception as e:
        principals = db_get_all("principal")
        return render_template("manage_principals.html", principals=principals, error=f"Database error: {e}")


# -----------------------
# USER MANAGEMENT ROUTES
# -----------------------

@app.route("/manage/<user_type>")
def manage_users(user_type):
    if session.get("principal"):
        role = "Principal"
        back_url = "/principal_dashboard"
    elif session.get("hod"):
        role = "HOD"
        back_url = "/hod_dashboard"
        if user_type != "faculty": return redirect("/hod_dashboard")
    else:
        return redirect("/")

    table_map = {"hods": "hods", "faculty": "faculty", "security": "security"}
    table = table_map.get(user_type)
    if not table: return redirect(back_url)
    
    where = ""
    params = ()
    if role == "HOD":
        where = "department = %s"
        params = (session.get("hod_department"),)
    
    users = db_get_all(table, where, params)
    
    return render_template("manage_users.html", 
        manager_role=role,
        back_url=back_url,
        users=users,
        user_type=user_type.capitalize(),
        user_type_singular=user_type.capitalize()[:-1] if user_type.endswith('s') else user_type.capitalize(),
        page_title=f"Manage {user_type.capitalize()}",
        show_department=(user_type in ["hods", "faculty"]),
        add_url=f"/add_user/{user_type}",
        edit_url=f"/edit_user/{user_type}",
        delete_url=f"/delete_user/{user_type}",
        message=flash_get_msg(), # custom helper
        departments=["CSE", "AI", "ISE", "ECE", "CIVIL", "MECH", "MATHS", "PHYSICS", "CHEM", "MBA", "CSDS"]
    )

def flash_get_msg():
    # Helper to get flashed messages in the same request if needed
    return None

@app.route("/add_user/<user_type>", methods=["POST"])
def add_user_route(user_type):
    # Auth check
    if not session.get("principal") and not session.get("hod"):
        return redirect("/")
    # Whitelist allowed table names to prevent SQL injection
    ALLOWED_TABLES = {"hods", "faculty", "security"}
    if user_type not in ALLOWED_TABLES:
        return redirect("/")

    name = request.form.get("name")
    email = request.form.get("email")
    password = hash_pw(request.form.get("password"))
    dept = request.form.get("department", "")
    phone = request.form.get("phone", "")
    desig = request.form.get("designation", "")
    gate = request.form.get("gate_assigned", "")
    photo = save_photo(request.files, "photo")

    conn = get_db(); cursor = conn.cursor()
    if user_type == "hods":
        cursor.execute("INSERT INTO hods (name, email, password, department, phone, photo) VALUES (%s,%s,%s,%s,%s,%s)", (name, email, password, dept, phone, photo))
    elif user_type == "faculty":
        cursor.execute("INSERT INTO faculty (name, email, password, department, phone, designation, photo) VALUES (%s,%s,%s,%s,%s,%s,%s)", (name, email, password, dept, phone, desig, photo))
    elif user_type == "security":
        cursor.execute("INSERT INTO security (name, email, password, phone, gate_assigned, photo) VALUES (%s,%s,%s,%s,%s,%s)", (name, email, password, phone, gate, photo))
    
    conn.commit(); cursor.close(); conn.close()
    return redirect(f"/manage/{user_type}")

@app.route("/edit_user/<user_type>", methods=["POST"])
def edit_user_route(user_type):
    # Auth check
    if not session.get("principal") and not session.get("hod"):
        return redirect("/")
    # Whitelist allowed table names to prevent SQL injection
    ALLOWED_TABLES = {"hods", "faculty", "security"}
    if user_type not in ALLOWED_TABLES:
        return redirect("/")

    uid = request.form.get("id")
    name = request.form.get("name")
    email = request.form.get("email")
    password = hash_pw(request.form.get("password"))
    dept = request.form.get("department", "")
    phone = request.form.get("phone", "")
    desig = request.form.get("designation", "")
    gate = request.form.get("gate_assigned", "")
    photo = save_photo(request.files, "photo")

    set_clauses = ["name=%s", "email=%s", "password=%s", "phone=%s"]
    vals = [name, email, password, phone]
    
    if user_type in ["hods", "faculty"]:
        set_clauses.append("department=%s")
        vals.append(dept)
    if user_type == "faculty":
        set_clauses.append("designation=%s")
        vals.append(desig)
    if user_type == "security":
        set_clauses.append("gate_assigned=%s")
        vals.append(gate)
    if photo:
        set_clauses.append("photo=%s")
        vals.append(photo)
    
    vals.append(uid)
    conn = get_db(); cursor = conn.cursor()
    cursor.execute(f"UPDATE {user_type} SET {', '.join(set_clauses)} WHERE id=%s", vals)
    conn.commit(); cursor.close(); conn.close()
    return redirect(f"/manage/{user_type}")

@app.route("/delete_user/<user_type>/<uid>")
def delete_user_route(user_type, uid):
    # Auth check
    if not session.get("principal") and not session.get("hod"):
        return redirect("/")
    # Whitelist allowed table names to prevent SQL injection
    ALLOWED_TABLES = {"hods", "faculty", "security"}
    if user_type not in ALLOWED_TABLES:
        return redirect("/")

    conn = get_db(); cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {user_type} WHERE id=%s", (uid,))
    conn.commit(); cursor.close(); conn.close()
    return redirect(f"/manage/{user_type}")


# -----------------------
# APPROVE (Principal approves → QR generated, details sent to security)
# -----------------------
@app.route("/approve/<req_id>")
def approve(req_id):
    if not session.get("principal"):
        return redirect("/principal_login")

    all_requests = db_get_all_requests()
    req = next((r for r in all_requests if r["id"] == req_id), None)

    if req:
        now = datetime.now()
        duration_hours = req.get("duration_hours", 1)
        deadline = now + timedelta(hours=duration_hours)
        
        # Parse slot start time using robust parser, then calculate deadline from it
        slot_start_dt = parse_slot_start(req.get("slot", ""), req.get("request_date"))
        if slot_start_dt:
            deadline = slot_start_dt + timedelta(hours=duration_hours)
            print(f"[APPROVE] slot_start={slot_start_dt}, deadline={deadline}")
        else:
            print(f"[APPROVE WARNING] Could not parse slot, using now + duration as deadline: {deadline}")

        db_update_request(req_id, {
            "deadline": deadline,
            "status": "Approved",
            "principal_approved_at": now
        })
        # Send approval email to faculty (async)
        threading.Thread(target=send_faculty_notification_email, args=(
            req["email"], req["name"], req["department"], req.get("slot", ""), req.get("request_date"), deadline
        ), daemon=True).start()

    return redirect("/principal_dashboard")


# -----------------------
# DECLINE
# -----------------------
@app.route("/decline/<req_id>", methods=["POST"])
def decline(req_id):
    if not session.get("principal"):
        return redirect("/principal_login")

    reason = request.form.get("rejection_reason", "").strip()
    if not reason:
        reason = "No reason provided"
    db_update_request(req_id, {"status": "Rejected", "rejection_reason": reason})
    return redirect("/principal_dashboard")


@app.route("/principal_view_request/<req_id>")
def principal_view_request(req_id):
    if not session.get("principal"): return redirect("/principal_login")
    
    all_requests = db_get_all_requests()
    data = next((r for r in all_requests if r["id"] == req_id), None)
    pending_list = [r for r in all_requests if r["status"] == "Pending Principal"]
    
    ai_summary_text = "No request selected."
    if data and "description" in data:
        ai_summary_text = generate_ai_summary(data["description"])

    # Calculate department-wise request counts for Manage Requests view
    dept_counts = {}
    for r in all_requests:
        dept = r.get("department", "Unknown")
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    # Calculate pending dept counts and urgency
    pending_dept_counts = {}
    for r in pending_list:
        dept = r.get("department", "Unknown")
        pending_dept_counts[dept] = pending_dept_counts.get(dept, 0) + 1

        slot_start_dt = parse_slot_start(r.get("slot", ""), r.get("request_date"))
        r["is_urgent"] = False
        if slot_start_dt and r.get("created_at"):
            if isinstance(r["created_at"], str):
                created_at_dt = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S")
            else:
                created_at_dt = r["created_at"]
            
            diff = slot_start_dt - created_at_dt
            if timedelta(0) <= diff <= timedelta(hours=1):
                r["is_urgent"] = True

    if data:
        # Check if the currently viewed request is urgent
        slot_start_dt = parse_slot_start(data.get("slot", ""), data.get("request_date"))
        data["is_urgent"] = False
        if slot_start_dt and data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at_dt = datetime.strptime(data["created_at"], "%Y-%m-%d %H:%M:%S")
            else:
                created_at_dt = data["created_at"]
            
            diff = slot_start_dt - created_at_dt
            if timedelta(0) <= diff <= timedelta(hours=1):
                data["is_urgent"] = True

    return render_template("principal_dashboard.html", 
        data=data, 
        pending_requests=pending_list,
        ai_summary=ai_summary_text,
        auto_mode=session.get("ai_auto_mode", False),
        all_requests=all_requests,
        dept_counts=dept_counts,
        total_requests=len(all_requests),
        pending_dept_counts=pending_dept_counts,
        total_pending=len(pending_list)
    )

# -----------------------
# SECURITY DASHBOARD
# -----------------------
@app.route("/security_dashboard")
def security_dashboard():

    if not session.get("security"):
        return redirect("/security_login")

    alerts = []
    safe = []

    now = datetime.now()

    all_requests = db_get_all_requests()
    for f in all_requests:

        if f["status"] == "Approved" and f["deadline"]:

            if now > f["deadline"]:
                f["time_status"] = "OVERDUE"
                alerts.append(f)
            else:
                f["time_status"] = "ON TIME"
                safe.append(f)

    latest = safe[-1] if safe else None

    return render_template(
        "security_dashboard.html",
        data=latest,
        alerts=alerts,
        safe=safe
    )


# ===========================================================
# PRINCIPAL MANAGEMENT ROUTES (Add/Edit/Delete HODs, Faculty, Security)
# ===========================================================

@app.route("/manage/hods")
def manage_hods():
    if not session.get("principal"):
        return redirect("/principal_login")
    users = db_get_all("hods")
    return render_template("manage_users.html",
        page_title="Manage HODs", user_type="HODs", user_type_singular="HOD",
        users=users, show_department=True,
        add_url="/manage/hods/add", edit_url="/manage/hods/edit", delete_url="/manage/hods/delete",
        manager_role="Principal", back_url="/principal_dashboard",
        departments=["CSE","AI","ISE","ECE","CIVIL","MECH","MATHS","PHYSICS","CHEM","MBA","CSDS"],
        message=request.args.get("msg"), message_type=request.args.get("mt","success"))

@app.route("/manage/hods/add", methods=["POST"])
def add_hod():
    if not session.get("principal"):
        return redirect("/principal_login")
    try:
        photo = save_photo(request.files, "photo")
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("INSERT INTO hods (name, email, password, department, phone, photo) VALUES (%s,%s,%s,%s,%s,%s)",
            (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
             request.form["department"], request.form.get("phone",""), photo))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/hods?msg=HOD+added+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/hods?msg=Error:+{e}&mt=error")

@app.route("/manage/hods/edit", methods=["POST"])
def edit_hod():
    if not session.get("principal"):
        return redirect("/principal_login")
    try:
        photo = save_photo(request.files, "photo")
        conn = get_db(); cursor = conn.cursor()
        if photo:
            cursor.execute("UPDATE hods SET name=%s, email=%s, password=%s, department=%s, phone=%s, photo=%s WHERE id=%s",
                (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
                 request.form["department"], request.form.get("phone",""), photo, request.form["id"]))
        else:
            cursor.execute("UPDATE hods SET name=%s, email=%s, password=%s, department=%s, phone=%s WHERE id=%s",
                (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
                 request.form["department"], request.form.get("phone",""), request.form["id"]))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/hods?msg=HOD+updated+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/hods?msg=Error:+{e}&mt=error")

@app.route("/manage/hods/delete/<int:user_id>")
def delete_hod(user_id):
    if not session.get("principal"):
        return redirect("/principal_login")
    try:
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("DELETE FROM hods WHERE id=%s", (user_id,))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/hods?msg=HOD+deleted+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/hods?msg=Error:+{e}&mt=error")


# --- PRINCIPAL: Manage Faculty ---

@app.route("/manage/faculty")
def manage_faculty():
    if not session.get("principal") and not session.get("hod"):
        return redirect("/")
    
    users = db_get_all("faculty", order_by="department ASC, name ASC")
    
    # If HOD, only show their department
    if session.get("hod"):
        users = [u for u in users if u["department"] == session.get("hod_department")]
        return render_template("manage_users.html",
            page_title="Department Faculty", user_type="Faculty", user_type_singular="Faculty Member",
            users=users, show_department=False,
            add_url="/manage/faculty/add", edit_url="/manage/faculty/edit", delete_url="/manage/faculty/delete",
            manager_role="HOD", back_url="/hod_dashboard",
            departments=[session.get("hod_department")],
            message=request.args.get("msg"), message_type=request.args.get("mt","success"))
            
    return render_template("manage_users.html",
        page_title="Manage Faculty", user_type="Faculty", user_type_singular="Faculty Member",
        users=users, show_department=True,
        add_url="/manage/faculty/add", edit_url="/manage/faculty/edit", delete_url="/manage/faculty/delete",
        manager_role="Principal", back_url="/principal_dashboard",
        departments=["CSE","AI","ISE","ECE","CIVIL","MECH","MATHS","PHYSICS","CHEM","MBA","CSDS"],
        message=request.args.get("msg"), message_type=request.args.get("mt","success"))

@app.route("/manage/faculty/add", methods=["POST"])
def add_faculty():
    if not session.get("principal") and not session.get("hod"):
        return redirect("/")
    try:
        photo = save_photo(request.files, "photo")
        dept = session.get("hod_department") if session.get("hod") else request.form["department"]
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("INSERT INTO faculty (name, email, password, department, phone, designation, photo) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
             dept, request.form.get("phone",""), request.form.get("designation",""), photo))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/faculty?msg=Faculty+added+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/faculty?msg=Error:+{e}&mt=error")

@app.route("/manage/faculty/edit", methods=["POST"])
def edit_faculty():
    if not session.get("principal") and not session.get("hod"):
        return redirect("/")
    try:
        photo = save_photo(request.files, "photo")
        dept = session.get("hod_department") if session.get("hod") else request.form["department"]
        conn = get_db(); cursor = conn.cursor()
        if photo:
            cursor.execute("UPDATE faculty SET name=%s, email=%s, password=%s, department=%s, phone=%s, designation=%s, photo=%s WHERE id=%s",
                (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
                 dept, request.form.get("phone",""), request.form.get("designation",""), photo, request.form["id"]))
        else:
            cursor.execute("UPDATE faculty SET name=%s, email=%s, password=%s, department=%s, phone=%s, designation=%s WHERE id=%s",
                (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
                 dept, request.form.get("phone",""), request.form.get("designation",""), request.form["id"]))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/faculty?msg=Faculty+updated+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/faculty?msg=Error:+{e}&mt=error")

@app.route("/manage/faculty/delete/<int:user_id>")
def delete_faculty(user_id):
    if not session.get("principal") and not session.get("hod"):
        return redirect("/")
    try:
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("DELETE FROM faculty WHERE id=%s", (user_id,))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/faculty?msg=Faculty+deleted+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/faculty?msg=Error:+{e}&mt=error")

# --- PRINCIPAL: View Faculty ---

@app.route("/view_faculty")
def view_faculty():
    if not session.get("principal"):
        return redirect("/principal_login")
    
    dept = request.args.get("department")
    if not dept:
        # Default to CSE if no dept selected but page accessed
        dept = "CSE"
        
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM faculty WHERE department=%s ORDER BY name ASC", (dept,))
        users = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        users = []

    return render_template("view_faculty.html",
        page_title=f"Faculty - {dept} Department",
        users=users, department=dept,
        manager_role="Principal", back_url="/principal_dashboard",
        departments=["CSE","AI","ISE","ECE","CIVIL","MECH","MATHS","PHYSICS","CHEM","MBA","CSDS"])


# --- PRINCIPAL: Manage Security ---

@app.route("/manage/security")
def manage_security():
    if not session.get("principal"):
        return redirect("/principal_login")
    users = db_get_all("security")
    return render_template("manage_users.html",
        page_title="Manage Security", user_type="Security", user_type_singular="Security Guard",
        users=users, show_department=False,
        add_url="/manage/security/add", edit_url="/manage/security/edit", delete_url="/manage/security/delete",
        manager_role="Principal", back_url="/principal_dashboard",
        message=request.args.get("msg"), message_type=request.args.get("mt","success"))

@app.route("/manage/security/add", methods=["POST"])
def add_security():
    if not session.get("principal"):
        return redirect("/principal_login")
    try:
        photo = save_photo(request.files, "photo")
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("INSERT INTO security (name, email, password, phone, gate_assigned, photo) VALUES (%s,%s,%s,%s,%s,%s)",
            (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
             request.form.get("phone",""), request.form.get("gate_assigned",""), photo))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/security?msg=Security+added+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/security?msg=Error:+{e}&mt=error")

@app.route("/manage/security/edit", methods=["POST"])
def edit_security():
    if not session.get("principal"):
        return redirect("/principal_login")
    try:
        photo = save_photo(request.files, "photo")
        conn = get_db(); cursor = conn.cursor()
        if photo:
            cursor.execute("UPDATE security SET name=%s, email=%s, password=%s, phone=%s, gate_assigned=%s, photo=%s WHERE id=%s",
                (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
                 request.form.get("phone",""), request.form.get("gate_assigned",""), photo, request.form["id"]))
        else:
            cursor.execute("UPDATE security SET name=%s, email=%s, password=%s, phone=%s, gate_assigned=%s WHERE id=%s",
                (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
                 request.form.get("phone",""), request.form.get("gate_assigned",""), request.form["id"]))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/security?msg=Security+updated+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/security?msg=Error:+{e}&mt=error")

@app.route("/manage/security/delete/<int:user_id>")
def delete_security(user_id):
    if not session.get("principal"):
        return redirect("/principal_login")
    try:
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("DELETE FROM security WHERE id=%s", (user_id,))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/manage/security?msg=Security+deleted+successfully&mt=success")
    except Exception as e:
        return redirect(f"/manage/security?msg=Error:+{e}&mt=error")


# ===========================================================
# HOD MANAGEMENT ROUTES (Add/Edit/Delete Faculty in their dept)
# ===========================================================

@app.route("/hod/manage/faculty")
def hod_manage_faculty():
    if not session.get("hod"):
        return redirect("/hod_login")
    dept = session.get("hod_department")
    users = db_get_all("faculty", "department = %s", (dept,))
    return render_template("manage_users.html",
        page_title=f"Manage {dept} Faculty", user_type="Faculty", user_type_singular="Faculty Member",
        users=users, show_department=True,
        add_url="/hod/manage/faculty/add", edit_url="/hod/manage/faculty/edit", delete_url="/hod/manage/faculty/delete",
        manager_role="HOD", back_url="/hod_dashboard",
        departments=[dept],
        message=request.args.get("msg"), message_type=request.args.get("mt","success"))

@app.route("/hod/manage/faculty/add", methods=["POST"])
def hod_add_faculty():
    if not session.get("hod"):
        return redirect("/hod_login")
    dept = session.get("hod_department")
    try:
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("INSERT INTO faculty (name, email, password, department, phone, designation) VALUES (%s,%s,%s,%s,%s,%s)",
            (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
             dept, request.form.get("phone",""), request.form.get("designation","")))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/hod/manage/faculty?msg=Faculty+added+successfully&mt=success")
    except Exception as e:
        return redirect(f"/hod/manage/faculty?msg=Error:+{e}&mt=error")

@app.route("/hod/manage/faculty/edit", methods=["POST"])
def hod_edit_faculty():
    if not session.get("hod"):
        return redirect("/hod_login")
    dept = session.get("hod_department")
    try:
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("UPDATE faculty SET name=%s, email=%s, password=%s, phone=%s, designation=%s WHERE id=%s AND department=%s",
            (request.form["name"], request.form["email"], hash_pw(request.form["password"]),
             request.form.get("phone",""), request.form.get("designation",""), request.form["id"], dept))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/hod/manage/faculty?msg=Faculty+updated+successfully&mt=success")
    except Exception as e:
        return redirect(f"/hod/manage/faculty?msg=Error:+{e}&mt=error")

@app.route("/hod/manage/faculty/delete/<int:user_id>")
def hod_delete_faculty(user_id):
    if not session.get("hod"):
        return redirect("/hod_login")
    dept = session.get("hod_department")
    try:
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("DELETE FROM faculty WHERE id=%s AND department=%s", (user_id, dept))
        conn.commit(); cursor.close(); conn.close()
        return redirect("/hod/manage/faculty?msg=Faculty+deleted+successfully&mt=success")
    except Exception as e:
        return redirect(f"/hod/manage/faculty?msg=Error:+{e}&mt=error")


# -----------------------
# EMAIL TEMPLATE MANAGEMENT
# -----------------------

@app.route("/manage_email_templates")
def manage_email_templates():
    if not session.get("principal"):
        return redirect("/principal_login")
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM email_templates ORDER BY id ASC")
    templates = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("manage_templates.html",
        templates=templates,
        message=request.args.get("msg"),
        message_type=request.args.get("mt", "success"))


@app.route("/save_email_template", methods=["POST"])
def save_email_template():
    if not session.get("principal"):
        return redirect("/principal_login")
    
    template_name = request.form.get("template_name")
    subject_template = request.form.get("subject_template", "")
    body_template = request.form.get("body_template", "")
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE email_templates SET subject_template=%s, body_template=%s WHERE template_name=%s",
            (subject_template, body_template, template_name)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/manage_email_templates?msg=Template+saved+successfully!&mt=success")
    except Exception as e:
        return redirect(f"/manage_email_templates?msg=Error:+{e}&mt=error")


@app.route("/reset_email_template/<template_name>")
def reset_email_template(template_name):
    if not session.get("principal"):
        return redirect("/principal_login")
    
    # Default templates
    defaults = {
        "hod_notification": {
            "subject": "New Faculty Exit Request - [FacultyName] ([Department])",
            "body": "Dear [HODName],\n\nA new faculty exit request has been submitted and requires your approval.\n\n--- Request Details ---\nFaculty Name : [FacultyName]\nDepartment   : [Department]\nReason       : [Description]\nTime Slot    : [Slot]\nDate         : [Date]\n------------------------\n\nPlease log in to the Faculty Exit Monitoring System to approve or decline this request.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College"
        },
        "principal_notification": {
            "subject": "HOD Approved Exit Request - [FacultyName] ([Department])",
            "body": "Dear [PrincipalName],\n\nAn HOD has approved a faculty exit request that now requires your final approval.\n\n--- Request Details ---\nFaculty Name : [FacultyName]\nDepartment   : [Department]\nReason       : [Description]\nTime Slot    : [Slot]\nDate         : [Date]\nApproved By  : [ApprovedBy]\n------------------------\n\nPlease log in to the Faculty Exit Monitoring System to approve or decline this request.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College"
        },
        "faculty_approval": {
            "subject": "Your Exit Request Has Been Approved - [Department]",
            "body": "Dear [FacultyName],\n\nGreat news! Your exit request has been approved by the Principal.\n\n--- Approved Request Details ---\nDepartment   : [Department]\nTime Slot    : [Slot]\nDate         : [Date]\nDeadline     : [Deadline]\n--------------------------------\n\nYour QR code pass has been generated. Please log in to the Faculty Exit Monitoring System to view your QR pass and show it to Security at the gate.\n\nPlease ensure you return before the deadline.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College"
        },
        "return_reminder": {
            "subject": "\u23f0 Reminder: Please Return to College - [FacultyName]",
            "body": "Dear [FacultyName],\n\nThis is a reminder that your approved exit slot is ending soon.\n\n--- Your Exit Details ---\nDepartment   : [Department]\nTime Slot    : [Slot]\nDate         : [Date]\nDeadline     : [Deadline]\nTime Left    : Approximately 10 minutes\n--------------------------\n\n\u26a0 Please ensure you return to the college campus BEFORE [Deadline] to avoid being marked as OVERDUE.\n\nIf you have already returned, please ensure your ENTRY QR code has been scanned by Security.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College"
        },
        "late_warning": {
            "subject": "\u26a0 Late Return Warning - [FacultyName] ([Department])",
            "body": "Dear [PrincipalName],\n\nThis is to notify you that a faculty/HOD member has returned LATE beyond their approved exit slot.\n\n--- Late Return Details ---\nFaculty Name : [FacultyName]\nDepartment   : [Department]\nTime Slot    : [Slot]\nDeadline     : [Deadline]\nEntry Time   : [EntryTime]\nMinutes Late : [MinutesLate]\nTotal Warnings : [TotalWarnings]\n----------------------------\n\nThis warning has been recorded and the faculty member has been notified on their dashboard.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College"
        }
    }
    
    default = defaults.get(template_name)
    if not default:
        return redirect("/manage_email_templates?msg=Unknown+template&mt=error")
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE email_templates SET subject_template=%s, body_template=%s WHERE template_name=%s",
            (default["subject"], default["body"], template_name)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/manage_email_templates?msg=Template+reset+to+default!&mt=success")
    except Exception as e:
        return redirect(f"/manage_email_templates?msg=Error:+{e}&mt=error")


# -----------------------
# LOGOUT
# -----------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -----------------------
# RUN
# -----------------------

def parse_slot_start_hour(slot):
    """Parse a slot string like '12-1 PM' and return the start hour in 24h format."""
    try:
        parts = slot.split("-")
        start_part = parts[0].strip()
        end_part = parts[1].strip()
        period = end_part.split(" ")[1]  # AM or PM
        start_hour = int(start_part)
        if period == "PM" and start_hour != 12:
            start_hour += 12
        elif period == "AM" and start_hour == 12:
            start_hour = 0
        # Special case: "11-12 PM" means start is 11 AM
        if start_part == "11" and "12 PM" in end_part:
            start_hour = 11
        return start_hour
    except Exception:
        return None


@app.route("/api/scan_exit/<req_id>")
def scan_exit(req_id):
    """Security scans the EXIT QR code — records the out-time."""
    if not session.get("security"):
        return {"status": "error", "message": "Unauthorized. Please log in as Security."}

    security_email = session.get("security_email", "Unknown")
    all_requests = db_get_all_requests()
    for req in all_requests:
        if str(req.get("id")) == str(req_id):
            now = datetime.now()

            if req.get("status") != "Approved":
                return {"status": "error", "message": f"Request not approved. Current status: {req.get('status')}"}

            # Security check: Ensure they don't exit before their slot!
            slot_start_dt = parse_slot_start(req.get("slot", ""), req.get("request_date"))
            if slot_start_dt:
                valid_from = slot_start_dt - timedelta(minutes=10)
                if now < valid_from:
                    return {
                        "status": "error", 
                        "message": f"Too early! Exit pass is only valid from {valid_from.strftime('%d %b %I:%M %p')}."
                    }

            if req.get("exit_scan_time"):
                return {
                    "status": "already",
                    "message": f"EXIT already scanned at {req['exit_scan_time'].strftime('%d %b %I:%M %p')}",
                    "name": req["name"], "email": req["email"],
                    "department": req["department"], "slot": req["slot"]
                }

            # Record exit scan time
            db_update_request(req_id, {
                "exit_scan_time": now,
                "scanned_by_exit": security_email
            })

            time_status = "ON TIME"
            if req["deadline"] and now > req["deadline"]:
                time_status = "OVERDUE"

            return {
                "status": "success",
                "scan_type": "EXIT",
                "name": req["name"],
                "email": req["email"],
                "department": req["department"],
                "slot": req["slot"],
                "time_status": time_status,
                "scan_time": now.strftime("%d %b %Y, %I:%M %p"),
                "req_status": req.get("status")
            }
    return {"status": "error", "message": "Invalid QR Code or Pass not found"}


@app.route("/api/scan_entry/<req_id>")
def scan_entry(req_id):
    """Security scans the ENTRY QR code — records the in-time."""
    if not session.get("security"):
        return {"status": "error", "message": "Unauthorized. Please log in as Security."}

    security_email = session.get("security_email", "Unknown")
    all_requests = db_get_all_requests()
    for req in all_requests:
        if str(req.get("id")) == str(req_id):
            now = datetime.now()

            if req.get("status") != "Approved":
                return {"status": "error", "message": f"Request not approved. Current status: {req.get('status')}"}

            if not req.get("exit_scan_time"):
                return {"status": "error", "message": "EXIT QR must be scanned first before ENTRY."}

            if req.get("entry_scan_time"):
                return {
                    "status": "already",
                    "message": f"ENTRY already scanned at {req['entry_scan_time'].strftime('%d %b %I:%M %p')}",
                    "name": req["name"], "email": req["email"],
                    "department": req["department"], "slot": req["slot"]
                }

            # Record entry scan time
            db_update_request(req_id, {
                "entry_scan_time": now,
                "scanned_by_entry": security_email
            })

            time_status = "ON TIME"
            if req["deadline"] and now > req["deadline"]:
                time_status = "OVERDUE"
                # Issue late warning and notify principal
                process_late_return(req, now)

            return {
                "status": "success",
                "scan_type": "ENTRY",
                "name": req["name"],
                "email": req["email"],
                "department": req["department"],
                "slot": req["slot"],
                "time_status": time_status,
                "scan_time": now.strftime("%d %b %Y, %I:%M %p"),
                "req_status": req.get("status")
            }
    return {"status": "error", "message": "Invalid QR Code or Pass not found"}


# -----------------------
# SECURITY HISTORY
# -----------------------
@app.route("/security_history")
def security_history():
    if not session.get("security"):
        return redirect("/security_login")

    all_requests = db_get_all_requests()
    # Show all requests that have been approved (with or without scans)
    history = [r for r in all_requests if r["status"] == "Approved"]
    # Sort by exit_scan_time descending (most recent first), unscanned at end
    history.sort(key=lambda x: x.get("exit_scan_time") or datetime.min, reverse=True)

    return render_template("security_history.html", history=history)


# -----------------------
# REMINDER CHECK API (for dashboard notifications)
# -----------------------
@app.route("/api/check_reminder")
def api_check_reminder():
    """API endpoint that the faculty/HOD dashboard polls to show
    a return reminder notification banner when the deadline is within 10 minutes."""
    email = session.get("faculty_email") or session.get("hod_email")
    if not email:
        return jsonify({"reminder": False})

    now = datetime.now()
    reminder_window = now + timedelta(minutes=10)

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT request_id, faculty_name, deadline, slot, request_date
            FROM faculty_requests
            WHERE faculty_email = %s
              AND status = 'Approved'
              AND deadline IS NOT NULL
              AND deadline > %s
              AND deadline <= %s
              AND entry_scan_time IS NULL
            ORDER BY deadline ASC
            LIMIT 1
        """, (email, now, reminder_window))
        req = cursor.fetchone()
        cursor.close()
        conn.close()

        if req:
            minutes_left = max(0, int((req["deadline"] - now).total_seconds() / 60))
            return jsonify({
                "reminder": True,
                "request_id": req["request_id"],
                "faculty_name": req["faculty_name"],
                "deadline": req["deadline"].strftime("%I:%M %p"),
                "deadline_full": req["deadline"].strftime("%d %B %Y, %I:%M %p"),
                "minutes_left": minutes_left,
                "slot": req.get("slot", ""),
            })
    except Exception as e:
        print(f"[REMINDER API ERROR] {e}")

    return jsonify({"reminder": False})


if __name__ == "__main__":
    app.run(debug=True)