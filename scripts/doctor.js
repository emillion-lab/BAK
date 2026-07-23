// doctor.js v3 — прицелен: изважда computeScores и сверява типовете на зоните
const fs = require('fs');
const code = fs.readFileSync('app.js', 'utf8');
const lines = code.split('\n');
const out = [];
function log(s){ out.push(s); console.log(s); }

// ── 1) редовете около 414 ─────────────────────────────────────
log('=== app.js редове 400–430 ===');
for (let i = 399; i < Math.min(lines.length, 430); i++){
  log((i+1) + ': ' + lines[i].slice(0, 200));
}

// ── 2) цялата функция computeScores ───────────────────────────
log('\n=== computeScores ===');
const ci = code.search(/function\s+computeScores\s*\(/);
if (ci < 0) log('не е намерена');
else {
  const startLine = code.slice(0, ci).split('\n').length;
  log('започва на ред ' + startLine);
  // до затварящата скоба
  let d = 0, started = false, end = ci;
  for (let i = ci; i < code.length; i++){
    if (code[i] === '{'){ d++; started = true; }
    else if (code[i] === '}'){ d--; if (started && !d){ end = i; break; } }
  }
  const fn = code.slice(ci, end + 1);
  log('дължина: ' + fn.length + ' знака');
  // всички .push в нея
  log('\n--- .push обръщения ---');
  for (const m of fn.matchAll(/([\w$.\[\]'"]+)\.push\(/g)){
    const ln = startLine + fn.slice(0, m.index).split('\n').length - 1;
    log('  ред ~' + ln + ': ' + m[1] + '.push(');
  }
  // обектни карти по тип
  log('\n--- обекти/карти в computeScores (първи 1500 знака) ---');
  log(fn.slice(0, 1500));
}

// ── 3) всички типове зони срещу типовете, използвани в кода ───
log('\n=== типове ===');
const zm = code.match(/const\s+ZONES\s*=\s*\[/);
const zoneTypes = {};
if (zm){
  const start = code.indexOf('[', zm.index);
  let d = 0, end = start;
  for (let i = start; i < code.length; i++){
    if (code[i] === '[') d++;
    else if (code[i] === ']'){ d--; if (!d){ end = i; break; } }
  }
  const body = code.slice(start, end + 1);
  for (const m of body.matchAll(/\{\s*id:"([^"]+)"[^{}]*type:"([^"]+)"/g)){
    (zoneTypes[m[2]] = zoneTypes[m[2]] || []).push(m[1]);
  }
}
log('типове в ZONES: ' + Object.keys(zoneTypes).sort().join(', '));
for (const t of Object.keys(zoneTypes).sort()){
  log('  ' + t + ': ' + zoneTypes[t].length + ' зони  [' + zoneTypes[t].slice(0,4).join(', ') + ']');
}

// търсим карта тип->нещо в целия файл
log('\n--- места, където типът се ползва като ключ ---');
const typeKeyRx = /\b(\w+)\s*\[\s*(?:z|zone|zn)\.type\s*\]/g;
for (const m of code.matchAll(typeKeyRx)){
  const ln = code.slice(0, m.index).split('\n').length;
  log('  ред ' + ln + ': ' + m[0]);
}
// и обекти, чиито ключове изглеждат като типове
const knownTypes = Object.keys(zoneTypes);
const objRx = /(\w+)\s*=\s*\{([^{}]{40,900})\}/g;
for (const m of code.matchAll(objRx)){
  const inner = m[2];
  const keys = [...inner.matchAll(/(\w+)\s*:/g)].map(x => x[1]);
  const hit = knownTypes.filter(t => keys.includes(t));
  if (hit.length >= 4){
    const missing = knownTypes.filter(t => !keys.includes(t));
    const ln = code.slice(0, m.index).split('\n').length;
    log('  ред ' + ln + ': ' + m[1] + ' покрива ' + hit.length + '/' + knownTypes.length
        + ' типа' + (missing.length ? ('  ❌ ЛИПСВАТ: ' + missing.join(', ')) : '  ✓ пълен'));
  }
}

fs.mkdirSync('debug', { recursive:true });
fs.writeFileSync('debug/doctor-report.txt', out.join('\n') + '\n', 'utf8');
