import mysql.connector
from db_setup import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def migrate():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()
    
    # Tables to add photo column
    for table in ["principal", "hods", "faculty", "security"]:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN photo VARCHAR(255)")
            print(f"Added 'photo' to {table}")
        except:
            print(f"'photo' already exists in {table}")

    # Faculty requests missing columns
    try:
        cursor.execute("ALTER TABLE faculty_requests ADD COLUMN proof VARCHAR(255)")
        print("Added 'proof' to faculty_requests")
    except:
        print("'proof' already exists in faculty_requests")

    try:
        cursor.execute("ALTER TABLE faculty_requests ADD COLUMN request_date DATE")
        print("Added 'request_date' to faculty_requests")
    except:
        print("'request_date' already exists in faculty_requests")

    conn.commit()
    cursor.close()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
