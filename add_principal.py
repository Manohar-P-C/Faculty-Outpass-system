import mysql.connector
import sys

# -----------------------
# DATABASE CONFIG
# -----------------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"  # Ensure this is your correct MySQL password
DB_NAME = "college_db"

def get_db():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

def add_principal(name, email, password, phone=""):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM principal WHERE email = %s", (email,))
        if cursor.fetchone():
            print(f"Error: A principal or vice principal with email '{email}' already exists.")
            return

        # Insert new account
        cursor.execute("""
            INSERT INTO principal (name, email, password, phone)
            VALUES (%s, %s, %s, %s)
        """, (name, email, password, phone))
        
        conn.commit()
        print(f"[SUCCESS] Successfully added {name} ({email}) to the principal database!")
        print("They can now log in through the Principal Login portal.")
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Add New Principal / Vice Principal")
    print("=" * 50)
    
    # If arguments are passed via command line
    if len(sys.argv) >= 4:
        name = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
        phone = sys.argv[4] if len(sys.argv) > 4 else ""
    else:
        # Interactive mode
        name = input("Enter Name (e.g., Vice Principal Ramesh): ")
        email = input("Enter Email: ")
        password = input("Enter Password: ")
        phone = input("Enter Phone (Optional): ")
        
    if name and email and password:
        add_principal(name, email, password, phone)
    else:
        print("Error: Name, Email, and Password are required.")
