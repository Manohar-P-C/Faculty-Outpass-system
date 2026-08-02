import mysql.connector
from db_setup import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from werkzeug.security import generate_password_hash

def migrate():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        hod_pw = generate_password_hash("3333")
        
        # Ensure HOD CSDS exists
        cursor.execute("SELECT id FROM hods WHERE department = 'CSDS'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO hods (name, email, password, department, phone) VALUES (%s, %s, %s, %s, %s)",
                           ("HOD CSDS", "hod.csds@svit.edu", hod_pw, "CSDS", ""))
            print("[OK] Inserted HOD CSDS")

        # Ensure HOD CSCY exists
        cursor.execute("SELECT id FROM hods WHERE department = 'CSCY'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO hods (name, email, password, department, phone) VALUES (%s, %s, %s, %s, %s)",
                           ("HOD CSCY", "hod.cscy@svit.edu", hod_pw, "CSCY", ""))
            print("[OK] Inserted HOD CSCY")

        # Ensure HOD CSBS exists
        cursor.execute("SELECT id FROM hods WHERE department = 'CSBS'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO hods (name, email, password, department, phone) VALUES (%s, %s, %s, %s, %s)",
                           ("HOD CSBS", "hod.csbs@svit.edu", hod_pw, "CSBS", ""))
            print("[OK] Inserted HOD CSBS")

        conn.commit()
        cursor.close()
        conn.close()
        print("[SUCCESS] New department HODs migrated successfully.")
    except Exception as e:
        print(f"[DB MIGRATION NOTICE] Could not connect or migrate DB: {e}")

if __name__ == "__main__":
    migrate()
