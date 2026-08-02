"""
Migration Script: Add AI Call Escalation Columns & Tables
- Adds assistant_name, assistant_phone, escalation_timeout_mins, ai_call_enabled to 'hods' table
- Adds ai_call_sent, ai_call_sid, ai_call_status, ai_call_timestamp to 'faculty_requests' table
- Creates 'ai_call_logs' table for recording call delivery history
"""

from db_setup import get_connection

def migrate_ai_call():
    print("=" * 60)
    print("Migrating Database for AI Call Escalation Feature...")
    print("=" * 60)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Alter 'hods' table
        hod_columns = [
            ("assistant_name", "VARCHAR(100) DEFAULT NULL"),
            ("assistant_phone", "VARCHAR(20) DEFAULT NULL"),
            ("escalation_timeout_mins", "INT DEFAULT 15"),
            ("ai_call_enabled", "TINYINT(1) DEFAULT 1")
        ]
        
        for col_name, col_def in hod_columns:
            try:
                cursor.execute(f"ALTER TABLE hods ADD COLUMN {col_name} {col_def}")
                print(f"[OK] Added '{col_name}' column to 'hods'.")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"[SKIP] Column '{col_name}' already exists in 'hods'.")
                else:
                    print(f"[ERROR] Failed adding '{col_name}' to 'hods': {e}")

        # 2. Alter 'faculty_requests' table
        request_columns = [
            ("ai_call_sent", "TINYINT(1) DEFAULT 0"),
            ("ai_call_sid", "VARCHAR(100) DEFAULT NULL"),
            ("ai_call_status", "VARCHAR(50) DEFAULT 'Not Triggered'"),
            ("ai_call_timestamp", "DATETIME DEFAULT NULL")
        ]
        
        for col_name, col_def in request_columns:
            try:
                cursor.execute(f"ALTER TABLE faculty_requests ADD COLUMN {col_name} {col_def}")
                print(f"[OK] Added '{col_name}' column to 'faculty_requests'.")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"[SKIP] Column '{col_name}' already exists in 'faculty_requests'.")
                else:
                    print(f"[ERROR] Failed adding '{col_name}' to 'faculty_requests': {e}")

        # 3. Create 'ai_call_logs' table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_call_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id VARCHAR(10) NOT NULL,
                department VARCHAR(50) NOT NULL,
                faculty_name VARCHAR(100) NOT NULL,
                assistant_name VARCHAR(100),
                assistant_phone VARCHAR(20) NOT NULL,
                call_sid VARCHAR(100),
                call_status VARCHAR(50) DEFAULT 'Queued',
                duration_seconds INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table 'ai_call_logs' created (or already exists).")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[SUCCESS] AI Call Escalation Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"[FATAL] Migration error: {e}")

if __name__ == "__main__":
    migrate_ai_call()
