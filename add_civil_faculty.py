import mysql.connector

# DB Config
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

faculties = [
    ("Dr. Ananthayya M B", "Professor & HOD"),
    ("Prof. Gowtham B", "Assistant Professor"),
    ("Prof. Eshwaraj", "Assistant Professor"),
    ("Prof. Sowmya R", "Assistant Professor"),
    ("Prof. Harshitha Manjunath", "Assistant Professor"),
]

def add_civil_faculty():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    # 1. Update the HOD to be the real HOD
    hod_email = "ananthayyamb.civil@svit.edu"
    cursor.execute("""
        UPDATE hods 
        SET name = %s, email = %s
        WHERE department = 'CIVIL'
    """, ("Dr. Ananthayya M B", hod_email))
    print("Updated CIVIL HOD to Dr. Ananthayya M B.")
    
    count = 0
    for name, designation in faculties:
        # Generate a simple email based on the name
        clean_name = name.replace("Dr. ", "").replace("Prof. ", "").replace(" ", "").replace("-", "").lower()
        email = f"{clean_name}.civil@svit.edu"
        password = "password123" # Default password
        department = "CIVIL"
        
        try:
            cursor.execute("""
                INSERT INTO faculty (name, email, password, department, phone, designation)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, email, password, department, "", designation))
            count += 1
            print(f"Added {name} ({email})")
        except mysql.connector.Error as err:
            if err.errno == 1062: # Duplicate entry
                print(f"Skipped {name} (Email {email} already exists)")
            else:
                print(f"Error adding {name}: {err}")
                
    conn.commit()
    cursor.close()
    conn.close()
    print(f"\nSuccessfully added {count} faculty members to the CIVIL department.")

if __name__ == "__main__":
    add_civil_faculty()
