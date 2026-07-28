"""
Migration script to add late-arrival warnings support.
Adds:
  1. late_warnings table — stores each warning event
  2. warning_sent column on faculty_requests — prevents duplicate warnings
  3. late_warning email template
Run ONCE before restarting app.py.
"""

import mysql.connector
from mysql.connector import Error

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

def migrate():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
        cursor = conn.cursor()

        # 1. Create late_warnings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS late_warnings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                faculty_email VARCHAR(150) NOT NULL,
                faculty_name VARCHAR(100) NOT NULL,
                department VARCHAR(50) NOT NULL,
                request_id VARCHAR(10) NOT NULL,
                slot VARCHAR(50),
                deadline DATETIME,
                entry_time DATETIME,
                minutes_late INT DEFAULT 0,
                notified_principal TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'late_warnings' created (or already exists).")

        # 2. Add warning_sent column to faculty_requests if not exists
        try:
            cursor.execute("""
                ALTER TABLE faculty_requests ADD COLUMN warning_sent TINYINT(1) DEFAULT 0
            """)
            print("[OK] Column 'warning_sent' added to faculty_requests.")
        except Error as e:
            if e.errno == 1060:  # Duplicate column
                print("[OK] Column 'warning_sent' already exists.")
            else:
                raise

        # 3. Add late_warning email template if not exists
        cursor.execute(
            "SELECT COUNT(*) FROM email_templates WHERE template_name = 'late_warning'"
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO email_templates 
                (template_name, display_name, subject_template, body_template, available_placeholders, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                "late_warning",
                "Late Return Warning (Principal Notification)",
                "⚠ Late Return Warning - [FacultyName] ([Department])",
                "Dear [PrincipalName],\n\nThis is to notify you that a faculty/HOD member has returned LATE beyond their approved exit slot.\n\n--- Late Return Details ---\nFaculty Name : [FacultyName]\nDepartment   : [Department]\nTime Slot    : [Slot]\nDeadline     : [Deadline]\nEntry Time   : [EntryTime]\nMinutes Late : [MinutesLate]\nTotal Warnings : [TotalWarnings]\n----------------------------\n\nThis warning has been recorded and the faculty member has been notified on their dashboard.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College",
                "[FacultyName], [Department], [Slot], [Deadline], [EntryTime], [MinutesLate], [TotalWarnings], [PrincipalName]",
                "Sent to Principal when a faculty/HOD returns late after their approved exit deadline"
            ))
            print("[OK] Email template 'late_warning' added.")
        else:
            print("[OK] Email template 'late_warning' already exists.")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[DONE] Warning migration complete!")

    except Error as e:
        print(f"[ERROR] Migration failed: {e}")
        raise


if __name__ == "__main__":
    print("=" * 50)
    print("Late Warning System - Database Migration")
    print("=" * 50)
    migrate()
