import mysql.connector
from db_setup import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from werkzeug.security import generate_password_hash

faculties = [
    ("Dr. Cyber HOD", "Associate Professor & HOD"),
    ("Prof. Cyber Faculty 1", "Assistant Professor"),
    ("Prof. Cyber Faculty 2", "Assistant Professor"),
]

def add_cscy_department():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # 1. Add HOD for CSCY if not exists
        hod_pw = generate_password_hash("3333")
        cursor.execute("SELECT id FROM hods WHERE department = 'CSCY'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO hods (name, email, password, department, phone)
                VALUES (%s, %s, %s, %s, %s)
            """, ("HOD CSCY", "hod.cscy@svit.edu", hod_pw, "CSCY", ""))
            print("Added HOD for CSCY (hod.cscy@svit.edu).")

        conn.commit()
        cursor.close()
        conn.close()
        print("Successfully setup CSCY department in database.")
    except Exception as e:
        print(f"Error setting up CSCY department: {e}")

if __name__ == "__main__":
    add_cscy_department()
