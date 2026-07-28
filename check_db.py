import mysql.connector
from db_setup import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

try:
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor(dictionary=True)
    for table in ["hods", "faculty", "security"]:
        cursor.execute(f"SELECT id, name, photo FROM {table} WHERE photo IS NOT NULL AND photo != ''")
        rows = cursor.fetchall()
        for r in rows:
            print(f"{table} ID {r['id']} ({r['name']}): {r['photo']}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")
