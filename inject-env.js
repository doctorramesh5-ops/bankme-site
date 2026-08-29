// inject-env.js
// Runs at Netlify build time — replaces placeholders with env variables
const fs = require('fs');

const file = 'app.html';
let html = fs.readFileSync(file, 'utf8');

html = html
  .replace('__FIREBASE_API_KEY__',             process.env.FIREBASE_API_KEY || '')
  .replace('__FIREBASE_AUTH_DOMAIN__',         process.env.FIREBASE_AUTH_DOMAIN || '')
  .replace('__FIREBASE_PROJECT_ID__',          process.env.FIREBASE_PROJECT_ID || '')
  .replace('__FIREBASE_STORAGE_BUCKET__',      process.env.FIREBASE_STORAGE_BUCKET || '')
  .replace('__FIREBASE_MESSAGING_SENDER_ID__', process.env.FIREBASE_MESSAGING_SENDER_ID || '')
  .replace('__FIREBASE_APP_ID__',              process.env.FIREBASE_APP_ID || '');

fs.writeFileSync(file, html, 'utf8');
console.log('✅ Firebase env vars injected into app.html');
