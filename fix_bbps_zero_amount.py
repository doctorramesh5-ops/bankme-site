#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Second follow-up fix for BBPS on the website (app.html).

Real bug found during testing: if you fetch the same bill again too soon,
Eko's BBPS gateway refuses to re-send the data and returns something like
  {"success": true, "data": {"message": "No key for Response"}}
Our code was treating "success: true" at face value and showing a fake
"Bill Fetched Successfully" card with a ₹0.00 amount — a real bill should
never show up as ₹0, so this patches fetchBBPSBill to treat a missing/zero
amount as a failed fetch (with a clear retry message) instead of a success.

Safe by design: the block below must match the CURRENT file text EXACTLY
ONCE before anything is written. If it doesn't match, nothing is written.

Usage:
    cd ~/Desktop/bankme-site
    python3 fix_bbps_zero_amount.py
"""
import sys, shutil, datetime

FILE = "app.html"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

old = """    var d=(j&&j.data)||j||{};
    var billAmt=Number(d.amount||d.bill_amount||0);"""

new = """    var d=(j&&j.data)||j||{};
    if(d&&d.message&&d.amount==null&&d.bill_amount==null){ throw new Error(d.message||'Could not fetch bill. Please wait a few seconds and try again.'); }
    var billAmt=Number(d.amount||d.bill_amount||0);
    if(!billAmt||billAmt<=0){ throw new Error('Could not fetch a valid bill amount. Please wait a few seconds and try again, or enter the amount manually.'); }"""

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
