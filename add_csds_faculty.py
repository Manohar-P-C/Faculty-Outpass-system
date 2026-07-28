import mysql.connector

# DB Config
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

faculties = [
    ("Dr. Padma Reddy A M", "Dean-Student Affairs & Professor"),
    ("Dr. Nagashree N", "Associate Professor & HOD"),
    ("Dr. Pushpalatha K N", "Professor"),
    ("Dr. Dhivyashri G", "Associate Professor"),
    ("Dr. Bhavana A", "Associate Professor"),
    ("Prof. Anitha C S", "Assistant Professor"),
    ("Prof. Nisha S K", "Assistant Professor"),
    ("Prof. Jyoti Kumari", "Assistant Professor"),
    ("Prof. Pavithra B", "Assistant Professor"),
    ("Prof. Amaranath", "Assistant Professor"),
    ("Prof. Shwetha H C", "Assistant Professor"),
    ("Prof. Bhavya T N", "Assistant Professor"),
    ("Prof. Lakshmi Durga N", "Assistant Professor"),
    ("Prof. Kayalvizhi V", "Assistant Professor"),
    ("Prof. Pulukuri Aparna", "Assistant Professor"),
    ("Prof. Mahesh C Arali", "POP Professor"),
    ("Prof. Vidyashree R", "POP Assistant Professor"),
]

def add_csds_faculty():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    # 1. Update the Dummy HOD to be the real HOD
    hod_email = "nagashreen.csds@svit.edu"
    cursor.execute("""
        UPDATE hods 
        SET name = %s, email = %s
        WHERE department = 'CSDS'
    """, ("Dr. Nagashree N", hod_email))
    print("Updated CSDS HOD from Dummy to Dr. Nagashree N.")
    
    count = 0
    for name, designation in faculties:
        # Generate a simple email based on the name
        clean_name = name.replace("Dr. ", "").replace("Prof. ", "").replace(" ", "").replace("-", "").lower()
        email = f"{clean_name}.csds@svit.edu"
        password = "password123" # Default password
        department = "CSDS"
        
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
    print(f"\nSuccessfully added {count} faculty members to the CSDS department.")

if __name__ == "__main__":
    add_csds_faculty()
