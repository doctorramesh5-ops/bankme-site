#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Website Assign Network (admin):
 - Assign Retailers gets an ADMIN column next to Distributor and Super Distributor
   ("Direct to Admin" = the retailer sits directly under the admin and the admin receives the upline commission)
 - customers who upgraded themselves to retailer are marked "UPGRADED" and listed in a box on top
   (name, mobile, date, retailer ID, Eko code, current parent). They arrive already assigned to the admin.
Run AFTER assign_sd_web.py, assign_users_web.py and upgrade_admin_backend.py (backend deployed).
Usage:  cd ~/Desktop/bankme-site && python3 upgrade_admin_web.py
"""
import sys, shutil, datetime
FILE = "app.html"
c = open(FILE, "r", encoding="utf-8").read()
if 'id="upgrade-admin-web"' in c:
    sys.exit("Already applied. Nothing written.")
for need in ('id="assign-sd-web"', 'id="assign-users-web"'):
    if c.count(need) != 1:
        sys.exit("ERROR: %s not found - apply assign_sd_web.py and assign_users_web.py first. Nothing written." % need)
pos = c.rfind("</body>")
if pos < 0 or c[pos + len("</body>"):].strip() != "</html>":
    sys.exit("ERROR: unexpected end of file. Nothing written.")

JS = r'''
var _upgInfo = {};
var _origMergeAssign = mergeBackendAssignUsers;
mergeBackendAssignUsers = async function(){
  await _origMergeAssign();
  _upgInfo = {};
  if (!CU || CU.role !== 'admin') return;
  try {
    var r = await authFetch(AEPS_API + '/admin/network/users'); var j = await r.json();
    if (!j || !j.success || !Array.isArray(j.users)) return;
    var all = window._assignUsers || [], norm = function(p){ return String(p || '').replace(/\D/g, '').slice(-10); };
    j.users.forEach(function(b){
      if (!b.upgradedFromCustomer) return;
      var p = norm(b.phone); _upgInfo[p] = { at: b.upgradedAt, internalId: b.internalId, eko: b.ekoUserCode };
      all.forEach(function(u){ if (norm(u.phone || u.mobile) === p) u.upgraded = true; });
    });
  } catch (e) {}
};

function assignPick(uid){
  var all = window._assignUsers || [];
  var d = document.getElementById('assign-d-' + uid), s = document.getElementById('assign-s-' + uid), a = document.getElementById('assign-a-' + uid), h = document.getElementById('assign-sel-' + uid);
  if (!d || !s || !h) return;
  if (d.value) {
    var dist = all.filter(function(p){ return p.uid === d.value; })[0];
    s.value = (dist && dist.assignedTo) ? dist.assignedTo : ''; s.disabled = true;
    if (a) { a.value = ''; a.disabled = true; }
    h.value = d.value;
  } else {
    var wasS = s.disabled; s.disabled = false; if (wasS) s.value = '';
    if (s.value) { if (a) { a.value = ''; a.disabled = true; } h.value = s.value; }
    else { if (a) a.disabled = false; h.value = a ? a.value : ''; }
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
  var adm = all.filter(function(u){ return u.role === 'admin'; })[0] || null;
  var targetLabel = isRet ? 'Retailer' : 'Distributor';
  var rc = getRC(type), prc = getRC(isRet ? 'distributor' : 'superdist'), src = getRC('superdist');
  var cols = isRet ? '1fr 1fr 1fr 1fr 1fr auto' : '1fr 1fr 1fr auto';
  function selStyle(on, col){ return 'width:100%;background:var(--bg3);border:1px solid ' + (on ? col : 'var(--border)') + ';border-radius:7px;padding:5px 8px;color:var(--text);font-size:.74rem;appearance:none'; }
  function dstr(x){ try { return x ? new Date(x).toLocaleDateString('en-IN') : '-'; } catch (e) { return '-'; } }
  function parentName(u){ var p = u.assignedTo ? all.filter(function(q){ return q.uid === u.assignedTo; })[0] : null; return p ? (p.role === 'admin' ? 'Admin (direct)' : p.name + ' (' + (getRC(p.role).label || p.role) + ')') : 'Unassigned'; }

  var html = '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:14px;overflow:auto">'
    + '<div style="min-width:' + (isRet ? '900px' : '560px') + '"><div style="background:var(--bg3);padding:10px 14px;display:grid;grid-template-columns:' + cols + ';gap:8px;font-size:.7rem;color:var(--muted2);font-weight:600;text-transform:uppercase">'
    + '<span>' + targetLabel + ' Name</span><span>Contact</span>' + (isRet ? '<span>Distributor</span><span>Super Distributor</span><span>Admin</span>' : '<span>Super Distributor</span>') + '<span>Action</span></div>';

  if (!targets.length) {
    html += '<div style="text-align:center;padding:24px;color:var(--muted2)">No ' + targetLabel + 's registered yet</div>';
  } else {
    targets.forEach(function(u){
      var cur = u.assignedTo ? all.filter(function(p){ return p.uid === u.assignedTo; })[0] : null;
      var up = isRet && u.upgraded;
      html += '<div style="padding:12px 14px;border-top:1px solid var(--border);display:grid;grid-template-columns:' + cols + ';gap:8px;align-items:center">'
        + '<div style="display:flex;align-items:center;gap:8px;min-width:0"><div style="width:28px;height:28px;border-radius:50%;background:' + rc.color + '22;color:' + rc.color + ';display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.75rem;flex-shrink:0">' + aepsEsc((u.name || 'U')[0].toUpperCase()) + '</div>'
        + '<div style="min-width:0"><div style="font-size:.82rem;font-weight:600;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + aepsEsc(u.name) + '</div>'
        + (up ? '<span style="font-size:.6rem;font-weight:700;padding:1px 6px;border-radius:100px;background:rgba(245,158,11,.15);color:var(--gold);border:1px solid rgba(245,158,11,.4)">⬆ UPGRADED</span>' : '')
        + (u.shopName ? '<div style="font-size:.68rem;color:var(--muted2)">🏪 ' + aepsEsc(u.shopName) + '</div>' : '') + '</div></div>'
        + '<div style="font-size:.75rem;color:var(--muted2)">' + aepsEsc(u.phone || '') + (u.email ? '<br/>' + aepsEsc(String(u.email).split('@')[0]) + '...' : '') + '</div>';
      if (isRet) {
        var distSel = cur && cur.role === 'distributor' ? cur.uid : '';
        var sdSel = cur && cur.role === 'superdist' ? cur.uid : (cur && cur.role === 'distributor' && cur.assignedTo ? cur.assignedTo : '');
        var admSel = cur && cur.role === 'admin' ? cur.uid : '';
        html += '<div><select id="assign-d-' + u.uid + '" onchange="assignPick(\'' + u.uid + '\')" style="' + selStyle(distSel, prc.color) + '"><option value="">-- No distributor --</option>'
          + dists.map(function(p){ return '<option value="' + p.uid + '"' + (distSel === p.uid ? ' selected' : '') + '>' + aepsEsc(p.name) + '</option>'; }).join('') + '</select></div>'
          + '<div><select id="assign-s-' + u.uid + '" onchange="assignPick(\'' + u.uid + '\')" ' + (distSel ? 'disabled' : '') + ' style="' + selStyle(sdSel, src.color) + '"><option value="">-- Unassigned --</option>'
          + sds.map(function(p){ return '<option value="' + p.uid + '"' + (sdSel === p.uid ? ' selected' : '') + '>' + aepsEsc(p.name) + '</option>'; }).join('') + '</select>'
          + (distSel ? '<div style="font-size:.62rem;color:var(--muted2);margin-top:2px">via distributor</div>' : (sdSel ? '<div style="font-size:.62rem;color:' + src.color + ';margin-top:2px">direct to super distributor</div>' : '')) + '</div>'
          + '<div>' + (adm
              ? '<select id="assign-a-' + u.uid + '" onchange="assignPick(\'' + u.uid + '\')" ' + ((distSel || sdSel) ? 'disabled' : '') + ' style="' + selStyle(admSel, 'var(--gold)') + '"><option value="">-- None --</option><option value="' + adm.uid + '"' + (admSel ? ' selected' : '') + '>Direct to Admin</option></select>'
                + (admSel ? '<div style="font-size:.62rem;color:var(--gold);margin-top:2px">commission to admin</div>' : '')
              : '<div style="font-size:.65rem;color:var(--muted2)">Admin account not found</div>') + '</div>'
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
  var direct = isRet ? targets.filter(function(u){ var p = u.assignedTo ? all.filter(function(q){ return q.uid === u.assignedTo; })[0] : null; return p && p.role === 'admin'; }).length : 0;
  var upgraded = isRet ? targets.filter(function(u){ return u.upgraded; }) : [];
  function card(n, label, col){ return '<div style="background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:10px;text-align:center"><div style="font-family:var(--font-head);font-size:1.2rem;font-weight:700;color:' + col + '">' + n + '</div><div style="font-size:.65rem;color:var(--muted2)">' + label + '</div></div>'; }

  var upBox = '';
  if (isRet) {
    upBox = '<div style="background:rgba(245,158,11,.06);border:1px solid rgba(245,158,11,.3);border-radius:14px;padding:12px 14px;margin-bottom:14px">'
      + '<div style="font-family:var(--font-head);font-size:.88rem;font-weight:700;color:var(--gold);margin-bottom:' + (upgraded.length ? '8px' : '2px') + '">⬆ Upgraded customers (' + upgraded.length + ')</div>'
      + (upgraded.length
          ? upgraded.map(function(u){
              var i = _upgInfo[String(u.phone || '').replace(/\D/g, '').slice(-10)] || {};
              return '<div style="display:grid;grid-template-columns:1.2fr 1fr 1fr 1.2fr 1.2fr;gap:8px;font-size:.74rem;padding:6px 0;border-top:1px solid var(--border);color:var(--text)">'
                + '<span style="font-weight:600">' + aepsEsc(u.name) + '</span><span>' + aepsEsc(u.phone || '') + '</span><span>' + dstr(i.at) + '</span>'
                + '<span style="color:var(--muted2)">' + aepsEsc(i.internalId || '') + (i.eko ? ' · Eko ' + aepsEsc(i.eko) : '') + '</span>'
                + '<span style="color:var(--gold)">' + aepsEsc(parentName(u)) + '</span></div>';
            }).join('')
          : '<div style="font-size:.74rem;color:var(--muted2)">No customer has upgraded to retailer yet. Upgraded customers appear here and are assigned directly to the admin.</div>')
      + '</div>';
  }
  html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:14px">'
    + card(targets.length, 'Total ' + targetLabel + 's', rc.color) + card(assigned, 'Assigned', 'var(--green)') + card(unassigned, 'Unassigned', 'var(--gold)')
    + (isRet ? card(direct, 'Direct to Admin', 'var(--gold)') + card(upgraded.length, 'Upgraded', 'var(--gold)') + card(dists.length, 'Distributors', prc.color) + card(sds.length, 'Super Distributors', src.color) : card(sds.length, 'Super Distributors', prc.color))
    + '</div>' + upBox + html;
  document.getElementById('assign-content').innerHTML = html;
}
'''
shutil.copy(FILE, FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
c = c[:pos] + '<script id="upgrade-admin-web">' + JS + '</script>\n</body>' + c[pos + len("</body>"):]
open(FILE, "w", encoding="utf-8").write(c)
print("OK: Admin column + upgraded customers box added to Assign Network.")
