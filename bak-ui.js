/* BAK · лого с рибата и бутон „Моят профил“ (12.11.2026)
 * Само добавя в горната лента — нищо не маха и не пипа app.js.
 * Бутонът се показва само на влезли (същият код като за BAK) и води към profil.html,
 * където шофьорът сменя музика, езици, екстри (преместено от fish.taxi).
 * Докосване на логото = ден/нощ (същото като бутона ◐); нощем рибата е на черна плочка.
 */
(function () {
  'use strict';
  var LOGO = 'data:image/png;base64,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';

  var NIGHT = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIwAAABCCAMAAACy/M7IAAAAkFBMVEVjUiaUbhn16Z2omF60kSrr0mXOslXZqyz94jAxJRCIelB7bkXKuodGOSG2rYEBAADyuQjjqAP6xQ7WmgPcogRNKgYpGARTNAlxRQX81io2JQkaEwhmOQWHVwWTZgj4yC/81k6qdwjoty+1hAv95HD0123+9rPWqCz90hnyyE7DigR1Vg3+/dH86JHmukfl141z77FrAAAAMHRSTlP///////////////////////////////////////////////////////////////9Ppz/1AAAIwElEQVR42u2aaZebuBKGAds4TjJjYSEJs68mmLb7//+7qdJm7Ab3cm5m7ofUSXLACOnhrZJKS5z9/5E5f2D+wPwrMHznOD++r4x9dxwR/wcwyc5ZrbzL6eXRvNefK0fwfw0mcdzVq3cC89p2s9l8QzuilWV78RDQ81dO8vthYmfVeSfPa8vj8RfYcWpwfwA7liiZt3I+4zPhuZ+D2bl+CxwbifEAYlG0IZDnOx91mChP3vrjMLHjdy0IAg3ZVqdAUxI0cija08vr6kPfKYb219HzPwjjrDaaZGKI8k3bG2mkFZeXkz++Gz5x3WJt3oa/D5OgKA8k6KcD2YZ03TQVWtOsaUi0KsqkPuXptHGf48TbVr236eJ3YBL3CqLcgxwIbfLMje4sjdI0yvKGkikPIaV36p7hJH1b6K8Y3KcwiQMoU1EAZJ1n0G4qhGAx54lqJ+E8juEnAU/cipIbDyHF5bQZF1vYWpYwe6rMIwqhueQAisVxOWZAmWaN5cHg8U6+mGdZd4WS8BBIliUYp+/aYoIiSQR7v78mAAQ8lBgcjJ3Leu5FxYIlSMaWe1O8LrvC9FPQsIrAM/GHR1bOGIuqibu6Uxe9KeV2g+HN2XLXdq5TFJohyScH9lgwkYca5wCh4zUP3+KWpWURi4MeyFJKCvyHVOier2SbhKUp4GhxSPkQOTeWgysW08FYlwVRHgeUlH19bgDeSnMTO6Tw2nwi/o2lEkuJMlkPUhZZrEnZJGQTa6ZDm0v98HZtcaC7Vxan9ZobS2fiqUqXsnbcG1kgViKN4m58HyYMXde9gnWvcuje4fWrp19fveJj9Yn+KxSGZPMjljgsooam9LZKZmeYZbmHierB9Mgg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';

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
      '.header .hdr-right{flex:none}' +
      '.header .bak-logo{cursor:pointer;border-radius:5px;transition:transform .18s cubic-bezier(.3,1.5,.5,1)}' +
      '.header .bak-logo:active{transform:scale(.92)}' +
      '#bak-toast{position:fixed;left:50%;top:calc(env(safe-area-inset-top,0px) + 70px);transform:translate(-50%,-16px);z-index:99990;' +
      'background:rgba(24,28,32,.72);color:#eef0ee;border:1px solid rgba(255,255,255,.14);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);' +
      'padding:11px 16px;border-radius:14px;font:500 15px -apple-system,BlinkMacSystemFont,Roboto,sans-serif;opacity:0;pointer-events:none;' +
      'transition:all .4s cubic-bezier(.3,1.5,.5,1);white-space:nowrap}' +
      '#bak-toast.on{opacity:1;transform:translate(-50%,0)}' +
      'body.theme-day #bak-toast{background:rgba(255,255,255,.85);color:#15191c;border-color:rgba(15,20,25,.12)}';
    document.head.appendChild(s);
  }

  function mount() {
    var h = document.querySelector('.header');
    if (!h) return;
    css();
    if (!h.querySelector('.bak-logo')) {
      var i = document.createElement('img');
      i.className = 'bak-logo'; i.alt = 'fish.taxi';
      i.title = 'Ден / нощ'; i.setAttribute('role', 'button');
      i.addEventListener('click', flip);
      h.insertBefore(i, h.firstChild);
    }
    logo();
    var r = h.querySelector('.hdr-right'), b = document.getElementById('bak-prof');
    if (logged() && r && !b) {
      b = document.createElement('a');
      b.id = 'bak-prof'; b.href = 'profil.html'; b.title = 'Моят профил';
      b.setAttribute('aria-label', 'Моят профил');
      b.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4.5 20.5c1.4-3.6 4.2-5.5 7.5-5.5s6.1 1.9 7.5 5.5"/></svg>';
      r.appendChild(b);
    } else if (!logged() && b) b.remove();
  }

  function night() { return document.body.classList.contains('theme-night'); }
  function logo() { var i = document.querySelector('.header .bak-logo'); if (i) i.src = night() ? NIGHT : LOGO; }
  function toast(m) {
    var t = document.getElementById('bak-toast');
    if (!t) { t = document.createElement('div'); t.id = 'bak-toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.textContent = m; t.classList.add('on'); clearTimeout(toast.t);
    toast.t = setTimeout(function () { t.classList.remove('on'); }, 2400);
  }
  /* логото прави същото като бутона за темата — и казва какво е станало */
  function flip() {
    var b = document.getElementById('theme-btn');
    if (!b) return;
    b.click();
    try { if (navigator.vibrate) navigator.vibrate(10); } catch (e) {}
    setTimeout(function () { logo(); toast(night() ? '🌙 Нощен режим · докосни логото за дневен' : '☀️ Дневен режим · докосни логото за нощен'); }, 30);
  }
  /* темата се сменя и сама (по часа) — логото я следва */
  new MutationObserver(logo).observe(document.body, { attributes: true, attributeFilter: ['class'] });

  document.addEventListener('bak:access', mount);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
