// doctor.js v2 — по-пълен шим (canvas, Image, URL, Date локали),
// за да стигнем до истинската грешка, а не до липса в шима.
const fs = require('fs');
const code = fs.readFileSync('app.js', 'utf8');
const out = [];
function log(s){ out.push(s); console.log(s); }

// ── 1) ZONES структура ─────────────────────────────────────────
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
    // само ,, е истинска дупка; траилинг запетая е легална
    log(/,\s*,/.test(body) ? '❌ ,, празен елемент в ZONES' : '✓ няма празни елементи');
    log('  зонови обекта: ' + (body.match(/\{\s*id:"[^"]+"/g) || []).length);
    const ids = [...body.matchAll(/\{\s*id:"([^"]+)"/g)].map(x => x[1]);
    const dup = ids.filter((v,i) => ids.indexOf(v) !== i);
    log(dup.length ? ('❌ дубликати: ' + [...new Set(dup)].join(',')) : '✓ няма дубликати');
    // валидни координати
    const badCoord = [];
    for (const z of body.matchAll(/\{\s*id:"([^"]+)"[^{}]*?lat:([\d.]+)\s*,\s*lng:([\d.]+)/g)){
      const la = parseFloat(z[2]), ln = parseFloat(z[3]);
      if (!(la > 42.5 && la < 42.85 && ln > 23.1 && ln < 23.5)) badCoord.push(z[1] + ' ' + la + ',' + ln);
    }
    log(badCoord.length ? ('⚠ извън София: ' + badCoord.join(' | ')) : '✓ всички координати в София');
  }
} catch(e){ log('ZONES проверка гръмна: ' + e.message); }

// ── 2) по-пълен фалшив браузър ─────────────────────────────────
const domHandlers = [];
function ctx2d(){
  const noop = () => {};
  return new Proxy({
    canvas:{width:300,height:150},
    measureText: () => ({width:10}),
    createLinearGradient: () => ({ addColorStop: noop }),
    createRadialGradient: () => ({ addColorStop: noop }),
    createPattern: () => ({}),
    getImageData: () => ({ data:[] }),
    fillStyle:'', strokeStyle:'', lineWidth:1, font:'', globalAlpha:1
  }, { get(t,k){ return (k in t) ? t[k] : noop; }, set(t,k,v){ t[k]=v; return true; } });
}
function fakeEl(tag){
  const el = {
    tagName:(tag||'div').toUpperCase(), style:{}, dataset:{},
    textContent:'', innerHTML:'', innerText:'', value:'', id:'', className:'',
    children:[], childNodes:[], parentElement:null, parentNode:null,
    offsetWidth:360, offsetHeight:640, clientWidth:360, clientHeight:640,
    width:360, height:200, scrollTop:0, scrollHeight:1000,
    classList:{ add(){}, remove(){}, toggle(){}, contains(){return false} },
    appendChild(c){ this.children.push(c); return c; },
    insertBefore(c){ this.children.push(c); return c; },
    insertAdjacentHTML(){}, removeChild(){}, remove(){}, replaceChildren(){},
    setAttribute(){}, getAttribute(){return null}, removeAttribute(){},
    addEventListener(){}, removeEventListener(){}, dispatchEvent(){},
    querySelector(){ return null }, querySelectorAll(){ return [] },
    closest(){ return null },
    getBoundingClientRect(){ return {top:0,left:0,right:360,bottom:640,width:360,height:640} },
    getContext(){ return ctx2d(); },
    scrollIntoView(){}, focus(){}, click(){}, blur(){}, play(){}, pause(){}
  };
  return el;
}
const leafletObj = new Proxy({}, { get(){ return () => leafletObj; }, apply(){ return leafletObj; } });
const L = new Proxy(function(){ return leafletObj; }, {
  get(t,k){
    if (k === 'Icon'){ const f = function(){ return leafletObj; }; f.Default = function(){ return leafletObj; }; return f; }
    return function(){ return leafletObj; };
  },
  apply(){ return leafletObj; }
});

global.window = global;
global.self = global;
global.L = L;
global.document = {
  readyState:'loading', title:'', cookie:'',
  body: fakeEl('body'), head: fakeEl('head'), documentElement: fakeEl('html'),
  addEventListener(ev, fn){ if (ev === 'DOMContentLoaded') domHandlers.push(fn); },
  removeEventListener(){},
  getElementById(){ return fakeEl(); },
  getElementsByClassName(){ return [] },
  getElementsByTagName(){ return [] },
  querySelector(){ return fakeEl(); },
  querySelectorAll(){ return []; },
  createElement(t){ return fakeEl(t); },
  createElementNS(){ return fakeEl(); },
  createTextNode(){ return fakeEl(); },
  createDocumentFragment(){ return fakeEl(); }
};
global.navigator = { userAgent:'node', language:'bg', languages:['bg'], onLine:true,
  geolocation:{ getCurrentPosition(){}, watchPosition(){ return 1 }, clearWatch(){} },
  serviceWorker:{ register(){ return Promise.resolve({}) }, ready: Promise.resolve({}) },
  vibrate(){}, share(){ return Promise.resolve() }, clipboard:{ writeText(){ return Promise.resolve() } } };
global.location = { href:'https://x/', hostname:'x', protocol:'https:', search:'', hash:'', reload(){} };
global.history = { pushState(){}, replaceState(){} };
global.localStorage = { getItem(){ return null }, setItem(){}, removeItem(){}, clear(){} };
global.sessionStorage = global.localStorage;
global.fetch = () => Promise.resolve({ ok:true, status:200,
  json:()=>Promise.resolve({}), text:()=>Promise.resolve(''), headers:{ get(){ return null } } });
global.XMLHttpRequest = function(){ this.open=function(){}; this.send=function(){}; this.setRequestHeader=function(){}; };
global.setInterval = () => 0;
global.clearInterval = () => {};
global.setTimeout = () => 0;
global.clearTimeout = () => {};
global.requestAnimationFrame = () => 0;
global.MutationObserver = function(){ this.observe=function(){}; this.disconnect=function(){}; };
global.ResizeObserver = function(){ this.observe=function(){}; this.disconnect=function(){}; };
global.IntersectionObserver = function(){ this.observe=function(){}; this.disconnect=function(){}; };
global.Image = function(){ return fakeEl('img'); };
global.Audio = function(){ return fakeEl('audio'); };
global.alert = () => {};
global.confirm = () => true;
global.prompt = () => null;
global.matchMedia = () => ({ matches:false, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} });
global.getComputedStyle = () => new Proxy({}, { get(){ return 'static'; } });
global.Notification = function(){}; global.Notification.permission='default';
global.Notification.requestPermission = () => Promise.resolve('denied');
global.screen = { width:360, height:640 };
global.devicePixelRatio = 2;
global.scrollTo = () => {};
global.open = () => null;

// ── 3) изпълнение ──────────────────────────────────────────────
try {
  new Function(code)();
  log('✓ top-level изпълнение мина');
} catch(e){
  log('❌ TOP-LEVEL: ' + e.constructor.name + ': ' + e.message);
  log('   ' + (e.stack||'').split('\n').slice(0,3).join(' ⏎ '));
}

log('DOMContentLoaded хендлъри: ' + domHandlers.length);
domHandlers.forEach((fn, i) => {
  try { fn({}); log('✓ DOMContentLoaded #' + (i+1) + ' мина ДОКРАЙ'); }
  catch(e){
    log('❌ DOMContentLoaded #' + (i+1) + ': ' + e.constructor.name + ': ' + e.message);
    const lines = (e.stack||'').split('\n').slice(1,4);
    lines.forEach(l => log('   ' + l.trim()));
    // извади реда от кода
    const m = (e.stack||'').match(/<anonymous>:(\d+):(\d+)/);
    if (m){
      const ln = parseInt(m[1],10);
      const src = code.split('\n');
      for (let k = Math.max(0, ln-3); k < Math.min(src.length, ln+2); k++){
        log('   ' + (k+1===ln ? '>>> ' : '    ') + (k+1) + ': ' + src[k].slice(0,150));
      }
    }
  }
});

fs.mkdirSync('debug', { recursive:true });
fs.writeFileSync('debug/doctor-report.txt', out.join('\n') + '\n', 'utf8');
