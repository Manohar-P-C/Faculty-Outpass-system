"""
Add CSE Department Faculty Members
Run this script once to insert all 29 CSE faculty into the database.
"""

import mysql.connector

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "manohar2129"
DB_NAME = "college_db"

faculty_list = [
    ("Dr. Manjunath T N",       "manjunath.tn@svit.edu",       "faculty123", "CSE", "", "Principal & Professor"),
    ("Dr. Shashikumar D R",     "shashikumar.dr@svit.edu",     "faculty123", "CSE", "", "Professor & HOD"),
    ("Dr. Shantakumar B Patil", "shantakumar.bp@svit.edu",     "faculty123", "CSE", "", "Professor & Associate Dean"),
    ("Dr. Tejashwini N",        "tejashwini.n@svit.edu",       "faculty123", "CSE", "", "Associate Professor"),
    ("Dr. Ajay V G",            "ajay.vg@svit.edu",            "faculty123", "CSE", "", "Associate Professor"),
    ("Dr. Varun E",             "varun.e@svit.edu",            "faculty123", "CSE", "", "Associate Professor"),
    ("Dr. Vinod Desai",         "vinod.desai@svit.edu",        "faculty123", "CSE", "", "Associate Professor"),
    ("Dr. Ramesh N Koppar",     "ramesh.koppar@svit.edu",      "faculty123", "CSE", "", "Associate Professor"),
    ("Dr. Srivinay",            "srivinay@svit.edu",           "faculty123", "CSE", "", "Associate Professor"),
    ("Prof. Manjusha",          "manjusha@svit.edu",           "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. H S Poornima Gowda","poornima.gowda@svit.edu",    "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Deepika G",         "deepika.g@svit.edu",          "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Sunil Kumar B",     "sunil.kumar@svit.edu",        "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Madhura N",         "madhura.n@svit.edu",          "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. G Ramanjinamma",    "ramanjinamma.g@svit.edu",     "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Sowmya H N",        "sowmya.hn@svit.edu",          "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Jayaprada S Hiremath","jayaprada.sh@svit.edu",     "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Pavithra B G",      "pavithra.bg@svit.edu",        "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. K Lalitha",         "lalitha.k@svit.edu",          "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Koushika K H",      "koushika.kh@svit.edu",        "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Lokesh Kumar Balaji","lokesh.balaji@svit.edu",     "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Anila Davis",       "anila.davis@svit.edu",        "faculty123", "CSE", "", "Assistant Professor"),
    ("Dr. H R Ravi Kumar",      "ravikumar.hr@svit.edu",       "faculty123", "CSE", "", "Assistant Professor"),
    ("Dr. Gautam Amiya",        "gautam.amiya@svit.edu",       "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Sahana G C",        "sahana.gc@svit.edu",          "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Arathi B N",        "arathi.bn@svit.edu",          "faculty123", "CSE", "", "Assistant Professor"),
    ("Prof. Manoj C",           "manoj.c@svit.edu",            "faculty123", "CSE", "", "POP Professor"),
    ("Prof. Sangeeta Arali",    "sangeeta.arali@svit.edu",     "faculty123", "CSE", "", "POP Associate Professor"),
    ("Prof. Nandeesh P S",      "nandeesh.ps@svit.edu",        "faculty123", "CSE", "", "POP Assistant Professor"),
]

def main():
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor()

    added = 0
    skipped = 0

    for name, email, password, dept, phone, designation in faculty_list:
        try:
            cursor.execute(
                "INSERT INTO faculty (name, email, password, department, phone, designation) VALUES (%s,%s,%s,%s,%s,%s)",
                (name, email, password, dept, phone, designation)
            )
            added += 1
            print(f"  [+] Added: {name} ({email})")
        except mysql.connector.IntegrityError:
            skipped += 1
            print(f"  [~] Skipped (already exists): {name} ({email})")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\nDone! Added: {added}, Skipped: {skipped}")

if __name__ == "__main__":
    print("=" * 50)
    print("Adding 29 CSE Faculty Members")
    print("=" * 50)
    main()
