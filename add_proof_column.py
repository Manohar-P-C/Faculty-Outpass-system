import mysql.connector

def add_proof_column():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="manohar2129",
        database="college_db"
    )
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE faculty_requests ADD COLUMN proof VARCHAR(255);")
        print("Proof column added to faculty_requests table.")
    except Exception as e:
        print(f"Error: {e}")
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    add_proof_column()
