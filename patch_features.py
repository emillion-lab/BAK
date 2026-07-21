# -*- coding: utf-8 -*-
"""BAK feature patcher: брояч на излизащи, Acibadem дедуп, басейни, дъжд-аларма.
Пише patch-report.txt ВИНАГИ; пипа app.js/index.html само при пълен успех + валиден JS."""
import re, subprocess, shutil, sys

rep, ok = [], True
src = open('app.js', encoding='utf-8').read()
orig = src

def step(label, fn):
    global src, ok
    try:
        src = fn(src)
        rep.append('OK   ' + label)
    except Exception as e:
        ok = False
        rep.append('FAIL ' + label + ' :: ' + repr(e)[:200])

# 1) Брояч "Сега излизат: N"
def p_counter(s):
    a = "  const shownList = flTerm==='all' ? visible : visible.filter(f=>f.term===flTerm);"
    assert s.count(a) == 1, 'anchor x%d' % s.count(a)
    ins = a + "\n" + (
        "  const nowCnt = shownList.filter(f=>f._state==='now').length;\n"
        "  html+='<div style=\"display:flex;align-items:center;gap:8px;padding:8px 10px;margin-bottom:8px;border-radius:10px;'\n"
        "    +'background:'+(nowCnt?'rgba(239,68,68,.18)':'rgba(255,255,255,.04)')+';'\n"
        "    +'border:1px solid '+(nowCnt?'#ef4444':'var(--border)')+'\">'\n"
        "    +'<span style=\"font-size:20px\">🔴</span>'\n"
        "    +'<span style=\"font-weight:900;font-size:16px;color:'+(nowCnt?'#ef4444':'var(--muted)')+'\">'\n"
        "    +(nowCnt?('Сега излизат: '+nowCnt+' полет'+(nowCnt===1?'':'а')):'Няма излизащи в момента')\n"
        "    +'</span></div>';")
    return s.replace(a, ins)
step('counter', p_counter)

# 2) Дедуп: маха стария 'tokuda' (зона + събитие)
def p_dedupe(s):
    n1 = len(re.findall(r'^\s*\{ id:"tokuda",.*\n', s, re.M))
    n2 = len(re.findall(r'^\s*\{ zone:"tokuda",.*\n', s, re.M))
    assert n1 == 1 and n2 == 1, 'zone x%d event x%d' % (n1, n2)
    s = re.sub(r'^\s*\{ id:"tokuda",.*\n', '', s, flags=re.M)
    s = re.sub(r'^\s*\{ zone:"tokuda",.*\n', '', s, flags=re.M)
    return s
step('dedupe tokuda', p_dedupe)

# 3) Басейни: зони след acibadem_mladost
def p_pools(s):
    m = re.search(r'^\s*\{ id:"acibadem_mladost",.*\},\n', s, re.M)
    assert m, 'mladost line'
    pools = (
        '  { id:"pool_marialuiza", name:"Басейн Мария Луиза (Борисова гр.) ☀лято", icon:"🏊", lat:42.6789, lng:23.3387, radius:220, type:"leisure", wazeName:"Басейн Мария Луиза София" },\n'
        '  { id:"pool_spartak",    name:"Басейн Спартак (Южен парк) ☀лято",        icon:"🏊", lat:42.6752, lng:23.3196, radius:200, type:"leisure", wazeName:"Спортен комплекс Спартак София" },\n'
        '  { id:"pool_diana",      name:"Басейни Диана (Дианабад) ☀лято",          icon:"🏊", lat:42.6586, lng:23.3555, radius:220, type:"leisure", wazeName:"Басейн Диана София" },\n'
        '  { id:"pool_akademika",  name:"Басейн Академика (4-ти км) ☀лято",        icon:"🏊", lat:42.6668, lng:23.3696, radius:200, type:"leisure", wazeName:"Спортен център Академика София" },\n')
    return s[:m.end()] + pools + s[m.end():]
step('pools zones', p_pools)

# 4) Тежести
def p_weights(s):
    a = '  acibadem_tokuda:0.8,'
    assert s.count(a) == 1, 'weights x%d' % s.count(a)
    return s.replace(a, '  pool_marialuiza:0.5, pool_spartak:0.5, pool_diana:0.5, pool_akademika:0.4,\n' + a)
