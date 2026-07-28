"""
Migration: Add reminder_sent column to faculty_requests
and add return_reminder email template.
Run this ONCE.
"""

import mysql.connector

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

def migrate():
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor()

    # 1. Add reminder_sent column to faculty_requests
    try:
        cursor.execute("ALTER TABLE faculty_requests ADD COLUMN reminder_sent TINYINT(1) DEFAULT 0")
        print("[OK] Added 'reminder_sent' column to faculty_requests.")
    except mysql.connector.errors.ProgrammingError as e:
        if "Duplicate column name" in str(e):
            print("[SKIP] 'reminder_sent' column already exists.")
        else:
            raise

    # 2. Add return_reminder email template
    try:
        cursor.execute("SELECT COUNT(*) FROM email_templates WHERE template_name = 'return_reminder'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO email_templates (template_name, display_name, subject_template, body_template, available_placeholders, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                "return_reminder",
                "Return Reminder (10 min before deadline)",
                "⏰ Reminder: Please Return to College - [FacultyName]",
                "Dear [FacultyName],\n\nThis is a reminder that your approved exit slot is ending soon.\n\n--- Your Exit Details ---\nDepartment   : [Department]\nTime Slot    : [Slot]\nDate         : [Date]\nDeadline     : [Deadline]\nTime Left    : Approximately 10 minutes\n--------------------------\n\n⚠ Please ensure you return to the college campus BEFORE [Deadline] to avoid being marked as OVERDUE.\n\nIf you have already returned, please ensure your ENTRY QR code has been scanned by Security.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College",
                "[FacultyName], [Department], [Slot], [Date], [Deadline]",
                "Sent to Faculty/HOD 10 minutes before their exit deadline expires"
            ))
            print("[OK] Added 'return_reminder' email template.")
        else:
            print("[SKIP] 'return_reminder' email template already exists.")
    except Exception as e:
        print(f"[ERROR] {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n[DONE] Migration complete!")


if __name__ == "__main__":
    migrate()
