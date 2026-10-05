#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website Assign screen: adds a SUPER DISTRIBUTOR column to "Assign Retailers".
 - Pick a distributor  -> the retailer sits under that distributor (its super distributor is shown automatically)
 - No distributor, pick a super distributor -> the retailer is linked DIRECTLY to the super distributor
   (the commission split then pays that super distributor its share and skips the distributor share)
"Assign Distributors" keeps working as before.

Usage:  cd ~/Desktop/bankme-site && python3 assign_sd_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
if 'id="assign-sd-web"' in c:
    sys.exit("Already applied. Nothing written.")
if c.count("function showAssignTab(type){") != 1 or c.count("async function doAssign(userUid, userRole){") != 1:
    sys.exit("ERROR: showAssignTab/doAssign not found exactly once. Nothing written. Tell Claude.")
pos = c.rfind("</body>")
if pos < 0 or c[pos + len("</body>"):].strip() != "</html>":
    sys.exit("ERROR: unexpected end of file. Nothing written.")

JS = r'''
function assignPick(uid){
  var all = window._assignUsers || [];
  var d = document.getElementById('assign-d-' + uid), s = document.getElementById('assign-s-' + uid), h = document.getElementById('assign-sel-' + uid);
  if (!d || !s || !h) return;
  if (d.value) {
    var dist = all.filter(function(p){ return p.uid === d.value; })[0];
    s.value = (dist && dist.assignedTo) ? dist.assignedTo : '';
    s.disabled = true; h.value = d.value;
  } else {
    var was = s.disabled; s.disabled = false; if (was) s.value = ''; h.value = s.value;
  }
}

function showAssignTab(type){
  ['retailer','distributor'].forEach(function(t){
    var btn = document.getElementById('at-' + t); if (!btn) return;
    var isActive = t === type, col = t === 'retailer' ? 'var(--green)' : 'var(--cyan)';
    btn.style.borderColor = isActive ? col : 'var(--border)';
    btn.style.background = isActive ? (t === 'retailer' ? 'rgba(16,185,129,.1)' : 'rgba(6,182,212,.1)') : 'transparent';
    btn.style.color = isActive ? col : 'var(--muted2)';
  });
  var all = window._assignUsers || [];
  var isRet = type === 'retailer';
  var targets = all.filter(function(u){ return u.role === type; });
  var dists = all.filter(function(u){ return u.role === 'distributor'; });
  var sds = all.filter(function(u){ return u.role === 'superdist'; });
  var targetLabel = isRet ? 'Retailer' : 'Distributor';
  var rc = getRC(type), prc = getRC(isRet ? 'distributor' : 'superdist'), src = getRC('superdist');
  var cols = isRet ? '1fr 1fr 1fr 1fr auto' : '1fr 1fr 1fr auto';
  function selStyle(on, col){ return 'width:100%;background:var(--bg3);border:1px solid ' + (on ? col : 'var(--border)') + ';border-radius:7px;padding:5px 8px;color:var(--text);font-size:.74rem;appearance:none'; }

  var html = '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:14px;overflow:auto">'
    + '<div style="min-width:' + (isRet ? '760px' : '560px') + '"><div style="background:var(--bg3);padding:10px 14px;display:grid;grid-template-columns:' + cols + ';gap:8px;font-size:.7rem;color:var(--muted2);font-weight:600;text-transform:uppercase">'
    + '<span>' + targetLabel + ' Name</span><span>Contact</span>' + (isRet ? '<span>Distributor</span><span>Super Distributor</span>' : '<span>Super Distributor</span>') + '<span>Action</span></div>';

  if (!targets.length) {
    html += '<div style="text-align:center;padding:24px;color:var(--muted2)">No ' + targetLabel + 's registered yet</div>';
  } else {
    targets.forEach(function(u){
      var cur = u.assignedTo ? all.filter(function(p){ return p.uid === u.assignedTo; })[0] : null;
      html += '<div style="padding:12px 14px;border-top:1px solid var(--border);display:grid;grid-template-columns:' + cols + ';gap:8px;align-items:center">'
        + '<div style="display:flex;align-items:center;gap:8px;min-width:0"><div style="width:28px;height:28px;border-radius:50%;background:' + rc.color + '22;color:' + rc.color + ';display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.75rem;flex-shrink:0">' + aepsEsc((u.name || 'U')[0].toUpperCase()) + '</div>'
        + '<div style="min-width:0"><div style="font-size:.82rem;font-weight:600;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + aepsEsc(u.name) + '</div>'
        + (u.shopName ? '<div style="font-size:.68rem;color:var(--muted2)">🏪 ' + aepsEsc(u.shopName) + '</div>' : '') + '</div></div>'
        + '<div style="font-size:.75rem;color:var(--muted2)">' + aepsEsc(u.phone || '') + (u.email ? '<br/>' + aepsEsc(String(u.email).split('@')[0]) + '...' : '') + '</div>';
      if (isRet) {
        var distSel = cur && cur.role === 'distributor' ? cur.uid : '';
        var sdSel = cur && cur.role === 'superdist' ? cur.uid : (cur && cur.role === 'distributor' && cur.assignedTo ? cur.assignedTo : '');
        html += '<div><select id="assign-d-' + u.uid + '" onchange="assignPick(\'' + u.uid + '\')" style="' + selStyle(distSel, prc.color) + '"><option value="">-- No distributor --</option>'
          + dists.map(function(p){ return '<option value="' + p.uid + '"' + (distSel === p.uid ? ' selected' : '') + '>' + aepsEsc(p.name) + '</option>'; }).join('') + '</select></div>'
          + '<div><select id="assign-s-' + u.uid + '" onchange="assignPick(\'' + u.uid + '\')" ' + (distSel ? 'disabled' : '') + ' style="' + selStyle(sdSel, src.color) + '"><option value="">-- Unassigned --</option>'
          + sds.map(function(p){ return '<option value="' + p.uid + '"' + (sdSel === p.uid ? ' selected' : '') + '>' + aepsEsc(p.name) + '</option>'; }).join('') + '</select>'
          + (distSel ? '<div style="font-size:.62rem;color:var(--muted2);margin-top:2px">via distributor</div>' : (sdSel ? '<div style="font-size:.62rem;color:' + src.color + ';margin-top:2px">direct to super distributor</div>' : '')) + '</div>'
          + '<input type="hidden" id="assign-sel-' + u.uid + '" value="' + aepsEsc(u.assignedTo || '') + '"/>';
      } else {
        html += '<div><select id="assign-sel-' + u.uid + '" style="' + selStyle(cur, prc.color) + '"><option value="">-- Unassigned --</option>'
          + sds.map(function(p){ return '<option value="' + p.uid + '"' + (u.assignedTo === p.uid ? ' selected' : '') + '>' + aepsEsc(p.name) + '</option>'; }).join('') + '</select>'
          + (cur ? '<div style="font-size:.65rem;color:' + prc.color + ';margin-top:2px">✓ ' + aepsEsc(cur.name) + '</div>' : '') + '</div>';
      }
      html += '<button onclick="doAssign(\'' + u.uid + '\',\'' + type + '\')" style="padding:6px 12px;border-radius:8px;background:linear-gradient(135deg,var(--rtai),var(--rtai2));border:none;color:#000;font-size:.72rem;cursor:pointer;font-weight:700;white-space:nowrap">Save ✓</button></div>';
    });
  }
  html += '</div></div>';

  var assigned = targets.filter(function(u){ return u.assignedTo; }).length, unassigned = targets.length - assigned;
  function card(n, label, col){ return '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:10px;text-align:center"><div style="font-family:var(--font-head);font-size:1.2rem;font-weight:700;color:' + col + '">' + n + '</div><div style="font-size:.65rem;color:var(--muted2)">' + label + '</div></div>'; }
  html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:14px">'
    + card(targets.length, 'Total ' + targetLabel + 's', rc.color) + card(assigned, 'Assigned', 'var(--green)') + card(unassigned, 'Unassigned', 'var(--gold)')
    + (isRet ? card(dists.length, 'Distributors', prc.color) + card(sds.length, 'Super Distributors', src.color) : card(sds.length, 'Super Distributors', prc.color))
    + '</div>' + html;
  document.getElementById('assign-content').innerHTML = html;
}
'''
shutil.copy(FILE, FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
c = c[:pos] + '<script id="assign-sd-web">' + JS + '</script>\n</body>' + c[pos + len("</body>"):]
open(FILE, "w", encoding="utf-8").write(c)
print("OK: Super Distributor column added to Assign Retailers.")
