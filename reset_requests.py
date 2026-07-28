import mysql.connector
from mysql.connector import Error

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

def reset_requests():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
        cursor = conn.cursor()

        # Clear faculty requests
        cursor.execute("DELETE FROM faculty_requests")
        print("[OK] Deleted all records from 'faculty_requests'.")

        # Clear late warnings
        cursor.execute("DELETE FROM late_warnings")
        print("[OK] Deleted all records from 'late_warnings'.")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[DONE] System requests and warnings have been successfully reset!")

    except Error as e:
        print(f"[ERROR] Reset failed: {e}")

if __name__ == "__main__":
    reset_requests()
