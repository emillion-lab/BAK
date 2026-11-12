/* BAK · лого с рибата и бутон „Моят профил“ (12.11.2026)
 * Само добавя в горната лента — нищо не маха и не пипа app.js.
 * Бутонът се показва само на влезли (същият код като за BAK) и води към profil.html,
 * където шофьорът сменя музика, езици, екстри (преместено от fish.taxi).
 */
(function () {
  'use strict';
  var LOGO = 'data:image/png;base64,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';

  function logged() { try { return !!localStorage.getItem('bak_access'); } catch (e) { return false; } }

  function css() {
    if (document.getElementById('bak-ui-css')) return;
    var s = document.createElement('style');
    s.id = 'bak-ui-css';
    s.textContent =
      '.header .bak-logo{height:24px;width:auto;flex:none;display:block;filter:drop-shadow(0 1px 3px rgba(0,0,0,.45))}' +
      '#bak-prof{width:32px;height:32px;flex:none;border-radius:50%;display:grid;place-items:center;' +
      'background:rgba(24,28,32,.38);box-shadow:0 0 0 1px rgba(255,255,255,.14),0 6px 16px rgba(0,0,0,.3);' +
      'backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);text-decoration:none;' +
      'transition:transform .18s cubic-bezier(.3,1.5,.5,1)}' +
      '#bak-prof:active{transform:scale(.9)}' +
      '#bak-prof svg{width:17px;height:17px;fill:none;stroke:#e6c36a;stroke-width:2;stroke-linecap:round}' +
      'body.theme-day #bak-prof{background:rgba(255,255,255,.6);box-shadow:0 0 0 1px rgba(15,20,25,.12),0 6px 16px rgba(15,27,45,.12)}' +
      'body.theme-day #bak-prof svg{stroke:#9a7424}' +
      /* тесен екран: заглавието се съкращава, дясната част остава видима */
      '.header>div:not(.hdr-right){min-width:0;flex:1 1 auto;overflow:hidden}' +
      '.header h1,.header p{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
      '.header .hdr-right{flex:none}';
    document.head.appendChild(s);
  }

  function mount() {
    var h = document.querySelector('.header');
    if (!h) return;
    css();
    if (!h.querySelector('.bak-logo')) {
      var i = document.createElement('img');
      i.className = 'bak-logo'; i.src = LOGO; i.alt = 'fish.taxi';
      h.insertBefore(i, h.firstChild);
    }
    var r = h.querySelector('.hdr-right'), b = document.getElementById('bak-prof');
    if (logged() && r && !b) {
      b = document.createElement('a');
      b.id = 'bak-prof'; b.href = 'profil.html'; b.title = 'Моят профил';
      b.setAttribute('aria-label', 'Моят профил');
      b.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4.5 20.5c1.4-3.6 4.2-5.5 7.5-5.5s6.1 1.9 7.5 5.5"/></svg>';
      r.appendChild(b);
    } else if (!logged() && b) b.remove();
  }

  document.addEventListener('bak:access', mount);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
