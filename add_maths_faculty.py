import mysql.connector

# DB Config
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

faculties = [
    ("Dr. Lakshminarayanachari K", "Professor & Vice Principal"),
    ("Dr. Arun Kumar R", "Professor & HOD"),
    ("Dr. Bhaskar C", "Assistant Professor"),
    ("Prof. Naveena G N", "Assistant Professor"),
    ("Prof. Kishore Kumar V", "Assistant Professor"),
    ("Prof. Niveditha M", "Assistant Professor"),
    ("Prof. Abhishek P A", "Assistant Professor"),
    ("Prof. Raghuvaran", "Assistant Professor"),
    ("Prof. Chaitra S", "Assistant Professor"),
]

def add_maths_faculty():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    # 1. Update the HOD to be the real HOD
    hod_email = "arunkumarr.maths@svit.edu"
    cursor.execute("""
        UPDATE hods 
        SET name = %s, email = %s
        WHERE department = 'MATHS'
    """, ("Dr. Arun Kumar R", hod_email))
    print("Updated MATHS HOD to Dr. Arun Kumar R.")
    
    count = 0
    for name, designation in faculties:
        # Generate a simple email based on the name
        clean_name = name.replace("Dr. ", "").replace("Prof. ", "").replace(" ", "").replace("-", "").lower()
        email = f"{clean_name}.maths@svit.edu"
        password = "password123" # Default password
        department = "MATHS"
        
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
    print(f"\nSuccessfully added {count} faculty members to the MATHS department.")

if __name__ == "__main__":
    add_maths_faculty()
