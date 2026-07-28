"""
Migration Script: Add exit_scan_time and entry_scan_time columns to faculty_requests table.
This enables tracking when security scans the EXIT QR and ENTRY QR for each request.
"""

import mysql.connector

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

def migrate():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("DESCRIBE faculty_requests")
    columns = [row[0] for row in cursor.fetchall()]

    if "exit_scan_time" not in columns:
        cursor.execute("ALTER TABLE faculty_requests ADD COLUMN exit_scan_time DATETIME NULL")
        print("[OK] Added 'exit_scan_time' column.")
    else:
        print("[SKIP] 'exit_scan_time' already exists.")

    if "entry_scan_time" not in columns:
        cursor.execute("ALTER TABLE faculty_requests ADD COLUMN entry_scan_time DATETIME NULL")
        print("[OK] Added 'entry_scan_time' column.")
    else:
        print("[SKIP] 'entry_scan_time' already exists.")

    if "scanned_by_exit" not in columns:
        cursor.execute("ALTER TABLE faculty_requests ADD COLUMN scanned_by_exit VARCHAR(150) NULL")
        print("[OK] Added 'scanned_by_exit' column.")
    else:
        print("[SKIP] 'scanned_by_exit' already exists.")

    if "scanned_by_entry" not in columns:
        cursor.execute("ALTER TABLE faculty_requests ADD COLUMN scanned_by_entry VARCHAR(150) NULL")
        print("[OK] Added 'scanned_by_entry' column.")
    else:
        print("[SKIP] 'scanned_by_entry' already exists.")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n[DONE] Migration complete!")


if __name__ == "__main__":
    migrate()
