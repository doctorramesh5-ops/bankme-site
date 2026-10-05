#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rewires BBPS on the BankMe website (app.html) from the static/simulated
version to real Eko calls through bankme-backend, matching what was just
done on the mobile app.

Safe by design: every block below must match the CURRENT file text
EXACTLY ONCE before anything is written. If any block doesn't match
(because the file has changed since this script was written), the whole
run aborts with a clear message and your file is left untouched.

Usage:
    cd ~/Desktop/bankme-site
    python3 fix_bbps_web.py
"""
import sys, re, shutil, datetime

FILE = "app.html"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

replacements = []  # list of (name, old, new)

# ─────────────────────────────────────────────────────────────────
# 1) Replace static BBPS_CATEGORIES + BBPS_BILLERS with live loaders
# ─────────────────────────────────────────────────────────────────
old1 = """// ══════════════════════════════════════════════════════════════════
// BBPS — Bharat Bill Payment System (NPCI Official Services)
// Complete service list as offered by GPay / PhonePe / BBPS 2024
// ══════════════════════════════════════════════════════════════════
var BBPS_CATEGORIES = [
  {id:'electricity',   label:'Electricity',        icon:'⚡',  color:'#f59e0b', hint:'CA Number / Service No. / Account No.'},
  {id:'water',         label:'Water',              icon:'💧',  color:'#06b6d4', hint:'Consumer No. / Account No.'},
  {id:'gas',           label:'Gas (Piped/PNG)',     icon:'🔥',  color:'#ef4444', hint:'Consumer No. / BP No.'},
  {id:'broadband',     label:'Broadband/Internet',  icon:'🌐',  color:'#8b5cf6', hint:'Account No. / Username'},
  {id:'dth',           label:'DTH / Cable TV',      icon:'📺',  color:'#3b82f6', hint:'Subscriber ID / Customer ID'},
  {id:'mobile_postpaid',label:'Mobile Postpaid',   icon:'📱',  color:'#10b981', hint:'10-digit Mobile Number'},
  {id:'mobile_prepaid', label:'Mobile Prepaid',    icon:'📲',  color:'#22c55e', hint:'10-digit Mobile Number'},
  {id:'landline',      label:'Landline',           icon:'☎️',  color:'#6366f1', hint:'STD Code + Phone Number'},
  {id:'fastag',        label:'FASTag',             icon:'🚗',  color:'#f97316', hint:'Vehicle No. / Tag ID'},
  {id:'insurance',     label:'Insurance',          icon:'🛡️',  color:'#0ea5e9', hint:'Policy No. / Customer ID'},
  {id:'loan_emi',      label:'Loan Repayment/EMI', icon:'🏦',  color:'#a855f7', hint:'Loan Account No.'},
  {id:'credit_card',   label:'Credit Card Bill',   icon:'💳',  color:'#ec4899', hint:'Credit Card Number'},
  {id:'housing',       label:'Housing Society',    icon:'🏘️',  color:'#84cc16', hint:'Flat No. / Member ID'},
  {id:'education',     label:'Education Fees',     icon:'🎓',  color:'#14b8a6', hint:'Student / Application ID'},
  {id:'hospital',      label:'Hospital / Health',  icon:'🏥',  color:'#f43f5e', hint:'Patient ID / Reg. No.'},
  {id:'municipal',     label:'Municipal Tax/Services',icon:'🏛️',color:'#78716c', hint:'Property ID / Account No.'},
  {id:'lpg',           label:'LPG Cylinder',       icon:'🫙',  color:'#fb923c', hint:'LPG Consumer No. / BP No.'},
  {id:'subscription',  label:'OTT / Subscription', icon:'🎬',  color:'#c084fc', hint:'Registered Mobile / Email'},
  {id:'transport',     label:'Metro / Bus Pass',   icon:'🚇',  color:'#2dd4bf', hint:'Card No. / Customer ID'},
  {id:'clubs',         label:'Club / Association', icon:'🎯',  color:'#facc15', hint:'Member ID'},
  {id:'recurring_deposit',label:'Recurring Deposit',icon:'💰', color:'#34d399', hint:'RD Account No.'},
  {id:'govt',          label:'Govt / Tax Payment', icon:'🏢',  color:'#94a3b8', hint:'Challan No. / Reference ID'},
];

