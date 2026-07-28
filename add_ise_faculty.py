import mysql.connector

# DB Config
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

faculties = [
    ("Dr. Vrinda Shetty", "Professor & HOD"),
    ("Dr. Vijayashree R Budyal", "Professor"),
    ("Dr. Priya Arundhati", "Associate Professor"),
    ("Prof. A M Shivaram", "Associate Professor"),
    ("Dr. Prasanna Lakshmi G S", "Associate Professor"),
    ("Dr. Amogh Pramod Kulkarni", "Associate Professor"),
    ("Prof. Santosh Y N", "Assistant Professor"),
    ("Prof. Deepa Pattan", "Assistant Professor"),
    ("Prof. Radha R", "Assistant Professor"),
    ("Prof. Vidya H A", "Assistant Professor"),
    ("Prof. Navya B R", "Assistant Professor"),
    ("Prof. Swathi C S", "Assistant Professor"),
    ("Prof. Divyamani M K", "Assistant Professor"),
    ("Prof. Thanuja M", "Assistant Professor"),
    ("Prof. Daniel D", "Assistant Professor"),
    ("Prof. Chaitra C", "Assistant Professor"),
    ("Prof. Pratibha Pujari", "Assistant Professor"),
    ("Prof. Nagamahesh B S", "POP Assistant Professor"),
]

def add_ise_faculty():
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
        clean_name = name.replace("Dr. ", "").replace("Prof. ", "").replace(" ", "").lower()
        email = f"{clean_name}.ise@svit.edu"
        password = "password123" # Default password
        department = "ISE"
        
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
    print(f"\nSuccessfully added {count} faculty members to the ISE department.")

if __name__ == "__main__":
    add_ise_faculty()
