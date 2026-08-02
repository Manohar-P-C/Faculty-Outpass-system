"""
Helper script to quickly assign an HOD Assistant Name & Phone Number to a Department
Usage: python set_assistant.py <DEPARTMENT> <ASSISTANT_NAME> <ASSISTANT_PHONE> [TIMEOUT_MINUTES]
Example: python set_assistant.py CSE "Ramesh (Assistant)" "+919876543210" 15
"""

import sys
from db_setup import get_connection

def set_assistant(department, name, phone, timeout=15):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Format phone number cleanly
        phone = phone.strip()
        if not phone.startswith("+") and len(phone) == 10 and phone.isdigit():
            phone = "+91" + phone

        cursor.execute("""
            UPDATE hods 
            SET assistant_name = %s, assistant_phone = %s, escalation_timeout_mins = %s, ai_call_enabled = 1
            WHERE department = %s
        """, (name, phone, int(timeout), department.upper()))
        
        updated_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        if updated_rows > 0:
            print(f"[SUCCESS] Updated {department.upper()} HOD Assistant to '{name}' ({phone}) with timeout = {timeout} mins.")
        else:
            print(f"[WARNING] No HOD found for department '{department.upper()}'. Please verify department code.")
    except Exception as e:
        print(f"[ERROR] Failed to set assistant: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python set_assistant.py <DEPARTMENT> <ASSISTANT_NAME> <ASSISTANT_PHONE> [TIMEOUT_MINUTES]")
        print("Example: python set_assistant.py CSE 'John Assistant' '+919876543210' 15")
    else:
        dept = sys.argv[1]
        asst_name = sys.argv[2]
        asst_phone = sys.argv[3]
        timeout_mins = sys.argv[4] if len(sys.argv) > 4 else 15
        set_assistant(dept, asst_name, asst_phone, timeout_mins)