var BBPS_BILLERS = {
  electricity:[
    'BESCOM (Bengaluru)','MSEDCL (Maharashtra)','TSSPDCL (Telangana South)',
    'TSNPDCL (Telangana North)','APSPDCL (AP South)','APEPDCL (AP East)',
    'TNEB / TANGEDCO (Tamil Nadu)','BSES Rajdhani (Delhi)','BSES Yamuna (Delhi)',
    'Tata Power Delhi','DHBVN (Haryana)','UHBVN (Haryana)',
    'PSPCL (Punjab)','JVVNL (Rajasthan)','AVVNL (Rajasthan)',
    'UPPCL (UP)','PUVVNL (UP East)','DVVNL (UP)','KESCO (Kanpur)',
    'CESC (Kolkata)','WBSEDCL (West Bengal)','SBPDCL (Bihar)',
    'NBPDCL (Bihar)','GRIDCO (Odisha)','TPNODL (Odisha)',
    'CSPDCL (Chhattisgarh)','MPEZ (MP East)','MPCZ (MP Central)',
    'MPWZ (MP West)','KPTCL / GESCOM (Karnataka)','HESCO (J&K)',
    'JKPDD (J&K)','APDCL (Assam)','MePDCL (Meghalaya)',
    'Torrent Power (Ahmedabad)','Torrent Power (Surat)','DGVCL (Gujarat)',
    'MGVCL (Gujarat)','PGVCL (Gujarat)','UGVCL (Gujarat)',
    'Kerala KSEB','PSPCL Ludhiana','NPCL (Noida)',
  ],
  water:[
    'Delhi Jal Board (DJB)','MCGM (Mumbai)','BWSSB (Bengaluru)',
    'HMWS&SB (Hyderabad)','Chennai Metro Water','CMWSSB (Tamil Nadu)',
    'Kolkata Municipal Water','PHED Rajasthan','PHED Jharkhand',
    'PHED Bihar','Punjab Water Supply','Haryana PHED','UP Jal Nigam',
    'BSCNL Water','Nagpur Municipal Water','Pune Municipal Corp Water',
    'Surat Municipal Water','Ahmedabad AMC Water','Jaipur Municipal Water',
    'Indore Nagar Nigam Water','Bhopal Nagar Nigam Water',
  ],
  gas:[
    'Mahanagar Gas (Mumbai)','Indraprastha Gas (Delhi)','Adani Gas',
    'Gujarat Gas','IGL CNG (Delhi)','MGL CNG (Mumbai)',
    'Sabarmati Gas','Torrent Gas','Bhagyanagar Gas (Hyderabad)',
    'Central UP Gas','Avantika Gas (MP)','Green Gas (Lucknow)',
    'GAIL Gas','Unique Central Piped Gas','HPNL Gas (Haryana)',
    'Siti Energy Gas','AG&P Pratham Gas','Think Gas',
  ],
  broadband:[
    'Jio Fiber','Airtel Xstream Fiber','BSNL Broadband','ACT Fibernet',
    'Hathway','DEN Networks','Spectra','Excitel','Tikona',
    'You Broadband','MTNL Broadband','Asianet Broadband',
    'GTPL Broadband','BSNL FTTH','Gigatel','Nextra Broadband',
    'Railwire','Netplus Broadband','Imtiaz Broadband','Sify Technologies',
  ],
  dth:[
    'Tata Play (Tata Sky)','Airtel Digital TV','Dish TV','Sun Direct',
    'Videocon D2H','DD Free Dish','In-Cable (Hathway)','GTPL Cable',
    'Den Cable','Siti Cable','FastWay Cable','Nxtdigital',
    'NXT Digital','7Star DTH','Ortel Cable',
  ],
  mobile_postpaid:[
    'Jio Postpaid','Airtel Postpaid','Vi (Vodafone Idea) Postpaid',
    'BSNL Postpaid','MTNL Postpaid (Delhi)','MTNL Postpaid (Mumbai)',
  ],
  mobile_prepaid:[
    'Jio Prepaid Recharge','Airtel Prepaid Recharge',
    'Vi (Vodafone Idea) Prepaid','BSNL Prepaid','MTNL Prepaid',
  ],
  landline:[
    'BSNL Landline','MTNL Delhi Landline','MTNL Mumbai Landline',
    'Airtel Landline','Jio Landline','TATA Teleservices Landline',
  ],
  fastag:[
    'Paytm Payments Bank FASTag','SBI FASTag','HDFC Bank FASTag',
    'ICICI Bank FASTag','Axis Bank FASTag','IDFC First Bank FASTag',
    'Kotak Bank FASTag','Bank of Baroda FASTag','Punjab National Bank FASTag',
    'Canara Bank FASTag','IndusInd Bank FASTag','Federal Bank FASTag',
    'Airtel Payments Bank FASTag','Equitas Bank FASTag','FINO FASTag',
    'Karnataka Bank FASTag','Saraswat Bank FASTag','NHAI FASTag (Official)',
  ],
  insurance:[
    'LIC of India','SBI Life Insurance','HDFC Life Insurance',
    'ICICI Prudential Life','Bajaj Allianz Life','Max Life Insurance',
    'Tata AIA Life','Aditya Birla Sun Life','Kotak Life Insurance',
    'Reliance Nippon Life','PNB MetLife','IndiaFirst Life',
    'New India Assurance','National Insurance','Oriental Insurance',
    'United India Insurance','Star Health Insurance','Niva Bupa Health',
    'Bajaj Allianz Health','Care Health Insurance','HDFC ERGO Health',
  ],
  loan_emi:[
    'SBI Home Loan','HDFC Home Loan','ICICI Home Loan','LIC Housing Finance',
    'Bajaj Finserv EMI','Tata Capital Loan','Muthoot Finance',
    'Manappuram Finance','IIFL Finance','Shriram Finance',
    'HDFC Personal Loan','Axis Bank Personal Loan','Kotak Personal Loan',
    'IndusInd Bank Loan','YES Bank Loan','PNB Housing Finance',
    'Canara Bank Loan','Bank of Baroda Loan','Union Bank Loan',
    'Federal Bank Loan','RBL Bank Loan','Hero FinCorp',
  ],
  credit_card:[
    'SBI Card','HDFC Credit Card','ICICI Credit Card','Axis Bank Credit Card',
    'Kotak Credit Card','IndusInd Bank Credit Card','YES Bank Credit Card',
    'RBL Bank Credit Card','Federal Bank Credit Card','AU Small Finance Bank Card',
    'American Express India','Citibank India','Standard Chartered India',
    'IDFC First Bank Credit Card','Bank of Baroda Credit Card',
    'Canara Bank Credit Card','Union Bank Credit Card',
  ],
  housing:[
    'DDA Housing (Delhi)','MHADA (Mumbai)','KHB (Karnataka)','APHB (Andhra Pradesh)',
    'TUDA (Telangana)','TNHB (Tamil Nadu)','GMDA (Guwahati)',
    'Noida Authority','Greater Noida Authority','YEIDA (Yamuna)','HRERA (Haryana)',
    'Mumbai Housing Society','Pune Housing Society','Bengaluru Apartment',
  ],
  education:[
    'CBSE Fee','ICSE Fee','Delhi University','Mumbai University',
    'Anna University','Osmania University','Bangalore University',
    'NIT Fee Portal','IIT Fee Portal','NEET / JEE Fee',
    'Narayana Schools','Aakash Institute','FIITJEE',
    'Byju Classes Fee','Vedantu Fee','Allen Career Institute',
    'Amity University','Manipal University','VIT University',
  ],
  hospital:[
    'Apollo Hospitals','Fortis Healthcare','Max Healthcare','Manipal Hospitals',
    'Narayana Health','Medanta','Aster Hospitals','AIIMS Fee Portal',
    'NIMHANS','PGI Chandigarh','CMC Vellore','Kokilaben Hospital',
    'Ruby Hall Clinic','Lilavati Hospital','Sir Ganga Ram Hospital',
  ],
  municipal:[
    'MCD Property Tax (Delhi)','MCGM Property Tax (Mumbai)','BBMP Property Tax (Bengaluru)',
    'GHMC Property Tax (Hyderabad)','Chennai Corporation Tax',
    'Kolkata Municipal Corp','Pune Municipal Corp','Ahmedabad Municipal',
    'Surat Municipal','Jaipur Nagar Nigam','Indore Nagar Nigam',
    'Nagpur Municipal','Lucknow Nagar Nigam','Kanpur Nagar Nigam',
    'Patna Municipal Corp','Bhopal Nagar Nigam','Raipur Nagar Nigam',
  ],
  lpg:[
    'HP Gas (Indane)','Bharat Gas (BPCL)','Indane Gas (IOCL)',
    'HP Gas Subsidy Link','Bharat Gas Subsidy Link','Indane Subsidy Link',
  ],
  subscription:[
    'Netflix India','Amazon Prime Video','Disney+ Hotstar','Sony LIV',
    'Zee5','Voot Select','JioCinema Premium','MX Player Gold',
    'Apple TV+ India','YouTube Premium','Spotify Premium India',
    'Gaana Plus','Wynk Music','Audible India',
  ],
  transport:[
    'Delhi Metro Card (DMRC)','Mumbai Metro Card','Bengaluru Metro (BMRCL)',
    'Hyderabad Metro (HMRL)','Chennai Metro','Kolkata Metro',
    'BEST Bus Pass (Mumbai)','DTC Bus Pass (Delhi)','TSRTC Bus Pass',
    'MSRTC Bus Pass','BMTC Bus Pass (Bengaluru)',
    'IRCTC Wallet','FASTag Recharge','NHAI Toll',
  ],
  clubs:[
    'Gymkhana Club Delhi','Taj Sports Club','FICCI Ladies Organization',
    'CII Membership','NASSCOM Membership','Rotary Club India',
    'Lions Club India','YMCA India',
  ],
  recurring_deposit:[
    'SBI RD / Savings','HDFC Bank RD','ICICI Bank RD','Axis Bank RD',
    'PNB RD','Post Office RD','Canara Bank RD','Bank of Baroda RD',
    'Kotak RD','IndusInd RD',
  ],
  govt:[
    'Income Tax (TIN-NSDL)','GST Payment (GSTN)','TDS Payment',
    'MCA21 Fee','DGFT Fee','Patent Fee (IP India)',
    'Passport Fee (MEA)','Aadhaar Update Fee (UIDAI)',
    'PAN Card Fee (NSDL / UTI)','Driving Licence Fee',
    'Vehicle Registration Fee','EPFO / PF Payment',
    'ESI Contribution','NPS Contribution','PPF Deposit',
    'Sukanya Samriddhi Yojana','Kisan Vikas Patra',
    'State Govt Challan','Court Fee','Police Challan / E-Challan',
    'Traffic Fine (Parivahan)','Jal Jeevan Mission',
  ],
};"""

new1 = """// ══════════════════════════════════════════════════════════════════
// BBPS — LIVE from Eko via bankme-backend (categories/operators no
// longer hardcoded — the old static list had no operator codes, so
// Eko's fetch-bill/pay-bill could never actually work against it)
// ══════════════════════════════════════════════════════════════════
var BANKME_API = 'https://bankme-backend.onrender.com';
var BBPS_CATEGORIES = [];
var BBPS_OPERATORS = [];

