#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website side of the AEPS commission split. Run AFTER pending_aeps_web.py and after the
backend script commission_split_backend.py is deployed. Admin account only matters for the sync parts.

 1) Assign screens: every Assign now also tells the backend (by mobile number)
 2) Commission screen: Save also stores the table in the backend
 3) New one-time helper  syncNetworkToBackend()  copies ALL existing assignments + the table
 4) AEPS receipt shows "Commission earned"

Usage:  cd ~/Desktop/bankme-site && python3 commission_split_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
R = []

R.append(("receipt data",
r"""credited: j.credited, creditFailed: !!j.creditFailed };""",
r"""credited: j.credited, commission: j.commission, creditFailed: !!j.creditFailed };"""))

R.append(("receipt row",
r"""    if (r.credited) rows.push(['Credited to your wallet', '\u20B9' + fmtN(r.credited)]);""",
r"""    if (r.credited) rows.push(['Credited to your wallet', '\u20B9' + fmtN(r.credited)]);
    if (r.commission) rows.push(['Commission earned', '\u20B9' + fmtN(r.commission)]);"""))

R.append(("assign -> backend",
"""    // Update local copy
    var all=window._assignUsers||[];
    for(var i=0;i<all.length;i++){
      if(all[i].uid===userUid){ all[i].assignedTo=parentUid||null; break; }
    }""",
"""    await syncLinkToBackend(userUid, parentUid);
    // Update local copy
    var all=window._assignUsers||[];
    for(var i=0;i<all.length;i++){
      if(all[i].uid===userUid){ all[i].assignedTo=parentUid||null; break; }
    }"""))

R.append(("commission save -> backend",
"""  try{ localStorage.setItem('bankme_commdata', JSON.stringify(window._commData)); }catch(e){}
  if(db){""",
"""  try{ localStorage.setItem('bankme_commdata', JSON.stringify(window._commData)); }catch(e){}
  syncCommissionToBackend();
  if(db){"""))

R.append(("sync functions",
"async function doAssign(userUid, userRole){",
r"""// ── Network + commission -> backend (AEPS commission split) ──
function aepsNetPhone(p){ return String(p||'').replace(/\D/g,'').slice(-10); }
async function aepsPostAdmin(path, body){
  try {
    var r = await authFetch(BACKEND_URL + path, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
    if (r.status === 401) return { success:false, error:'Session expired - log in again' };
    return await r.json();
  } catch(e){ return { success:false, error:e.message }; }
}
async function syncLinkToBackend(userUid, parentUid){
  var all = window._assignUsers || [];
  var child = all.filter(function(u){ return u.uid===userUid; })[0];
  var parent = parentUid ? all.filter(function(u){ return u.uid===parentUid; })[0] : null;
  if (!child || !child.phone) { toast('Saved here, but this user has no mobile number so the backend was not updated','e'); return; }
  if (parentUid && (!parent || !parent.phone)) { toast('Saved here, but the parent has no mobile number so the backend was not updated','e'); return; }
  var j = await aepsPostAdmin('/admin/network/link', { childPhone: aepsNetPhone(child.phone), parentPhone: parent ? aepsNetPhone(parent.phone) : '' });
  if (!j.success) toast('Saved here, but backend sync failed: ' + (j.error || j.message || 'error'), 'e');
}
async function syncCommissionToBackend(){
  if (!window._commData) return;
  var j = await aepsPostAdmin('/admin/commission', { data: window._commData });
  if (!j.success) toast('Commission saved here, but backend sync failed: ' + (j.error || j.message || 'error'), 'e');
}
// ONE-TIME: run in the browser console while logged in as admin:  syncNetworkToBackend()
async function syncNetworkToBackend(){
  var all = window._assignUsers;
  if (!all) {
    try { var snap = await db.collection('bankme_users').get(); all = []; snap.forEach(function(d){ var u=d.data(); u.uid=d.id; all.push(u); }); }
    catch(e){ console.log('Cannot load users', e); toast('Could not load users','e'); return; }
  }
  var byUid = {}; all.forEach(function(u){ byUid[u.uid] = u; });
  var links = [], skipped = 0;
  all.forEach(function(u){
    if (!u.assignedTo) return;
    var p = byUid[u.assignedTo];
    if (u.phone && p && p.phone) links.push({ childPhone: aepsNetPhone(u.phone), parentPhone: aepsNetPhone(p.phone) }); else skipped++;
  });
  var j1 = await aepsPostAdmin('/admin/network/sync', { links: links });
  var j2 = window._commData ? await aepsPostAdmin('/admin/commission', { data: window._commData }) : { success:false, error:'Open the Commission page once, then run this again' };
  console.log('links found:', links.length, 'skipped (no phone):', skipped, j1, '| commission:', j2);
  toast('Network: ' + (j1.success ? j1.synced + ' links synced' : 'FAILED (' + (j1.error||'') + ')') + ' · Commission: ' + (j2.success ? 'saved' : 'not saved'), (j1.success && j2.success) ? 's' : 'e');
}

async function doAssign(userUid, userRole){"""))

ok = True
for name, o, n in R:
    k = c.count(o)
    if k != 1:
        ok = False; print("ERROR '%s': expected 1 match, found %d" % (name, k))
if not ok:
    print("Nothing written. Tell Claude which line says ERROR."); sys.exit(1)
for name, o, n in R:
    c = c.replace(o, n, 1)
b = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, b)
open(FILE, "w", encoding="utf-8").write(c)
print("OK: %d changes applied. Backup: %s" % (len(R), b))
