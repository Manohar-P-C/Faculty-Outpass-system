import mysql.connector
from db_setup import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

try:
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()
    for table in ["hods", "faculty", "security"]:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN photo VARCHAR(255)")
            print(f"Added photo column to {table}")
        except Exception as e:
            print(f"Column may already exist in {table}: {e}")
    conn.commit()
    cursor.close()
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")
