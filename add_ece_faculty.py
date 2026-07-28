import mysql.connector

# DB Config
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

faculties = [
    ("Dr. Jayasimha Y", "Dean-Academics & Professor"),
    ("Prof. Shanmukha Swamy R C", "Dean-Administration & Professor"),
    ("Dr. Venkatesha M", "Professor & HOD"),
    ("Dr. Chaya B M", "Associate Professor"),
    ("Dr. Vani B P", "Associate Professor"),
    ("Dr. Suryanarayana N K", "Associate Professor"),
    ("Dr. Pavithra G S", "Associate Professor"),
    ("Prof. Nayana K", "Assistant Professor"),
    ("Prof. Praveen B R", "Assistant Professor"),
    ("Prof. Amulya H G", "Assistant Professor"),
    ("Prof. Darshan R V", "Assistant Professor"),
    ("Prof. Akshith Monnappa K", "Assistant Professor"),
    ("Prof. Prabha K", "Assistant Professor"),
    ("Prof. Advaith P R", "Assistant Professor"),
    ("Prof. Nagayya S Hiremath", "Assistant Professor"),
    ("Prof. Divya T M", "Assistant Professor"),
    ("Prof. Tejashree S", "Assistant Professor"),
    ("Dr. Ajay Kumar N", "Assistant Professor"),
    ("Prof. Manjuvani K M", "Assistant Professor"),
    ("Prof. Shruthi N", "Assistant Professor"),
    ("Prof. Shashank S Bhagwat", "Assistant Professor"),
    ("Prof. Kalyani Kandraju", "Assistant Professor"),
    ("Prof. Monisha Uday", "Assistant Professor"),
    ("Prof. Akshatha V Kulkarni", "Assistant Professor"),
]

def add_ece_faculty():
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
        clean_name = name.replace("Dr. ", "").replace("Prof. ", "").replace(" ", "").replace("-", "").lower()
        email = f"{clean_name}.ece@svit.edu"
        password = "password123" # Default password
        department = "ECE"
        
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
    print(f"\nSuccessfully added {count} faculty members to the ECE department.")

if __name__ == "__main__":
    add_ece_faculty()
