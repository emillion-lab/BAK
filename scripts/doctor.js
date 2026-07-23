// doctor.js — намира РУНТАЙМ грешката в app.js (node --check хваща само синтаксис).
// Прави фалшив DOM/Leaflet, изпълнява файла, после ръчно вика DOMContentLoaded
// хендлърите — там живее основната логика на приложението.
const fs = require('fs');
const path = 'app.js';
const code = fs.readFileSync(path, 'utf8');
const out = [];

function log(s){ out.push(s); console.log(s); }

// ── 1) структурна проверка на ZONES ────────────────────────────
try {
  const m = code.match(/const\s+ZONES\s*=\s*\[/);
  if (!m) log('❌ ZONES не е намерен');
  else {
    const start = code.indexOf('[', m.index);
    let d = 0, end = start;
    for (let i = start; i < code.length; i++){
      if (code[i] === '[') d++;
      else if (code[i] === ']'){ d--; if (!d){ end = i; break; } }
    }
    const body = code.slice(start, end + 1);
    // дупки в масива: ,, или [, или ,]
    const holes = [];
    if (/\[\s*,/.test(body)) holes.push('[, в началото');
    if (/,\s*,/.test(body)) holes.push(',, (празен елемент)');
    if (/,\s*\]/.test(body)) holes.push(', ] в края');
    log(holes.length ? ('❌ ДУПКИ В МАСИВА: ' + holes.join(' | '))
                     : '✓ няма дупки в ZONES');
    const objs = body.match(/\{\s*id:"[^"]+"/g) || [];
    log('  зонови обекта: ' + objs.length);
    // липсващи полета
    const bad = [];
    const re = /\{\s*id:"([^"]+)"[^{}]*\}/g;
    let z;
    while ((z = re.exec(body))){
      const s = z[0];
      ['name:', 'lat:', 'lng:', 'type:'].forEach(f => {
        if (s.indexOf(f) < 0) bad.push(z[1] + ' липсва ' + f);
      });
    }
    log(bad.length ? ('❌ ' + bad.join(' | ')) : '✓ всички зони с пълни полета');
  }
} catch(e){ log('ZONES проверка гръмна: ' + e.message); }

// ── 2) фалшив браузър ──────────────────────────────────────────
const domHandlers = [];
function fakeEl(){
  const el = {
    style:{}, dataset:{}, textContent:'', innerHTML:'', value:'',
    children:[], parentElement:null, offsetWidth:100, offsetHeight:100,
    classList:{ add(){}, remove(){}, toggle(){}, contains(){return false} },
    appendChild(c){ this.children.push(c); return c; },
    insertAdjacentHTML(){}, removeChild(){}, remove(){},
    setAttribute(){}, getAttribute(){return null}, addEventListener(){},
    querySelector(){ return null }, querySelectorAll(){ return [] },
    getBoundingClientRect(){ return {top:0,left:0,width:100,height:100} },
    scrollIntoView(){}, focus(){}, click(){}
  };
  return el;
}
const leafletObj = new Proxy({}, { get(){ return () => leafletObj; },
                                   apply(){ return leafletObj; } });
function LFn(){ return leafletObj; }
const L = new Proxy(LFn, {
  get(t,k){
    if (k === 'Icon') { const f = function(){ return leafletObj; }; f.Default = function(){ return leafletObj; }; return f; }
    return function(){ return leafletObj; };
  },
  apply(){ return leafletObj; }
});

global.window = global;
global.L = L;
global.document = {
  readyState:'loading',
  body: fakeEl(), head: fakeEl(), documentElement: fakeEl(),
  addEventListener(ev, fn){ if (ev === 'DOMContentLoaded') domHandlers.push(fn); },
  removeEventListener(){},
  getElementById(){ return fakeEl(); },
  querySelector(){ return fakeEl(); },
  querySelectorAll(){ return []; },
  createElement(){ return fakeEl(); },
  createTextNode(){ return fakeEl(); },
  cookie:''
};
global.navigator = { userAgent:'node', language:'bg',
                     geolocation:{ getCurrentPosition(){}, watchPosition(){ return 1 } },
                     serviceWorker:{ register(){ return Promise.resolve({}) } } };
global.location = { href:'https://x/', hostname:'x', protocol:'https:', search:'' };
global.localStorage = { getItem(){ return null }, setItem(){}, removeItem(){} };
global.sessionStorage = global.localStorage;
global.fetch = () => Promise.resolve({ ok:true, json:()=>Promise.resolve({}),
                                       text:()=>Promise.resolve('') });
global.setInterval = () => 0;
global.setTimeout  = () => 0;
global.requestAnimationFrame = () => 0;
global.MutationObserver = function(){ this.observe = function(){}; this.disconnect = function(){}; };
global.alert = () => {};
global.matchMedia = () => ({ matches:false, addListener(){}, addEventListener(){} });
global.getComputedStyle = () => ({ position:'static', display:'block' });
global.Notification = { permission:'default', requestPermission(){ return Promise.resolve('denied') } };

// ── 3) изпълнение на файла ─────────────────────────────────────
let topErr = null;
try {
  new Function(code)();
  log('✓ top-level изпълнение мина');
} catch(e){
  topErr = e;
  log('❌ TOP-LEVEL ГРЕШКА: ' + e.constructor.name + ': ' + e.message);
  const st = (e.stack||'').split('\n').slice(0,4).join(' ⏎ ');
  log('   ' + st);
}

// ── 4) ръчно пускане на DOMContentLoaded (там е логиката) ──────
log('регистрирани DOMContentLoaded хендлъри: ' + domHandlers.length);
domHandlers.forEach((fn, i) => {
  try {
    fn({});
    log('✓ DOMContentLoaded #' + (i+1) + ' мина');
  } catch(e){
    log('❌ ГРЕШКА В DOMContentLoaded #' + (i+1) + ': ' + e.constructor.name + ': ' + e.message);
    const st = (e.stack||'').split('\n').slice(1,5).join(' ⏎ ');
    log('   ' + st);
  }
});

fs.mkdirSync('debug', { recursive:true });
fs.writeFileSync('debug/doctor-report.txt', out.join('\n') + '\n', 'utf8');
