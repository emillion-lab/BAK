# -*- coding: utf-8 -*-
# BAK · Waze и Google Maps спират да връщат PAGE NOT FOUND от PWA
#
# ТРИ ПОПРАВКИ:
#  1. Хостът беше `https://waze.com/ul` — БЕЗ www. Апексът не сервира /ul
#     и връща точно страницата PAGE NOT FOUND, която се вижда.
#     Правилният е `https://www.waze.com/ul`.
#  2. Запетаята между координатите беше кодирана като %2C.
#     Waze я иска сурова: ll=42.6885,23.4082
#  3. В инсталирано PWA схемата waze:// през скрит iframe се блокира тихо
#     от WebView-то. Нищо не се случва, таймерът от 1.2s пада и отвежда
#     на уеб адреса — тоест право в счупения линк. Затова в standalone
#     режим се тръгва направо към https, а Android сам предлага Waze
#     през app links.
#
# Същата трета поправка важи и за Google Maps (geo: схемата).
#
# Идемпотентен.
import io, sys

p = sys.argv[1] if len(sys.argv) > 1 else 'app.js'
s = io.open(p, encoding='utf-8').read()
n0 = len(s)

if 'FT-WAZE-FIX' in s:
    print('SKIP: waze fix already applied'); sys.exit(0)

def rep(old, new, tag, expect=1):
    global s
    if s.count(old) != expect:
        print('FAIL anchor (%d hits, expected %d): %s' % (s.count(old), expect, tag))
        sys.exit(1)
    s = s.replace(old, new)
    print(' -', tag)

rep("""window.openWaze = function(name, lat, lng){
  var hasLL = isFinite(lat) && isFinite(lng);
  var q   = encodeURIComponent(name || '');
  // Схемата на самото приложение — не минава през waze.com, който
  // пренасочва към intent:// и чупи инсталираното PWA.
  var app = hasLL ? 'waze://?ll=' + lat + ',' + lng + '&navigate=yes'
                  : 'waze://?q=' + q + '&navigate=yes';
  var web = hasLL ? 'https://waze.com/ul?ll=' + lat + '%2C' + lng + '&navigate=yes'
                  : 'https://waze.com/ul?q=' + q + '&navigate=yes';
  openApp(app, web);
};""",
"""/* FT-WAZE-FIX — виж коментара в patch_waze_fix.py */
window.isStandalonePWA = function(){
  try{
    return (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches)
        || window.navigator.standalone === true
        || document.referrer.indexOf('android-app://') === 0;
  }catch(e){ return false; }
};

window.wazeUrl = function(name, lat, lng){
  var hasLL = isFinite(lat) && isFinite(lng);
  return hasLL
    ? 'https://www.waze.com/ul?ll=' + lat + ',' + lng + '&navigate=yes&zoom=17'
    : 'https://www.waze.com/ul?q=' + encodeURIComponent(name || '') + '&navigate=yes';
};

window.openWaze = function(name, lat, lng){
  var hasLL = isFinite(lat) && isFinite(lng);
  var q   = encodeURIComponent(name || '');
  var web = window.wazeUrl(name, lat, lng);
  if (window.isStandalonePWA()) { openExternal(web); return; }
  var app = hasLL ? 'waze://?ll=' + lat + ',' + lng + '&navigate=yes'
                  : 'waze://?q=' + q + '&navigate=yes';
  openApp(app, web);
};""", 'openWaze: www + сурова запетая + пряк път в standalone')

rep("""window.openGoogleMaps = function(name, lat, lng){
  var hasLL = isFinite(lat) && isFinite(lng);""",
"""window.openGoogleMaps = function(name, lat, lng){
  var hasLL = isFinite(lat) && isFinite(lng);
  if (window.isStandalonePWA()) {
    openExternal(hasLL
      ? 'https://www.google.com/maps/dir/?api=1&destination=' + lat + ',' + lng + '&travelmode=driving'
      : 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(name || ''));
    return;
  }""", 'същият пряк път за Google Maps')

io.open(p, 'w', encoding='utf-8').write(s)
print('OK  %d -> %d chars' % (n0, len(s)))
