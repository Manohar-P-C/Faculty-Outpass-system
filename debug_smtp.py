# -*- coding: utf-8 -*-
"""Deep SMTP debug - shows exact server response at each step"""
import os, smtplib, ssl

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

EMAIL    = os.environ.get("SENDER_EMAIL", "")
PASSWORD = os.environ.get("SENDER_PASSWORD", "")

print(f"Email   : {EMAIL}")
print(f"Password: {'*' * len(PASSWORD)} ({len(PASSWORD)} chars)")
print()

# ── Test 1: Port 587 (STARTTLS) ────────────────────────────
print("--- Test 1: smtp.gmail.com:587 (STARTTLS) ---")
try:
    smtp = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
    smtp.set_debuglevel(1)   # prints every server response
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(EMAIL, PASSWORD)
    smtp.quit()
    print("\n[OK] Port 587 LOGIN SUCCESSFUL")
except Exception as e:
    print(f"\n[FAIL] Port 587 error: {type(e).__name__}: {e}")

print()

# ── Test 2: Port 465 (SSL) ─────────────────────────────────
print("--- Test 2: smtp.gmail.com:465 (SSL) ---")
try:
    context = ssl.create_default_context()
    smtp2 = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15, context=context)
    smtp2.set_debuglevel(1)
    smtp2.login(EMAIL, PASSWORD)
    smtp2.quit()
    print("\n[OK] Port 465 LOGIN SUCCESSFUL")
except Exception as e:
    print(f"\n[FAIL] Port 465 error: {type(e).__name__}: {e}")
