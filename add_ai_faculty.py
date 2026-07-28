import mysql.connector

# DB Config
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

faculties = [
    ("Dr. T G Manjunatha", "Professor & HOD"),
    ("Dr. Vikramathithan A C", "Professor"),
    ("Dr. Priti Mishra", "Professor"),
    ("Dr. Kumaresh Sheelavant", "Associate Professor"),
    ("Dr. Sukruth Gowda M A", "Associate Professor"),
    ("Prof. Rekha Murthy", "Assistant Professor"),
    ("Prof. Anitha M C", "Assistant Professor"),
    ("Prof. Jayshri", "Assistant Professor"),
    ("Prof. Shilpa Patil", "Assistant Professor"),
    ("Prof. Pooja A", "Assistant Professor"),
    ("Prof. Soumya L N", "Assistant Professor"),
    ("Prof. Geetha M", "Assistant Professor"),
    ("Prof. Shail Kumari Shah", "Assistant Professor"),
    ("Prof. Resmi S", "Assistant Professor"),
    ("Prof. Pooja Snehal Janwe", "Assistant Professor"),
    ("Prof. Deepika G S", "Assistant Professor"),
    ("Prof. Nazia Nusrat Ul Ain", "Assistant Professor"),
    ("Prof. Raghu Prasad G S", "POP Professor"),
    ("Prof. Priyanka S Mandakki", "POP Assistant Professor"),
]

def add_ai_faculty():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    count = 0
    for name, designation in faculties:
        # Generate a simple email based on the name
        # e.g., "Dr. T G Manjunatha" -> "tgmanjunatha.ai@svit.edu"
        clean_name = name.replace("Dr. ", "").replace("Prof. ", "").replace(" ", "").lower()
        email = f"{clean_name}.ai@svit.edu"
        password = "password123" # Default password
        department = "AI"
        
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
    print(f"\nSuccessfully added {count} faculty members to the AI department.")

if __name__ == "__main__":
    add_ai_faculty()
