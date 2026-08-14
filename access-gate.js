/* BAK · заключване на достъпа с код
 *
 * Самостоятелен файл — не пипа останалата логика на приложението.
 * Чете списъка от fish.taxi (cross-origin, GitHub Pages праща CORS *).
 *
 * ЧЕСТНО: това е обфускация, не защита. Списъкът е публичен, проверката
 * е на клиента. Спира случайно споделяне на код и дава лесно отнемане.
 * Истинската проверка идва с api/ (D1 + Worker).
 *
 * Слага на <body> един от три класа:
 *   ft-demo   — без код: живите данни се замъгляват
 *   ft-full   — валиден код
 *   ft-admin  — валиден код с роля admin
 */

(function () {
  'use strict';

  var PEPPER = 'fishtaxi-access-v1';
  var LIST_URL = 'https://fish.taxi/data/access.json';
  var LS_KEY = 'bak_access';
  var CACHE_KEY = 'bak_access_cache';
  var RECHECK_MS = 3600 * 1000;          // 1 час
  var DEMO_MS = 30 * 60 * 1000;          // 30 мин демо на устройство
  var DEMO_KEY = 'bak_demo_until';

  function sha256hex(s) {
    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))
      .then(function (buf) {
        return Array.prototype.map.call(new Uint8Array(buf), function (b) {
          return b.toString(16).padStart(2, '0');
        }).join('');
      });
  }

  function hashCode(c) {
    var n = String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    return sha256hex(PEPPER + ':' + n).then(function (h) { return h.slice(0, 16); });
  }

  function ls(k, v) {
    try {
      if (v === undefined) return JSON.parse(localStorage.getItem(k) || 'null');
      if (v === null) { localStorage.removeItem(k); return null; }
      localStorage.setItem(k, JSON.stringify(v));
      return v;
    } catch (e) { return null; }
  }

  function fetchList() {
    return fetch(LIST_URL + '?t=' + Math.floor(Date.now() / 60000))
      .then(function (r) { return r.json(); })
      .then(function (j) { ls(CACHE_KEY, { at: Date.now(), list: j }); return j; })
      .catch(function () {
        var c = ls(CACHE_KEY);
        return c ? c.list : null;   // без мрежа: последният известен списък
      });
  }

  function applyLevel(level, rec) {
    var b = document.body;
    if (!b) return;
    b.classList.remove('ft-demo', 'ft-full', 'ft-admin');
    b.classList.add(level === 'demo' ? 'ft-demo' : (rec && rec.role === 'admin' ? 'ft-admin' : 'ft-full'));
    window.BAKAccess = window.BAKAccess || {};
    window.BAKAccess.level = level;
    window.BAKAccess.driver = rec || null;
    try {
      document.dispatchEvent(new CustomEvent('bak:access', { detail: { level: level, driver: rec || null } }));
    } catch (e) {}
  }

  function check() {
    var rec = ls(LS_KEY);
    if (!rec) return Promise.resolve({ level: 'demo', driver: null });
    if (Date.now() - (rec.checked || 0) < RECHECK_MS)
      return Promise.resolve({ level: 'full', driver: rec });

    return fetchList().then(function (list) {
      if (!list) return { level: 'full', driver: rec };   // без мрежа не наказваме
      var hit = (list.drivers || []).filter(function (d) { return d.hash === rec.hash; })[0];
      if (!hit || hit.status !== 'active') {
        ls(LS_KEY, null);
        return { level: 'demo', driver: null, revoked: true };
      }
      hit.hash = rec.hash; hit.checked = Date.now();
      ls(LS_KEY, hit);
      return { level: 'full', driver: hit };
    });
  }

  function redeem(code) {
    return hashCode(code).then(function (h) {
      return fetchList().then(function (list) {
        if (!list) return { ok: false, reason: 'Няма връзка. Опитай пак.' };
        var hit = (list.drivers || []).filter(function (d) { return d.hash === h; })[0];
        if (!hit) return { ok: false, reason: 'Непознат код.' };
        if (hit.status !== 'active') return { ok: false, reason: 'Кодът е спрян.' };
        hit.hash = h; hit.checked = Date.now();
        ls(LS_KEY, hit);
        return { ok: true, driver: hit };
      });
    });
  }

  function demoLeft() {
    var until = ls(DEMO_KEY);
    if (!until) return null;
    return Math.max(0, until - Date.now());
  }

  function startDemo() {
    var until = ls(DEMO_KEY);
    if (!until || until < Date.now() - 24 * 3600 * 1000) {
      until = Date.now() + DEMO_MS;
      ls(DEMO_KEY, until);
    }
    return until;
  }

  // ─── Изглед ───────────────────────────────────────────────────────────

  function css() {
    if (document.getElementById('bak-gate-css')) return;
    var s = document.createElement('style');
    s.id = 'bak-gate-css';
    s.textContent = [
      '#bak-gate{position:fixed;inset:0;z-index:99999;background:rgba(10,10,11,.94);',
      'backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;padding:24px;',
      'font-family:-apple-system,BlinkMacSystemFont,Inter,sans-serif}',
      '#bak-gate .bx{width:100%;max-width:360px;text-align:center;color:#f2f0ea}',
      '#bak-gate h2{font-size:1.3rem;margin:0 0 8px;font-weight:700}',
      '#bak-gate p{font-size:.94rem;color:#a8a49a;margin:0 0 20px;line-height:1.55}',
      '#bak-gate input{width:100%;padding:16px;font-size:1.3rem;text-align:center;',
      'letter-spacing:.22em;text-transform:uppercase;border-radius:12px;border:2px solid #3a3a3c;',
      'background:#1a1a1c;color:#f2f0ea;outline:none;font-family:inherit}',
      '#bak-gate input:focus{border-color:#f5c518}',
      '#bak-gate .go{width:100%;margin-top:12px;padding:16px;border:none;border-radius:12px;',
      'background:#f5c518;color:#0a0a0a;font-size:1.02rem;font-weight:700;font-family:inherit}',
      '#bak-gate .demo{margin-top:16px;background:none;border:none;color:#a8a49a;',
      'font-size:.9rem;text-decoration:underline;font-family:inherit}',
      '#bak-gate .er{color:#ff6b6b;font-size:.88rem;min-height:1.2em;margin-top:10px;font-weight:600}',
      'body.ft-demo [data-live]{filter:blur(7px);pointer-events:none;user-select:none}',
      '#bak-demobar{position:fixed;left:0;right:0;bottom:0;z-index:9998;background:#f5c518;',
      'color:#0a0a0a;padding:11px 16px;font-size:.88rem;font-weight:600;text-align:center;',
      'font-family:-apple-system,BlinkMacSystemFont,Inter,sans-serif}',
      '#bak-demobar b{text-decoration:underline}'
    ].join('');
    document.head.appendChild(s);
  }

  function showGate() {
    css();
    if (document.getElementById('bak-gate')) return;
    var d = document.createElement('div');
    d.id = 'bak-gate';
    d.innerHTML =
      '<div class="bx">' +
        '<h2>БАКШИШ</h2>' +
        '<p>Въведи кода, който получи по Viber или WhatsApp.</p>' +
        '<input id="bak-code" maxlength="9" placeholder="XXXXXXXX" autocomplete="off" ' +
        'autocapitalize="characters" spellcheck="false" inputmode="text">' +
        '<div class="er" id="bak-err"></div>' +
        '<button class="go" id="bak-go">Влез</button>' +
        '<button class="demo" id="bak-demo">Разгледай в демо режим</button>' +
      '</div>';
    document.body.appendChild(d);

    var inp = d.querySelector('#bak-code');
    var er = d.querySelector('#bak-err');
    inp.focus();

    d.querySelector('#bak-go').onclick = function () {
      er.textContent = '';
      redeem(inp.value).then(function (r) {
        if (!r.ok) { er.textContent = r.reason; return; }
        d.remove();
        var bar = document.getElementById('bak-demobar');
        if (bar) bar.remove();
        applyLevel('full', r.driver);
      });
    };

    inp.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') d.querySelector('#bak-go').click();
    });

    d.querySelector('#bak-demo').onclick = function () {
      startDemo();
      d.remove();
      applyLevel('demo', null);
      showDemoBar();
    };
  }

  function showDemoBar() {
    css();
    if (document.getElementById('bak-demobar')) return;
    var b = document.createElement('div');
    b.id = 'bak-demobar';
    b.innerHTML = 'Демо режим · живите данни са скрити · <b>въведи код</b>';
    b.onclick = showGate;
    document.body.appendChild(b);
  }

  function boot() {
    check().then(function (r) {
      applyLevel(r.level, r.driver);
      if (r.level === 'demo') {
        var left = demoLeft();
        if (left === null || left <= 0) showGate();
        else showDemoBar();
      }
    });
  }

  window.BAKAccess = {
    redeem: redeem,
    check: check,
    showGate: showGate,
    signOut: function () { ls(LS_KEY, null); location.reload(); },
    isAdmin: function () { var r = ls(LS_KEY); return !!(r && r.role === 'admin'); }
  };

  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
