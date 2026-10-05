#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixes the DMT OTP input label on the website — it said "6-digit OTP" but
real OTPs vary by the sender's bank (Fino Payments Bank sends 4 digits).
Validation already accepts any length >= 4, so this was purely a display
mismatch. Also removes the maxlength=6 cap so a 4-digit OTP isn't visually
cramped or a longer one ever gets truncated.

Safe by design: the block below must match the CURRENT file text EXACTLY
ONCE before anything is written.

Usage:
    cd ~/Desktop/bankme-site
    python3 fix_dmt_otp_label.py
"""
import sys, shutil, datetime

FILE = "app.html"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

old = """          '<label class="flabel">Enter OTP sent to '+DMT.senderMobile+'</label>'
          +'<input class="finp" id="dmt-otp" maxlength="6" placeholder="6-digit OTP"/>'"""

new = """          '<label class="flabel">Enter OTP sent to '+DMT.senderMobile+'</label>'
          +'<input class="finp" id="dmt-otp" maxlength="8" placeholder="Enter OTP"/>'"""

count = content.count(old)
if count != 1:
    print(f"❌ Expected to find the target text exactly once, found {count}.")
    print("   -> Your file has changed since this script was written against it.")
    print("   -> Nothing has been written. Tell Claude and paste the relevant section fresh.")
    sys.exit(1)

content = content.replace(old, new, 1)

backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Fix applied successfully in {FILE}")
print(f"   Backup of the previous version saved as {backup}")
