# -*- coding: utf-8 -*-
"""
Live diagnostic: checks DB connection and SMTP config.
Run: python check_smtp_db.py
"""
import os, sys

# ── Load .env ──────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[.env] Loaded .env file")
except ImportError:
    print("[.env] python-dotenv not installed - reading OS env only")

# ─────────────────────────────────────────────
# 1. DATABASE CHECK
# ─────────────────────────────────────────────
print("\n" + "="*60)
print("  DATABASE CHECK")
print("="*60)

DB_HOST     = os.environ.get("DB_HOST",     "localhost")
DB_USER     = os.environ.get("DB_USER",     "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "manohar2129")
DB_NAME     = os.environ.get("DB_NAME",     "college_db")
DB_PORT     = int(os.environ.get("DB_PORT", 3306))

print(f"  Host     : {DB_HOST}:{DB_PORT}")
print(f"  User     : {DB_USER}")
print(f"  Database : {DB_NAME}")
print(f"  Password : {'*' * len(DB_PASSWORD) if DB_PASSWORD else '(not set)'}")

db_ok = False
try:
    import mysql.connector
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, port=DB_PORT, connection_timeout=5
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [r[0] for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    print(f"\n  [OK] DB CONNECTED  ({len(tables)} tables)")
    print(f"  Tables: {', '.join(tables) if tables else '(none)'}")
    db_ok = True
except Exception as e:
    print(f"\n  [FAIL] DB CONNECTION FAILED")
    print(f"  Error: {e}")
    print("\n  --> Make sure MySQL Server is running (Start -> Services -> MySQL)")

# ─────────────────────────────────────────────
# 2. SMTP CHECK
# ─────────────────────────────────────────────
print("\n" + "="*60)
print("  SMTP / EMAIL CHECK")
print("="*60)

SENDER_EMAIL    = os.environ.get("SENDER_EMAIL",    "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

print(f"  SENDER_EMAIL    : {SENDER_EMAIL if SENDER_EMAIL else '(NOT SET)'}")
print(f"  SENDER_PASSWORD : {'*' * len(SENDER_PASSWORD) if SENDER_PASSWORD else '(NOT SET)'}")

smtp_ok = False
if not SENDER_EMAIL or not SENDER_PASSWORD:
    print("\n  [WARNING] SMTP credentials missing - app will run in DEV MODE")
    print("  Emails will be printed to terminal, NOT actually sent.")
    print("\n  --> To fix, create a .env file with:")
    print("      SENDER_EMAIL=your_gmail@gmail.com")
    print("      SENDER_PASSWORD=your_16_char_app_password")
else:
    print("\n  Testing SMTP connection to smtp.gmail.com:587 ...")
    import smtplib
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.quit()
        print("  [OK] SMTP LOGIN SUCCESSFUL - emails will be sent normally")
        smtp_ok = True
    except smtplib.SMTPAuthenticationError:
        print("  [FAIL] SMTP AUTH FAILED - wrong email/password")
        print("  --> Go to Google Account -> Security -> App Passwords -> generate one")
    except Exception as e:
        print(f"  [FAIL] SMTP ERROR: {e}")

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
print("\n" + "="*60)
print("  SUMMARY")
print("="*60)
print(f"  Database : {'CONNECTED' if db_ok  else 'NOT CONNECTED - start MySQL!'}")
print(f"  SMTP     : {'CONFIGURED & WORKING' if smtp_ok else 'NOT CONFIGURED (dev mode)' if not SENDER_EMAIL else 'CONFIGURED BUT FAILED'}")
print("="*60 + "\n")
