#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website: removes the partner name "Eko" from everything a retailer/customer SEES (AEPS activation,
onboarding, status messages, DMT). Admin screens, API paths and code are NOT touched.
 "Eko retailer code" -> "BankMe Agent ID", one-time setup -> "BankMe AePS Activation", etc.
Afterwards it lists any remaining "Eko" text so nothing is missed.
Usage:  cd ~/Desktop/bankme-site && python3 brand_web.py
"""
import sys, re, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
# (old, new) - order matters, longest first
R = [
 ("Creating your Eko retailer code…", "Activating your BankMe AePS…"),
 ("Verifying your PAN with Eko. This", "Verifying your PAN. This"),
 ("Create my Eko retailer code →", "Activate my BankMe AePS →"),
 ("Eko retailer code created", "BankMe AePS activated"),
 ("Eko retailer onboarding (one time)", "BankMe AePS Activation (one time)"),
 ("Your account has no Eko retailer code yet.", "Your BankMe AePS is not activated yet."),
 ("not linked to an Eko retailer code", "not activated for BankMe AePS"),
 ("Eko retailer code", "BankMe Agent ID"),
 ("Eko code ", "Agent ID "),
 ("Submit Activation to Eko →", "Submit Activation →"),
 ("Activation submitted to Eko", "Activation submitted"),
 ("Eko will review and approve your AEPS service.", "BankMe will review and approve your AEPS service."),
 ("Eko may take time to approve", "Approval may take some time"),
 ("go to Eko for KYC", "go to our banking partner for KYC"),
 ("sent securely to Eko", "sent securely to our banking partner"),
 ("Eko could not onboard this retailer.", "We could not activate this retailer."),
 ("Check status with Eko", "Check status"),
 ("Checking with Eko…", "Checking status…"),
 ("Confirmed by Eko", "Confirmed"),
 ("until Eko confirms", "until the bank network confirms"),
 ("per Eko transaction", "per transaction"),
 ("Verifying sender with Eko…", "Verifying sender…"),
 ("NPCI DMT via Eko", "NPCI DMT"),
]
n = 0
for o, new in R:
    k = c.count(o)
    if k:
        c = c.replace(o, new); n += k
if n == 0:
    print("Nothing to change (already applied, or the texts differ).")
else:
    shutil.copy(FILE, FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    open(FILE, "w", encoding="utf-8").write(c)
    print("OK: %d visible 'Eko' texts replaced." % n)
print("\nRemaining 'Eko' text (admin pages are expected here; send any user-facing lines to Claude):")
for i, line in enumerate(c.split("\n"), 1):
    for m in re.finditer(r"(?<![A-Za-z_/.])Eko(?![A-Za-z_])", line):
        s = max(0, m.start() - 60); print("%d: ...%s" % (i, line[s:m.end() + 60].strip())); break
