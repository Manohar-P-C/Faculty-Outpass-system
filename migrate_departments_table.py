import mysql.connector
from db_setup import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def migrate_departments():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        # 1. Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                icon VARCHAR(10) DEFAULT '🏫',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Created departments table.")

        # 2. Seed initial 13 departments if table is empty
        cursor.execute("SELECT COUNT(*) FROM departments")
        count = cursor.fetchone()[0]
        if count == 0:
            default_depts = [
                ("CSE", "Computer Science & Engineering", "💻"),
                ("AI", "Artificial Intelligence & Machine Learning", "🤖"),
                ("ISE", "Information Science & Engineering", "🖥️"),
                ("ECE", "Electronics & Communication Engineering", "📡"),
                ("CIVIL", "Civil Engineering", "🏗️"),
                ("MECH", "Mechanical Engineering", "⚙️"),
                ("MATHS", "Mathematics", "📐"),
                ("PHYSICS", "Physics", "🔬"),
                ("CHEM", "Chemistry", "⚗️"),
                ("MBA", "Master of Business Administration", "📊"),
                ("CSDS", "Computer Science & Data Science", "💾"),
                ("CSCY", "Computer Science & Cyber Security", "🛡️"),
                ("CSBS", "Computer Science & Business Studies", "💼")
            ]
            cursor.executemany("""
                INSERT INTO departments (code, name, icon)
                VALUES (%s, %s, %s)
            """, default_depts)
            print(f"[OK] Seeded {len(default_depts)} default departments.")
        else:
            print(f"[INFO] Departments table already contains {count} records.")

        conn.commit()
        cursor.close()
        conn.close()
        print("[SUCCESS] Departments migration complete!")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")

if __name__ == "__main__":
    migrate_departments()