step('pools weights', p_weights)

# 5) Събития — лятно изтичане
def p_events(s):
    m = re.search(r'^\s*\{ zone:"acibadem_tokuda",.*прегледи.*\n', s, re.M)
    assert m, 'events anchor'
    ev = (
        '  { zone:"pool_marialuiza", name:"Басейн Мария Луиза – лятно изтичане", endHour:18.5, boost:1.6, repeat:"daily" },\n'
        '  { zone:"pool_spartak",    name:"Басейн Спартак – лятно изтичане",    endHour:18.5, boost:1.5, repeat:"daily" },\n'
        '  { zone:"pool_diana",      name:"Басейни Диана – лятно изтичане",     endHour:19.0, boost:1.5, repeat:"daily" },\n'
        '  { zone:"pool_akademika",  name:"Басейн Академика – лятно изтичане",  endHour:18.0, boost:1.4, repeat:"daily" },\n')
    return s[:m.start()] + ev + s[m.start():]
step('pools events', p_events)

# 6) Дъжд-аларма — append
def p_rain(s):
    rain = """

// ------ Дъжд-аларма: Open-Meteo 15-мин прогноза ------
(function(){
  async function checkRain(){
    try{
      const r=await fetch('https://api.open-meteo.com/v1/forecast?latitude=42.6977&longitude=23.3219&minutely_15=precipitation&forecast_hours=4&timezone=Europe%2FSofia');
      const d=await r.json();
      const t=(d.minutely_15&&d.minutely_15.time)||[], p=(d.minutely_15&&d.minutely_15.precipitation)||[];
      const now=Date.now();
      let hit=null, stop=null;
      for(let i=0;i<t.length;i++){
        const ts=new Date(t[i]).getTime();
        if(ts<now-15*60000) continue;
        if(p[i]>=0.1 && !hit) hit={ts:ts};
        else if(hit && p[i]<0.1){ stop=ts; break; }
      }
      let el=document.getElementById('rain-banner');
      if(!hit){ if(el) el.remove(); return; }
      const hhmm=function(x){return new Date(x).toLocaleTimeString('bg',{hour:'2-digit',minute:'2-digit'});};
      const started=hit.ts<=now;
      const txt=started
        ? ('🌧️ Вали сега'+(stop?(' до ~'+hhmm(stop)):'')+' — търсенето расте')
        : ('🌧️ Дъжд около '+hhmm(hit.ts)+(stop?(' до '+hhmm(stop)):''));
      if(!el){
        el=document.createElement('div');
        el.id='rain-banner';
        el.style.cssText='position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:9999;background:rgba(30,58,138,.92);color:#dbeafe;font-weight:900;font-size:15px;padding:9px 16px;border-radius:12px;border:1px solid #3b82f6;box-shadow:0 4px 14px rgba(0,0,0,.4);pointer-events:none;white-space:nowrap';
        document.body.appendChild(el);
      }
      el.textContent=txt;
    }catch(e){}
  }
  checkRain();
  setInterval(checkRain, 15*60000);
})();
"""
    return s + rain
step('rain banner', p_rain)

# Валидация и запис
if ok:
    open('/tmp/app.candidate.js', 'w', encoding='utf-8').write(src)
    r = subprocess.run(['node', '--check', '/tmp/app.candidate.js'], capture_output=True, text=True)
    if r.returncode == 0:
        shutil.move('/tmp/app.candidate.js', 'app.js')
        idx = open('index.html', encoding='utf-8').read()
        idx = re.sub(r'app\.js\?v=[0-9a-z]+', 'app.js?v=20260720ui3', idx)
        open('index.html', 'w', encoding='utf-8').write(idx)
        rep.append('OK   node --check + записано, cache-bust ui3')
    else:
        ok = False
        rep.append('FAIL node --check :: ' + (r.stderr or '')[:400])
else:
    rep.append('SKIP запис — има провалени стъпки, app.js НЕ е пипнат')

open('patch-report.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('\n'.join(rep))
sys.exit(0)
