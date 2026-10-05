#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrects the previous fix_bbps_zero_amount.py patch, which was too strict.

Real-world finding: TNEB (and other billers) legitimately show ₹0.00 when
there's no bill due this cycle (confirmed directly against TNEB's own
website for the same consumer number). The previous patch rejected ANY
zero amount as an error, which would also wrongly reject a real "nothing
due" bill. This patch removes that overly strict check, while keeping the
original, correct check: reject only when Eko sends back an error-shaped
payload with no amount field at all (e.g. {"message":"No key for Response"}),
which happens if you re-fetch the same bill too soon.

Safe by design: the block below must match the CURRENT file text EXACTLY
ONCE before anything is written. If it doesn't match, nothing is written.

Usage:
    cd ~/Desktop/bankme-site
    python3 fix_bbps_allow_zero_due.py
"""
import sys, shutil, datetime

FILE = "app.html"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

old = """    var d=(j&&j.data)||j||{};
    if(d&&d.message&&d.amount==null&&d.bill_amount==null){ throw new Error(d.message||'Could not fetch bill. Please wait a few seconds and try again.'); }
    var billAmt=Number(d.amount||d.bill_amount||0);
    if(!billAmt||billAmt<=0){ throw new Error('Could not fetch a valid bill amount. Please wait a few seconds and try again, or enter the amount manually.'); }"""

new = """    var d=(j&&j.data)||j||{};
    if(d&&d.message&&d.amount==null&&d.bill_amount==null){ throw new Error(d.message||'Could not fetch bill. Please wait a few seconds and try again.'); }
    var billAmt=Number(d.amount||d.bill_amount||0);
    // Note: ₹0 is a legitimate "nothing due this cycle" result for many
    // billers (confirmed against TNEB directly) — do NOT treat it as an error."""

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
