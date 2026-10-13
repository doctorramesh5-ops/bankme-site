import os,sys,shutil,time
f='app.html'
if not os.path.exists(f): sys.exit('Run this inside ~/Desktop/bankme-site')
s=open(f).read()
pairs=[
 ("+[100,500,1000,2000,5000].map(function(a){\n        return '<button onclick=\"document.getElementById(\\'wa-amount\\')",
  "+[].map(function(a){ /* QUICKAMT_OFF */\n        return '<button onclick=\"document.getElementById(\\'wa-amount\\')"),
 ("+[500,1000,2000,5000].map(function(a){\n        return '<button onclick=\"document.getElementById(\\'wd-amount\\')",
  "+[].map(function(a){ /* QUICKAMT_OFF */\n        return '<button onclick=\"document.getElementById(\\'wd-amount\\')"),
]
if s.count('QUICKAMT_OFF')>=2: print('Already applied.'); sys.exit(0)
for a,b in pairs:
    if s.count(a)!=1: sys.exit('Anchor not found exactly once (%d) - nothing changed.'%s.count(a))
shutil.copy(f,f+'.bak.'+time.strftime('%Y%m%d%H%M%S'))
for a,b in pairs: s=s.replace(a,b)
open(f,'w').write(s); print('Applied OK: quick amount buttons removed from Wallet add/withdraw.')
