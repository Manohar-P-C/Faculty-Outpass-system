"""
Database Setup Script for Faculty Exit Monitoring System
Creates MySQL database and tables for faculty, HODs, principal, and security.
Supports Aiven cloud MySQL (SSL required).
Run this ONCE before starting the application.
"""

import os
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

# -----------------------
# DATABASE CONFIG
# -----------------------
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "manohar2129")
DB_NAME = os.environ.get("DB_NAME", "college_db")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_SSL = os.environ.get("DB_SSL", "false").lower() in ("true", "1", "required")


def get_connection(use_database=True):
    """Get a MySQL connection with optional SSL support for Aiven."""
    config = {
        'host': DB_HOST,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'port': DB_PORT,
    }
    if use_database:
        config['database'] = DB_NAME
    if DB_SSL:
        config['ssl_disabled'] = False
        config['ssl_verify_cert'] = False
    return mysql.connector.connect(**config)


def create_database():
    """Create the database if it doesn't exist.
    On cloud providers like Aiven, the database may already exist (e.g. 'defaultdb'),
    so this step is skipped gracefully if it fails."""
    try:
        conn = get_connection(use_database=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"[OK] Database '{DB_NAME}' created (or already exists).")
        cursor.close()
        conn.close()
    except Error as e:
        # On Aiven free tier, you may not have permission to create databases.
        # The default 'defaultdb' already exists.
        print(f"[INFO] Skipping database creation (may already exist on cloud): {e}")