var BBPS_CAT_STYLE = [
  {match:/electric/i,  icon:'⚡', color:'#f59e0b', hint:'CA Number / Service No. / Account No.'},
  {match:/water/i,      icon:'💧', color:'#06b6d4', hint:'Consumer No. / Account No.'},
  {match:/gas/i,        icon:'🔥', color:'#ef4444', hint:'Consumer No. / BP No.'},
  {match:/broadband|internet/i, icon:'🌐', color:'#8b5cf6', hint:'Account No. / Username'},
  {match:/dth|cable/i,  icon:'📺', color:'#3b82f6', hint:'Subscriber ID / Customer ID'},
  {match:/landline/i,   icon:'☎️', color:'#6366f1', hint:'STD Code + Phone Number'},
  {match:/postpaid/i,   icon:'📱', color:'#10b981', hint:'10-digit Mobile Number'},
  {match:/prepaid/i,    icon:'📲', color:'#22c55e', hint:'10-digit Mobile Number'},
  {match:/fastag/i,     icon:'🚗', color:'#f97316', hint:'Vehicle No. / Tag ID'},
  {match:/insurance/i,  icon:'🛡️', color:'#0ea5e9', hint:'Policy No. / Customer ID'},
  {match:/loan/i,       icon:'🏦', color:'#a855f7', hint:'Loan Account No.'},
  {match:/credit card/i,icon:'💳', color:'#ec4899', hint:'Credit Card Number'},
  {match:/housing|society/i, icon:'🏘️', color:'#84cc16', hint:'Flat No. / Member ID'},
  {match:/education/i,  icon:'🎓', color:'#14b8a6', hint:'Student / Application ID'},
  {match:/hospital|health/i, icon:'🏥', color:'#f43f5e', hint:'Patient ID / Reg. No.'},
  {match:/municipal/i,  icon:'🏛️', color:'#78716c', hint:'Property ID / Account No.'},
  {match:/lpg|cylinder/i, icon:'🫙', color:'#fb923c', hint:'LPG Consumer No. / BP No.'},
  {match:/subscription|ott/i, icon:'🎬', color:'#c084fc', hint:'Registered Mobile / Email'},
  {match:/metro|bus|transport/i, icon:'🚇', color:'#2dd4bf', hint:'Card No. / Customer ID'},
  {match:/club|association/i, icon:'🎯', color:'#facc15', hint:'Member ID'},
  {match:/recurring deposit/i, icon:'💰', color:'#34d399', hint:'RD Account No.'},
  {match:/tax|govt|government/i, icon:'🏢', color:'#94a3b8', hint:'Challan No. / Reference ID'},
];
var BBPS_DEFAULT_STYLE={icon:'🧾',color:'#10b981',hint:'Consumer Number / Account Number'};
function bbpsStyleFor(name){
  for(var i=0;i<BBPS_CAT_STYLE.length;i++){ if(BBPS_CAT_STYLE[i].match.test(name||'')) return BBPS_CAT_STYLE[i]; }
  return BBPS_DEFAULT_STYLE;
}

