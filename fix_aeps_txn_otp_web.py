#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eko confirmed: for withdrawals above Rs 5,000 the customer's 6-digit SMS OTP must go in the
'otp' attribute of the PidOptions BEFORE the fingerprint capture (in addition to
txn_otp_request_id). The wizard now asks for that OTP on the capture screen and sends it.
Run after secure_and_wallet_aeps_web.py.

Usage:  cd ~/Desktop/bankme-site && python3 fix_aeps_txn_otp_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
R = []

R.append(("capture signature",
"async function aepsCaptureFinger(wadh){",
"async function aepsCaptureFinger(wadh, otp){\n  otp = String(otp || '').replace(/\\D/g, '');"))

R.append(("PidOptions otp",
"wadh=\"' + (wadh || '') + '\" posh=\"UNKNOWN\"",
"wadh=\"' + (wadh || '') + '\" otp=\"' + otp + '\" posh=\"UNKNOWN\""))

R.append(("OTP field on capture screen",
"    + '<button onclick=\"aepsCustomerGo()\" class=\"btn-primary\">",
"    + (txnOtpId ? '<label class=\"flabel\">Customer\\'s 6-digit SMS OTP</label><input class=\"finp\" id=\"m-txn-otp\" type=\"tel\" maxlength=\"6\" placeholder=\"OTP sent to the customer\\'s Aadhaar-linked mobile\" style=\"letter-spacing:6px;font-size:1.2rem;font-weight:700;text-align:center\" oninput=\"this.value=this.value.replace(/[^0-9]/g,\\'\\')\"/>' : '')\n    + '<button onclick=\"aepsCustomerGo()\" class=\"btn-primary\">"))

R.append(("read OTP before scan",
"  var p = AEPS_LIVE.pending; if (!p) return renderAEPSStep3();\n  aepsBusy(3, 'Scanning…', 'Ask the customer to keep the finger on the device');\n  var cap = await aepsCaptureFinger('');",
"""  var p = AEPS_LIVE.pending; if (!p) return renderAEPSStep3();
  var txnOtp = '';
  if (p.txnOtpId) {
    txnOtp = ((document.getElementById('m-txn-otp') || {}).value || '').replace(/\\D/g, '');
    if (txnOtp.length !== 6) { toast("Enter the customer's 6-digit SMS OTP", 'e'); return; }
  }
  aepsBusy(3, 'Scanning…', 'Ask the customer to keep the finger on the device');
  var cap = await aepsCaptureFinger('', txnOtp);"""))

ok = True
for name, o, n in R:
    k = c.count(o)
    if k != 1:
        ok = False; print("ERROR '%s': expected 1 match, found %d" % (name, k))
if not ok:
    print("Nothing written. Tell Claude."); sys.exit(1)
for name, o, n in R:
    c = c.replace(o, n, 1)
b = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, b)
open(FILE, "w", encoding="utf-8").write(c)
print("OK: %d changes applied. Backup: %s" % (len(R), b))