def create_tables():
    """Create all required tables."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # -----------------------
        # PRINCIPAL TABLE
        # -----------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS principal (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                photo VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'principal' created.")

        # -----------------------
        # HOD TABLE
        # -----------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hods (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                department VARCHAR(50) NOT NULL,
                phone VARCHAR(20),
                photo VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'hods' created.")

        # -----------------------
        # FACULTY TABLE
        # -----------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faculty (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                department VARCHAR(50) NOT NULL,
                phone VARCHAR(20),
                photo VARCHAR(255),
                designation VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'faculty' created.")

        # -----------------------
        # SECURITY TABLE
        # -----------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                photo VARCHAR(255),
                gate_assigned VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'security' created.")

        # -----------------------
        # FACULTY REQUESTS TABLE (exit requests)
        # -----------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faculty_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id VARCHAR(10) NOT NULL UNIQUE,
                faculty_email VARCHAR(150) NOT NULL,
                faculty_name VARCHAR(100) NOT NULL,
                department VARCHAR(50) NOT NULL,
                description TEXT,
                slot VARCHAR(50),
                duration_hours INT DEFAULT 1,
                status VARCHAR(50) DEFAULT 'Pending HOD',
                proof VARCHAR(255),
                request_date DATE,
                deadline DATETIME,
                hod_approved_by VARCHAR(150),
                hod_approved_at DATETIME,
                principal_approved_at DATETIME,
                exit_scan_time DATETIME,
                entry_scan_time DATETIME,
                scanned_by_exit VARCHAR(150),
                scanned_by_entry VARCHAR(150),
                reminder_sent TINYINT(1) DEFAULT 0,
                warning_sent TINYINT(1) DEFAULT 0,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'faculty_requests' created.")

        # -----------------------
        # EMAIL TEMPLATES TABLE
        # -----------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                template_name VARCHAR(100) NOT NULL UNIQUE,
                display_name VARCHAR(150) NOT NULL,
                subject_template VARCHAR(255) NOT NULL,
                body_template TEXT NOT NULL,
                available_placeholders TEXT,
                description VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'email_templates' created.")

        # -----------------------
        # SYSTEM SETTINGS TABLE
        # -----------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                setting_key VARCHAR(100) PRIMARY KEY,
                setting_value VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'system_settings' created.")

        # -----------------------
        # LATE WARNINGS TABLE
        # -----------------------
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
        print("[OK] Table 'late_warnings' created.")

        # -----------------------
        # DEPARTMENTS TABLE
        # -----------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                icon VARCHAR(10) DEFAULT '🏫',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'departments' created.")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[DONE] All tables created successfully!")

    except Error as e:
        print(f"[ERROR] Error creating tables: {e}")
        raise


def seed_default_data():
    """Insert default principal, HOD, security, and faculty accounts."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # -----------------------
        # SEED PRINCIPAL
        # -----------------------
        cursor.execute("SELECT COUNT(*) FROM principal")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO principal (name, email, password, phone)
                VALUES (%s, %s, %s, %s)
            """, ("Principal", "arjunkv350@gmail.com", generate_password_hash("1234"), ""))
            print("[OK] Default principal account added.")

        # -----------------------
        # SEED HODs
        # -----------------------
        cursor.execute("SELECT COUNT(*) FROM hods")
        if cursor.fetchone()[0] == 0:
            hod_pw = generate_password_hash("3333")
            hods = [
                ("HOD CSE", "hod.cse@svit.edu", hod_pw, "CSE", ""),
                ("HOD AI", "hod.ai@svit.edu", hod_pw, "AI", ""),
                ("HOD ISE", "hod.ise@svit.edu", hod_pw, "ISE", ""),
                ("HOD ECE", "hod.ece@svit.edu", hod_pw, "ECE", ""),
                ("HOD CIVIL", "hod.civil@svit.edu", hod_pw, "CIVIL", ""),
                ("HOD MECH", "hod.mech@svit.edu", hod_pw, "MECH", ""),
                ("HOD MATHS", "hod.maths@svit.edu", hod_pw, "MATHS", ""),
                ("HOD PHYSICS", "hod.physics@svit.edu", hod_pw, "PHYSICS", ""),
                ("HOD CHEM", "hod.chem@svit.edu", hod_pw, "CHEM", ""),
                ("HOD MBA", "hod.mba@svit.edu", hod_pw, "MBA", ""),
                ("HOD CSDS", "hod.csds@svit.edu", hod_pw, "CSDS", ""),
                ("HOD CSCY", "hod.cscy@svit.edu", hod_pw, "CSCY", ""),
                ("HOD CSBS", "hod.csbs@svit.edu", hod_pw, "CSBS", ""),
            ]
            cursor.executemany("""
                INSERT INTO hods (name, email, password, department, phone)
                VALUES (%s, %s, %s, %s, %s)
            """, hods)
            print("[OK] Default HOD accounts added (13 departments).")

        # -----------------------
        # SEED SECURITY
        # -----------------------
        cursor.execute("SELECT COUNT(*) FROM security")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO security (name, email, password, phone, gate_assigned)
                VALUES (%s, %s, %s, %s, %s)
            """, ("Security Guard", "eshanshekar06112006@gmail.com", generate_password_hash("2222"), "", "Main Gate"))
            print("[OK] Default security account added.")

        # -----------------------
        # SEED FACULTY
        # -----------------------
        cursor.execute("SELECT COUNT(*) FROM faculty")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO faculty (name, email, password, department, phone, designation)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Manohar", "manohar472007@gmail.com", generate_password_hash("Manohar2129"), "CSE", "", "Assistant Professor"))
            print("[OK] Default faculty account added.")

        # -----------------------
        # SEED EMAIL TEMPLATES
        # -----------------------
        cursor.execute("SELECT COUNT(*) FROM email_templates")
        if cursor.fetchone()[0] == 0:
            templates = [
                (
                    "hod_notification",
                    "HOD Notification (Faculty submits request)",
                    "New Faculty Exit Request - [FacultyName] ([Department])",
                    "Dear [HODName],\n\nA new faculty exit request has been submitted and requires your approval.\n\n--- Request Details ---\nFaculty Name : [FacultyName]\nDepartment   : [Department]\nReason       : [Description]\nTime Slot    : [Slot]\nDate         : [Date]\n------------------------\n\nPlease log in to the Faculty Exit Monitoring System to approve or decline this request.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College",
                    "[FacultyName], [Department], [Description], [Slot], [Date], [HODName]",
                    "Sent to HOD when a faculty member submits a new exit request"
                ),
                (
                    "principal_notification",
                    "Principal Notification (HOD approves request)",
                    "HOD Approved Exit Request - [FacultyName] ([Department])",
                    "Dear [PrincipalName],\n\nAn HOD has approved a faculty exit request that now requires your final approval.\n\n--- Request Details ---\nFaculty Name : [FacultyName]\nDepartment   : [Department]\nReason       : [Description]\nTime Slot    : [Slot]\nDate         : [Date]\nApproved By  : [ApprovedBy]\n------------------------\n\nPlease log in to the Faculty Exit Monitoring System to approve or decline this request.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College",
                    "[FacultyName], [Department], [Description], [Slot], [Date], [PrincipalName], [ApprovedBy]",
                    "Sent to Principal when an HOD approves a faculty request"
                ),
                (
                    "faculty_approval",
                    "Faculty Approval (Principal approves request)",
                    "Your Exit Request Has Been Approved - [Department]",
                    "Dear [FacultyName],\n\nGreat news! Your exit request has been approved by the Principal.\n\n--- Approved Request Details ---\nDepartment   : [Department]\nTime Slot    : [Slot]\nDate         : [Date]\nDeadline     : [Deadline]\n--------------------------------\n\nYour QR code pass has been generated. Please log in to the Faculty Exit Monitoring System to view your QR pass and show it to Security at the gate.\n\nPlease ensure you return before the deadline.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College",
                    "[FacultyName], [Department], [Slot], [Date], [Deadline]",
                    "Sent to Faculty when the Principal approves their exit request"
                ),
                (
                    "return_reminder",
                    "Return Reminder (10 min before deadline)",
                    "\u23f0 Reminder: Please Return to College - [FacultyName]",
                    "Dear [FacultyName],\n\nThis is a reminder that your approved exit slot is ending soon.\n\n--- Your Exit Details ---\nDepartment   : [Department]\nTime Slot    : [Slot]\nDate         : [Date]\nDeadline     : [Deadline]\nTime Left    : Approximately 10 minutes\n--------------------------\n\n\u26a0 Please ensure you return to the college campus BEFORE [Deadline] to avoid being marked as OVERDUE.\n\nIf you have already returned, please ensure your ENTRY QR code has been scanned by Security.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College",
                    "[FacultyName], [Department], [Slot], [Date], [Deadline]",
                    "Sent to Faculty/HOD 10 minutes before their exit deadline expires"
                ),
                (
                    "late_warning",
                    "Late Return Warning (Principal Notification)",
                    "\u26a0 Late Return Warning - [FacultyName] ([Department])",
                    "Dear [PrincipalName],\n\nThis is to notify you that a faculty/HOD member has returned LATE beyond their approved exit slot.\n\n--- Late Return Details ---\nFaculty Name : [FacultyName]\nDepartment   : [Department]\nTime Slot    : [Slot]\nDeadline     : [Deadline]\nEntry Time   : [EntryTime]\nMinutes Late : [MinutesLate]\nTotal Warnings : [TotalWarnings]\n----------------------------\n\nThis warning has been recorded and the faculty member has been notified on their dashboard.\n\nRegards,\nFaculty Exit Monitoring System\nSVIT College",
                    "[FacultyName], [Department], [Slot], [Deadline], [EntryTime], [MinutesLate], [TotalWarnings], [PrincipalName]",
                    "Sent to Principal when a faculty/HOD returns late after their approved exit deadline"
                ),
            ]
            cursor.executemany("""
                INSERT INTO email_templates (template_name, display_name, subject_template, body_template, available_placeholders, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, templates)
            print("[OK] Default email templates added (5 templates).")

        # -----------------------
        # SEED DEPARTMENTS
        # -----------------------
        cursor.execute("SELECT COUNT(*) FROM departments")
        if cursor.fetchone()[0] == 0:
            default_depts = [
                ("CSE", "Computer Science & Engineering", "💻"),
                ("AI", "Artificial Intelligence & Machine Learning", "🤖"),
                ("ISE", "Information Science & Engineering", "🖥️"),
                ("ECE", "Electronics & Communication Engineering", "📡"),
                ("CIVIL", "Civil Engineering", "🏗️"),
                ("MECH", "Mechanical Engineering", "⚙️"),
                ("MATHS", "Mathematics", "📐"),
                ("PHYSICS", "Physics", "🔬"),
                ("CHEM", "Chemistry", "⚗️"),
                ("MBA", "Master of Business Administration", "📊"),
                ("CSDS", "Computer Science & Data Science", "💾"),
                ("CSCY", "Computer Science & Cyber Security", "🛡️"),
                ("CSBS", "Computer Science & Business Studies", "💼")
            ]
            cursor.executemany("""
                INSERT INTO departments (code, name, icon)
                VALUES (%s, %s, %s)
            """, default_depts)
            print("[OK] Default departments seeded (13 departments).")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[DONE] Default data seeded successfully!")

    except Error as e:
        print(f"[ERROR] Error seeding data: {e}")
        raise


if __name__ == "__main__":
    print("=" * 50)
    print("Faculty Exit Monitoring System - DB Setup")
    print("=" * 50)
    print(f"\nConnecting to: {DB_HOST}:{DB_PORT} (SSL: {DB_SSL})")
    print(f"Database: {DB_NAME}")
    print()
    create_database()
    create_tables()
    seed_default_data()
    print()
    print("=" * 50)
    print("Setup complete! You can now run app.py")
    print("=" * 50)