async function loadBBPSCategories(){
  try{
    var r=await fetch(BANKME_API+'/eko/bbps/categories');
    var j=await r.json();
    var list=(j&&j.data&&j.data.param_attributes&&j.data.param_attributes.list_elements)||[];
    BBPS_CATEGORIES=list.map(function(c){
      var name=c.operator_category_name||c.name||String(c.operator_category_id||c.id||'');
      var st=bbpsStyleFor(name);
      return {id:(c.operator_category_id!=null?c.operator_category_id:c.id), label:name, icon:st.icon, color:st.color, hint:st.hint};
    });
  }catch(e){ console.log('BBPS categories load failed:',e.message); BBPS_CATEGORIES=[]; }
}

async function loadBBPSOperators(categoryId){
  try{
    var r=await fetch(BANKME_API+'/eko/bbps/operators?category='+categoryId);
    var j=await r.json();
    var list=(j&&j.data&&j.data.param_attributes&&j.data.param_attributes.list_elements)||[];
    BBPS_OPERATORS=list.map(function(o){
      return {id:String(o.operator_id!=null?o.operator_id:(o.id||'')), name:(o.name||o.operator_name||String(o.operator_id||o.id||''))};
    });
  }catch(e){ console.log('BBPS operators load failed:',e.message); BBPS_OPERATORS=[]; }
}"""

replacements.append(("BBPS_CATEGORIES + BBPS_BILLERS block", old1, new1))

# ─────────────────────────────────────────────────────────────────
# 2) initBBPSForm — load live categories, add customer-mobile field
# ─────────────────────────────────────────────────────────────────
old2a = """function initBBPSForm(){
  window._bbpsCategory='';
  window._bbpsBiller='';
  window._bbpsBillerHint='Consumer Number';
  var root=document.getElementById('bbps-form-root');
  if(!root) return;

  // Use DOM methods to avoid all quote-escaping issues
  root.innerHTML='';

  // ── Category section ──
  var catSection=document.createElement('div');
  catSection.style.marginBottom='14px';

  var catTitle=document.createElement('div');
  catTitle.style.cssText='font-size:.72rem;font-weight:700;color:var(--muted2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px';
  catTitle.textContent='Select Bill Category';
  catSection.appendChild(catTitle);

  var catGrid=document.createElement('div');
  catGrid.style.cssText='display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:7px';
  catGrid.id='bbps-cat-grid';

  BBPS_CATEGORIES.forEach(function(c){"""

new2a = """async function initBBPSForm(){
  window._bbpsCategory='';
  window._bbpsBiller=null;
  window._bbpsBillerHint='Consumer Number';
  var root=document.getElementById('bbps-form-root');
  if(!root) return;

  root.innerHTML='<div style="text-align:center;padding:30px"><div style="width:30px;height:30px;border:3px solid rgba(0,212,170,.2);border-top-color:var(--rtai);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 10px"></div><div style="font-size:.8rem;color:var(--muted2)">Loading bill categories…</div></div>';
  await loadBBPSCategories();
  if(!BBPS_CATEGORIES.length){
    root.innerHTML='<div style="text-align:center;padding:24px;color:var(--muted2);font-size:.82rem">Could not load bill categories.<br><button onclick="initBBPSForm()" style="margin-top:8px;padding:6px 14px;border-radius:7px;border:1px solid var(--border2);background:var(--bg3);color:var(--text);cursor:pointer;font-size:.74rem">Retry</button></div>';
    return;
  }

  // Use DOM methods to avoid all quote-escaping issues
  root.innerHTML='';

  // ── Category section ──
  var catSection=document.createElement('div');
  catSection.style.marginBottom='14px';

  var catTitle=document.createElement('div');
  catTitle.style.cssText='font-size:.72rem;font-weight:700;color:var(--muted2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px';
  catTitle.textContent='Select Bill Category';
  catSection.appendChild(catTitle);

  var catGrid=document.createElement('div');
  catGrid.style.cssText='display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:7px';
  catGrid.id='bbps-cat-grid';

  BBPS_CATEGORIES.forEach(function(c){"""

replacements.append(("initBBPSForm header (live-load categories)", old2a, new2a))

old2b = """  consRow.appendChild(fetchBtn);
  consSection.appendChild(consRow);

  var consHint=document.createElement('div');"""

new2b = """  consRow.appendChild(fetchBtn);
  consSection.appendChild(consRow);

  // Customer mobile number — Eko requires this (confirmation_mobile_no)
  var mobileLabel=document.createElement('label');
  mobileLabel.className='flabel';
  mobileLabel.textContent="Customer's Mobile Number";
  consSection.appendChild(mobileLabel);
  var mobileInput=document.createElement('input');
  mobileInput.id='bbps-mobile';
  mobileInput.className='finp';
  mobileInput.type='tel';
  mobileInput.maxLength=10;
  mobileInput.placeholder='10-digit mobile for SMS confirmation';
  consSection.appendChild(mobileInput);

  var consHint=document.createElement('div');"""

replacements.append(("initBBPSForm consumer section (add mobile field)", old2b, new2b))

# ─────────────────────────────────────────────────────────────────
# 3) selectBBPSCategory — load live operators instead of static map
# ─────────────────────────────────────────────────────────────────
old3 = """function selectBBPSCategory(catId){
  window._bbpsCategory=catId;
  window._bbpsBiller='';
  // Update category highlight using stored color per tile
  BBPS_CATEGORIES.forEach(function(c){
    var tile=document.getElementById('bbps-cat-'+c.id);
    if(!tile) return;
    var nameDiv=tile.querySelector('[data-role="catname"]');
    if(c.id===catId){
      tile.style.borderColor=c.color||'var(--rtai)';
      tile.style.background='rgba(0,212,170,.1)';
      tile.style.transform='translateY(-1px)';
      if(nameDiv) nameDiv.style.color=c.color||'var(--rtai)';
    } else {
      tile.style.borderColor='var(--border)';
      tile.style.background='var(--bg3)';
      tile.style.transform='';
      if(nameDiv) nameDiv.style.color='var(--muted2)';
    }
  });
  // Show biller section
  var billerSection=document.getElementById('bbps-biller-section');
  if(billerSection) billerSection.style.display='block';
  // Update biller label
  var catObj=BBPS_CATEGORIES.find(function(c){return c.id===catId;})||{label:catId};
  var lbl=document.getElementById('bbps-biller-label');
  if(lbl) lbl.textContent='Select '+catObj.label+' Biller';
  // Update consumer hint
  window._bbpsBillerHint=catObj.hint||'Consumer Number';
  var consLbl=document.getElementById('bbps-consumer-label');
  if(consLbl) consLbl.textContent=catObj.hint||'Consumer Number';
  var consInp=document.getElementById('bbps-consumer');
  if(consInp) consInp.placeholder='Enter '+( catObj.hint||'Consumer Number');
  // Reset biller badge
  var badge=document.getElementById('bbps-biller-badge');
  if(badge) badge.style.display='none';
  // Clear biller search
  var search=document.getElementById('bbps-biller-search');
  if(search) search.value='';
  // Hide consumer section until biller is chosen
  var consSection=document.getElementById('bbps-consumer-section');
  if(consSection) consSection.style.display='none';
  // Populate dropdown
  filterBBPSBillers();
}"""

new3 = """async function selectBBPSCategory(catId){
  window._bbpsCategory=catId;
  window._bbpsBiller=null;
  // Update category highlight using stored color per tile
  BBPS_CATEGORIES.forEach(function(c){
    var tile=document.getElementById('bbps-cat-'+c.id);
    if(!tile) return;
    var nameDiv=tile.querySelector('[data-role="catname"]');
    if(c.id===catId){
      tile.style.borderColor=c.color||'var(--rtai)';
      tile.style.background='rgba(0,212,170,.1)';
      tile.style.transform='translateY(-1px)';
      if(nameDiv) nameDiv.style.color=c.color||'var(--rtai)';
    } else {
      tile.style.borderColor='var(--border)';
      tile.style.background='var(--bg3)';
      tile.style.transform='';
      if(nameDiv) nameDiv.style.color='var(--muted2)';
    }
  });
  // Show biller section
  var billerSection=document.getElementById('bbps-biller-section');
  if(billerSection) billerSection.style.display='block';
  // Update biller label
  var catObj=BBPS_CATEGORIES.find(function(c){return c.id===catId;})||{label:catId};
  var lbl=document.getElementById('bbps-biller-label');
  if(lbl) lbl.textContent='Select '+catObj.label+' Biller';
  // Update consumer hint
  window._bbpsBillerHint=catObj.hint||'Consumer Number';
  var consLbl=document.getElementById('bbps-consumer-label');
  if(consLbl) consLbl.textContent=catObj.hint||'Consumer Number';
  var consInp=document.getElementById('bbps-consumer');
  if(consInp) consInp.placeholder='Enter '+( catObj.hint||'Consumer Number');
  // Reset biller badge
  var badge=document.getElementById('bbps-biller-badge');
  if(badge) badge.style.display='none';
  // Clear biller search, load live billers for this category
  var search=document.getElementById('bbps-biller-search');
  if(search){ search.value=''; search.disabled=true; search.placeholder='Loading billers…'; }
  // Hide consumer section until biller is chosen
  var consSection=document.getElementById('bbps-consumer-section');
  if(consSection) consSection.style.display='none';
  BBPS_OPERATORS=[];
  await loadBBPSOperators(catId);
  if(search){ search.disabled=false; search.placeholder='Search biller name...'; }
  // Populate dropdown
  filterBBPSBillers();
}"""

replacements.append(("selectBBPSCategory (live operators)", old3, new3))

# ─────────────────────────────────────────────────────────────────
# 4) filterBBPSBillers — use BBPS_OPERATORS objects
# ─────────────────────────────────────────────────────────────────
old4 = """function filterBBPSBillers(){
  var cat=window._bbpsCategory;
  if(!cat) return;
  var q=(document.getElementById('bbps-biller-search')?.value||'').toLowerCase().trim();
  var list=BBPS_BILLERS[cat]||[];
  var filtered=list.filter(function(b){ return !q||b.toLowerCase().indexOf(q)>=0; });
  var dd=document.getElementById('bbps-biller-dropdown');
  if(!dd) return;
  if(!filtered.length){ dd.style.display='none'; return; }
  dd.style.display='block';
  dd.innerHTML='';
  filtered.forEach(function(b){
    var item=document.createElement('div');
    item.style.cssText='padding:10px 14px;cursor:pointer;font-size:.82rem;color:var(--text);border-bottom:1px solid var(--border)';
    if(q){
      var re=new RegExp('('+q.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&')+')','gi');
      item.innerHTML=b.replace(re,'<mark style="background:rgba(245,158,11,.3);color:var(--gold);border-radius:2px">$1</mark>');
    } else {
      item.textContent=b;
    }
    item.addEventListener('mouseenter',function(){ item.style.background='var(--bg3)'; });
    item.addEventListener('mouseleave',function(){ item.style.background=''; });
    item.addEventListener('click',function(){ selectBBPSBiller(b); });
    dd.appendChild(item);
  });
}"""

new4 = """function filterBBPSBillers(){
  var cat=window._bbpsCategory;
  if(!cat) return;
  var q=(document.getElementById('bbps-biller-search')?.value||'').toLowerCase().trim();
  var list=BBPS_OPERATORS||[];
  var filtered=list.filter(function(b){ return !q||b.name.toLowerCase().indexOf(q)>=0; });
  var dd=document.getElementById('bbps-biller-dropdown');
  if(!dd) return;
  if(!filtered.length){ dd.style.display='none'; return; }
  dd.style.display='block';
  dd.innerHTML='';
  filtered.forEach(function(b){
    var item=document.createElement('div');
    item.style.cssText='padding:10px 14px;cursor:pointer;font-size:.82rem;color:var(--text);border-bottom:1px solid var(--border)';
    if(q){
      var re=new RegExp('('+q.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&')+')','gi');
      item.innerHTML=b.name.replace(re,'<mark style="background:rgba(245,158,11,.3);color:var(--gold);border-radius:2px">$1</mark>');
    } else {
      item.textContent=b.name;
    }
    item.addEventListener('mouseenter',function(){ item.style.background='var(--bg3)'; });
    item.addEventListener('mouseleave',function(){ item.style.background=''; });
    item.addEventListener('click',function(){ selectBBPSBiller(b); });
    dd.appendChild(item);
  });
}"""

replacements.append(("filterBBPSBillers (live operators)", old4, new4))

# ─────────────────────────────────────────────────────────────────
# 5) selectBBPSBiller — takes {id,name} object instead of plain string
# ─────────────────────────────────────────────────────────────────
old5 = """function selectBBPSBiller(billerName){
  window._bbpsBiller=billerName;
  // Hide dropdown
  var dd=document.getElementById('bbps-biller-dropdown');
  if(dd) dd.style.display='none';
  // Update search input
  var search=document.getElementById('bbps-biller-search');
  if(search) search.value=billerName;
  // Show badge
  var badge=document.getElementById('bbps-biller-badge');
  var badgeText=document.getElementById('bbps-biller-badge-text');
  if(badge&&badgeText){
    badgeText.textContent='✓ '+billerName;
    badge.style.display='flex';
  }
  // Show consumer/amount section
  var consSection=document.getElementById('bbps-consumer-section');
  if(consSection) consSection.style.display='block';
  // Update consumer label/placeholder from category hint
  var catObj=BBPS_CATEGORIES.find(function(c){return c.id===window._bbpsCategory;})||{};
  var hint=catObj.hint||'Consumer Number';
  window._bbpsBillerHint=hint;
  var lbl=document.getElementById('bbps-consumer-label');
  if(lbl) lbl.textContent=hint;
  var inp=document.getElementById('bbps-consumer');
  if(inp) inp.placeholder='Enter '+hint;
  // Focus consumer input
  setTimeout(function(){ if(inp) inp.focus(); },100);
}"""

new5 = """function selectBBPSBiller(biller){
  window._bbpsBiller=biller; // {id, name}
  // Hide dropdown
  var dd=document.getElementById('bbps-biller-dropdown');
  if(dd) dd.style.display='none';
  // Update search input
  var search=document.getElementById('bbps-biller-search');
  if(search) search.value=biller.name;
  // Show badge
  var badge=document.getElementById('bbps-biller-badge');
  var badgeText=document.getElementById('bbps-biller-badge-text');
  if(badge&&badgeText){
    badgeText.textContent='✓ '+biller.name;
    badge.style.display='flex';
  }
  // Show consumer/amount section
  var consSection=document.getElementById('bbps-consumer-section');
  if(consSection) consSection.style.display='block';
  // Update consumer label/placeholder from category hint
  var catObj=BBPS_CATEGORIES.find(function(c){return c.id===window._bbpsCategory;})||{};
  var hint=catObj.hint||'Consumer Number';
  window._bbpsBillerHint=hint;
  var lbl=document.getElementById('bbps-consumer-label');
  if(lbl) lbl.textContent=hint;
  var inp=document.getElementById('bbps-consumer');
  if(inp) inp.placeholder='Enter '+hint;
  // Focus consumer input
  setTimeout(function(){ if(inp) inp.focus(); },100);
}"""

replacements.append(("selectBBPSBiller (object instead of string)", old5, new5))

# ─────────────────────────────────────────────────────────────────
# 6) clearBBPSBiller — null instead of empty string, for consistency
# ─────────────────────────────────────────────────────────────────
old6 = """function clearBBPSBiller(){
  window._bbpsBiller='';"""
new6 = """function clearBBPSBiller(){
  window._bbpsBiller=null;"""
replacements.append(("clearBBPSBiller (null instead of '')", old6, new6))

# ─────────────────────────────────────────────────────────────────
# 7) fetchBBPSBill — real call instead of simulated random bill
# ─────────────────────────────────────────────────────────────────
old7_start_marker = "// ══════════════════════════════════════════════════════════════════\n// BBPS: Auto Bill Fetch — simulates NPCI BBPS fetch API\n// ══════════════════════════════════════════════════════════════════\nasync function fetchBBPSBill(silent){"
old7_end_marker = "  if(fetchBtn){ fetchBtn.disabled=false; fetchBtn.textContent='Re-fetch'; }\n  if(!silent) toast('Bill fetched! ₹'+fmtN(billAmt)+' due','s');\n}"

start_idx = content.find(old7_start_marker)
end_idx = content.find(old7_end_marker)
if start_idx == -1 or end_idx == -1:
    print("❌ Could not locate fetchBBPSBill boundaries — aborting, no changes written.")
    sys.exit(1)
end_idx_full = end_idx + len(old7_end_marker)
old7 = content[start_idx:end_idx_full]

new7 = """// ══════════════════════════════════════════════════════════════════
// BBPS: Real bill fetch via Eko (through bankme-backend)
// ══════════════════════════════════════════════════════════════════
async function fetchBBPSBill(silent){
  var consumer=(document.getElementById('bbps-consumer')?.value||'').trim();
  var mobile=(document.getElementById('bbps-mobile')?.value||'').trim();
  var biller=window._bbpsBiller||null;
  var cat=window._bbpsCategory||'';
  if(!consumer||consumer.length<4){ if(!silent) toast('Enter a valid consumer number','e'); return; }
  if(!biller){ if(!silent) toast('Select a biller first','e'); return; }
  if(!mobile||mobile.length!==10){ if(!silent) toast("Enter the customer's 10-digit mobile number",'e'); return; }

  var bc=document.getElementById('bbps-bill-card');
  var as=document.getElementById('bbps-amt-section');
  var fetchBtn=document.getElementById('bbps-fetch-btn');
  if(!bc||!as) return;

  bc.style.display='block';
  bc.innerHTML='<div style="display:flex;align-items:center;gap:10px;padding:4px 0">'
    +'<div style="width:20px;height:20px;border:3px solid rgba(0,212,170,.2);border-top-color:var(--rtai);border-radius:50%;animation:spin .8s linear infinite;flex-shrink:0"></div>'
    +'<div style="font-size:.8rem;color:var(--muted2)">Fetching bill from NPCI BBPS gateway…</div></div>';
  if(fetchBtn){ fetchBtn.disabled=true; fetchBtn.textContent='Fetching…'; }
  if(as) as.style.display='none';

  var catObj=BBPS_CATEGORIES.find(function(c){return c.id===cat;})||{label:cat,icon:'🧾'};
  var senderName=(CU&&(CU.shopName||CU.name))||'Retailer';

  try{
    var qs=new URLSearchParams({
      phone_operator_code: biller.id,
      utility_acc_no: consumer,
      confirmation_mobile_no: mobile,
      sender_name: senderName,
      category: cat
    }).toString();
    var r=await fetch(BANKME_API+'/eko/bbps/fetch-bill?'+qs);
    var j=await r.json();
    if(j&&j.success===false){ throw new Error(j.message||'Could not fetch bill'); }
    var d=(j&&j.data)||j||{};
    var billAmt=Number(d.amount||d.bill_amount||0);
    var consumerName=d.customerName||d.customer_name||senderName;
    var dueDateStr=d.dueDate||d.due_date||'';
    var billNumber=d.billNumber||d.bill_number||d.bill_id||('BILL'+consumer.slice(-6));

    window._bbpsFetchedAmt=billAmt;

    var rows=[
      ['👤 Consumer',consumerName],
      ['🏢 Biller',biller.name],
      ['🧾 Bill No.',billNumber],
    ].concat(dueDateStr?[['📆 Due Date',dueDateStr]]:[]).concat([
      ['💰 Bill Amount','<span style="font-family:var(--font-head);font-size:1rem;font-weight:700;color:var(--green)">₹'+fmtN(billAmt)+'</span>'],
    ]);

    bc.innerHTML='<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">'
      +'<div style="font-size:1.2rem">'+catObj.icon+'</div>'
      +'<div style="font-size:.82rem;font-weight:700;color:var(--green)">Bill Fetched Successfully</div>'
      +'<div style="margin-left:auto;font-size:.65rem;background:rgba(16,185,129,.15);color:var(--green);padding:2px 7px;border-radius:100px;font-weight:700">NPCI BBPS</div>'
      +'</div>'
      +'<div style="background:var(--bg2);border-radius:8px;padding:8px 10px">'
      +rows.map(function(r){
        return '<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);font-size:.76rem">'
          +'<span style="color:var(--muted2)">'+r[0]+'</span>'
          +'<span style="color:var(--text);text-align:right;max-width:55%">'+r[1]+'</span></div>';
      }).join('')
      +'</div>';

    var amtEl=document.getElementById('bbps-amount');
    if(amtEl) amtEl.value=billAmt||'';
    var totalEl=document.getElementById('bbps-total-amt');
    if(totalEl) totalEl.textContent=billAmt?'₹'+fmtN(billAmt+10):'₹—';
    if(as) as.style.display='block';
    if(!silent) toast('Bill fetched! ₹'+fmtN(billAmt)+' due','s');
  }catch(e){
    bc.style.display='none'; bc.innerHTML='';
    if(!silent) toast(e.message||'Could not fetch bill. You can enter the amount manually.','e');
    if(as) as.style.display='block';
  }finally{
    if(fetchBtn){ fetchBtn.disabled=false; fetchBtn.textContent='Re-fetch'; }
  }
}"""

replacements.append(("fetchBBPSBill (real Eko call)", old7, new7))

# ─────────────────────────────────────────────────────────────────
# 8) processService 'bbps' branch — real pay-bill call
# ─────────────────────────────────────────────────────────────────
old8_start_marker = "  // ── BBPS: Direct wallet debit ──────────────────────────────────────────\n  if(svcId==='bbps'){"
old8_end_marker = "    toast('₹'+fmtN(bbpsAmt)+' bill paid + ₹10 charge · ✅','s');\n    return;\n  }"

s8 = content.find(old8_start_marker)
e8 = content.find(old8_end_marker)
if s8 == -1 or e8 == -1:
    print("❌ Could not locate processService('bbps') boundaries — aborting, no changes written.")
    sys.exit(1)
e8_full = e8 + len(old8_end_marker)
old8 = content[s8:e8_full]

new8 = """  // ── BBPS: Real pay-bill via Eko ─────────────────────────────────────────
  if(svcId==='bbps'){
    var cat=window._bbpsCategory||'';
    var biller=window._bbpsBiller||null;
    var consumer=document.getElementById('bbps-consumer')?.value.trim()||'';
    var mobile=document.getElementById('bbps-mobile')?.value.trim()||'';
    var bbpsAmt=parseFloat(document.getElementById('bbps-amount')?.value)||0;
    var billerHint=window._bbpsBillerHint||'Consumer Number';
    var SERVICE_CHARGE=10;
    var totalDebit=bbpsAmt+SERVICE_CHARGE;
    if(!cat){ toast('Select a bill category','e'); return; }
    if(!biller){ toast('Select a biller','e'); return; }
    if(!consumer){ toast('Enter '+billerHint,'e'); return; }
    if(!mobile||mobile.length!==10){ toast("Enter the customer's 10-digit mobile number",'e'); return; }
    if(!bbpsAmt||bbpsAmt<1){ toast('Enter valid amount','e'); return; }
    if(totalDebit>(CU.wallet||0)){ toast('Insufficient wallet balance (need ₹'+fmtN(totalDebit)+')','e'); return; }
    var senderName=(CU&&(CU.shopName||CU.name))||'Retailer';
    var form=document.getElementById('svc-form');
    form.innerHTML='<div style="text-align:center;padding:24px"><div style="width:44px;height:44px;border:4px solid rgba(245,158,11,.2);border-top-color:var(--gold);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 12px"></div><p style="color:var(--gold);font-weight:600">💸 Processing Payment…</p><p style="color:var(--muted2);font-size:.75rem;margin-top:4px">NPCI BBPS via Eko</p></div>';
    var txnId;
    try{
      var r=await fetch(BANKME_API+'/eko/bbps/pay-bill',{
        method:'POST',
        headers:{'content-type':'application/json'},
        body:JSON.stringify({
          phone_operator_code: biller.id,
          utility_acc_no: consumer,
          confirmation_mobile_no: mobile,
          sender_name: senderName,
          category: cat,
          amount: bbpsAmt
        })
      });
      var j=await r.json();
      if(j&&j.success===false){ throw new Error(j.message||'Payment failed'); }
      var d=(j&&j.data)||j||{};
      txnId=d.txn_id||d.referenceId||d.reference_id||('BBP'+Date.now().toString().slice(-8));
    }catch(e){
      form.innerHTML='';
      toast(e.message||'Bill payment failed. Please try again.','e');
      return;
    }
    var now=new Date();
    function pad(n){return String(n).padStart(2,'0');}
    var dateStr=pad(now.getDate())+' '+now.toLocaleString('en-IN',{month:'short'})+' '+now.getFullYear()+' '+pad(now.getHours())+':'+pad(now.getMinutes())+':'+pad(now.getSeconds());
    var catObj=BBPS_CATEGORIES.find(function(c){return c.id===cat;})||{label:cat,icon:'🧾'};
    var txn={id:txnId,service:'bbps',title:'Bill Pay — '+catObj.label+' ('+biller.name+')',amount:bbpsAmt,serviceCharge:SERVICE_CHARGE,totalPaid:totalDebit,type:'debit',date:dateStr,txnId:txnId,status:'success',rtaiVerified:true,biller:biller.name,consumer:consumer,consumerLabel:billerHint,category:cat};
    CU.wallet=Math.max(0,(CU.wallet||0)-totalDebit);
    TXN_HISTORY.push(txn);
    document.getElementById('wallet-chip').textContent='₹'+fmtN(CU.wallet);
    try{if(db&&CU.uid){await db.collection('bankme_users').doc(CU.uid).update({wallet:CU.wallet});}}catch(e){}
    form.style.display='none';
    var res=document.getElementById('svc-result');
    res.style.display='block';
    res.innerHTML='<div style="background:var(--bg3);border:1px solid var(--green);border-radius:14px;padding:16px">'
      +'<div style="text-align:center;margin-bottom:14px">'
      +'<div style="font-size:2.2rem">✅</div>'
      +'<div style="font-family:var(--font-head);font-size:.95rem;font-weight:700;color:var(--green)">Bill Payment Successful!</div>'
      +'<div style="font-size:.68rem;color:var(--rtai);margin-top:2px">💰 Debited from Wallet · NPCI BBPS Processed</div>'
      +'</div>'
      +'<div style="background:var(--bg2);border-radius:10px;padding:10px;margin-bottom:12px">'
      +[['Category',catObj.icon+' '+catObj.label],['Biller',biller.name],[billerHint,consumer],['Bill Amount','₹'+fmtN(bbpsAmt)],['Service Charge','₹'+fmtN(SERVICE_CHARGE)],['Total Paid','₹'+fmtN(totalDebit)],['Paid via','Wallet'],['TXN ID',txnId],['Date & Time',dateStr],['Status','Success ✓']].map(function(r){
        return '<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:.76rem">'
          +'<span style="color:var(--muted2)">'+r[0]+'</span>'
          +'<span style="color:var(--text);font-weight:600;text-align:right;max-width:60%">'+r[1]+'</span></div>';
      }).join('')
      +'</div>'
      +'<div style="display:flex;gap:8px">'
      +'<button onclick="shareAEPS(\\''+txnId+'\\')" style="flex:1;padding:9px;border-radius:9px;background:linear-gradient(135deg,#25D366,#128C7E);border:none;color:#fff;cursor:pointer;font-size:.78rem;font-weight:700">📱 Share Receipt</button>'
      +'<button onclick="document.getElementById(\\'svc-modal\\').classList.remove(\\'show\\')" style="flex:1;padding:9px;border-radius:9px;background:linear-gradient(135deg,var(--rtai),var(--rtai2));border:none;color:#000;cursor:pointer;font-size:.78rem;font-weight:700">Done ✓</button>'
      +'</div></div>';
    toast('₹'+fmtN(bbpsAmt)+' bill paid + ₹10 charge · ✅','s');
    return;
  }"""

replacements.append(("processService 'bbps' branch (real pay-bill)", old8, new8))

# ─────────────────────────────────────────────────────────────────
# Dry-run check: every OLD must appear EXACTLY once
# ─────────────────────────────────────────────────────────────────
ok = True
for name, old, new in replacements:
    count = content.count(old)
    if count != 1:
        ok = False
        print(f"❌ '{name}': expected to find the old text exactly once, found {count}.")
        print("   -> Your file has changed since this script was written against it.")
        print("   -> Nothing has been written. Tell Claude and paste the relevant section fresh.")

if not ok:
    sys.exit(1)

for name, old, new in replacements:
    content = content.replace(old, new, 1)

backup = FILE + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
shutil.copy(FILE, backup)
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ All {len(replacements)} BBPS blocks updated successfully in {FILE}")
print(f"   Backup of the original saved as {backup}")
