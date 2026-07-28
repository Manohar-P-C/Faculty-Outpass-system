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

def list_principals():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM principal")
        principals = cursor.fetchall()
        
        print("\n--- Current Principals / Vice Principals ---")
        if not principals:
            print("No accounts found.")
        else:
            for p in principals:
                print(f"ID: {p['id']} | Name: {p['name']} | Email: {p['email']}")
        print("--------------------------------------------\n")
        return principals
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def remove_principal(email):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT id, name FROM principal WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"Error: No account found with email '{email}'.")
            return

        # Confirm before deleting
        confirm = input(f"Are you sure you want to remove '{user[1]}' ({email})? (y/n): ")
        if confirm.lower() == 'y':
            cursor.execute("DELETE FROM principal WHERE email = %s", (email,))
            conn.commit()
            print(f"[SUCCESS] Successfully removed {user[1]} ({email}) from the database.")
        else:
            print("Operation cancelled.")
            
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Remove Principal / Vice Principal")
    print("=" * 50)
    
    list_principals()
    
    if len(sys.argv) >= 2:
        email = sys.argv[1]
        remove_principal(email)
    else:
        email = input("Enter the Email of the account you want to remove (or press Enter to exit): ")
        if email.strip():
            remove_principal(email.strip())
