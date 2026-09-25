"""
Rollback Script: Remove AI Call Escalation Columns & Tables from MySQL Database
- Drops assistant_name, assistant_phone, escalation_timeout_mins, ai_call_enabled from 'hods'
- Drops ai_call_sent, ai_call_sid, ai_call_status, ai_call_timestamp from 'faculty_requests'
- Drops 'ai_call_logs' table
"""

from db_setup import get_connection

def rollback_ai_call():
    print("=" * 60)
    print("Rolling back AI Call Escalation Database Changes...")
    print("=" * 60)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Drop columns from 'hods'
        hod_columns = ["assistant_name", "assistant_phone", "escalation_timeout_mins", "ai_call_enabled"]
        for col in hod_columns:
            try:
                cursor.execute(f"ALTER TABLE hods DROP COLUMN {col}")
                print(f"[OK] Dropped column '{col}' from 'hods'.")
            except Exception as e:
                print(f"[SKIP] Column '{col}' in 'hods': {e}")

        # 2. Drop columns from 'faculty_requests'
        request_columns = ["ai_call_sent", "ai_call_sid", "ai_call_status", "ai_call_timestamp"]
        for col in request_columns:
            try:
                cursor.execute(f"ALTER TABLE faculty_requests DROP COLUMN {col}")
                print(f"[OK] Dropped column '{col}' from 'faculty_requests'.")
            except Exception as e:
                print(f"[SKIP] Column '{col}' in 'faculty_requests': {e}")

        # 3. Drop 'ai_call_logs' table
        try:
            cursor.execute("DROP TABLE IF EXISTS ai_call_logs")
            print("[OK] Dropped table 'ai_call_logs'.")
        except Exception as e:
            print(f"[ERROR] Could not drop table 'ai_call_logs': {e}")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[SUCCESS] AI Call Escalation rollback completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"[FATAL] Rollback error: {e}")

if __name__ == "__main__":
    rollback_ai_call()
