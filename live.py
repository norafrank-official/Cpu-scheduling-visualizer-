"""Live, second-by-second CPU scheduling dashboard (HTML/JS component)."""
from __future__ import annotations

import json

import pandas as pd
import streamlit.components.v1 as components

from engine import POLICY, Result
from ui import PALETTE

TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');
:root{--card:rgba(9,20,34,.80);--line:rgba(255,255,255,.09);--txt:#e8eef7;--mut:#8fa3bb;--cy:#22d3ee;--run:#facc15;--ready:#60a5fa;--done:#22c55e}
*{box-sizing:border-box}
body{margin:0;padding:2px;font-family:'Space Grotesk','Segoe UI',system-ui,sans-serif;color:var(--txt);background:transparent}
.grid{display:grid;grid-template-columns:minmax(290px,.85fr) 1.7fr;gap:16px;align-items:start}
.col{display:flex;flex-direction:column;gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 24px;backdrop-filter:blur(6px);box-shadow:0 14px 40px rgba(0,0,0,.30)}
.row{display:flex;align-items:baseline;gap:12px;margin:10px 0;flex-wrap:wrap}
.k{font-weight:600;color:#cfdbea;font-size:15px}
.big{font-size:26px;font-weight:700}
.cpu{font-family:'JetBrains Mono',monospace;font-size:30px;font-weight:700;color:#22e55e;text-shadow:0 0 18px rgba(34,229,94,.45);transition:color .2s}
.cpu.idle{color:#94a3b8;text-shadow:none}.cpu.done{color:var(--cy);text-shadow:0 0 18px rgba(34,211,238,.4)}
.timer{font-family:'JetBrains Mono',monospace;font-size:34px;font-weight:700}
.mut{color:var(--mut);font-size:13px}
.avg b{font-family:'JetBrains Mono',monospace;font-size:24px;margin-left:8px}
.mini{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
.pill{padding:6px 12px;border-radius:999px;background:rgba(148,163,184,.12);font-size:12.5px;color:#cbd5e1}
.pill b{color:#fff;font-family:'JetBrains Mono',monospace}
table{width:100%;border-collapse:collapse}
th{font-size:14px;color:#fff;font-weight:700;padding:6px 8px 14px;text-align:center}
td{padding:10px 8px;text-align:center;font-size:15px;border-top:1px solid rgba(255,255,255,.05)}
td.pid{font-weight:700}
.bar{position:relative;height:30px;border-radius:9px;background:rgba(148,163,184,.18);overflow:hidden;min-width:150px}
.fill{position:absolute;left:0;top:0;bottom:0;width:0;border-radius:9px;background:var(--ready);transition:width .35s ease,background .25s}
.fill.run{background:var(--run);box-shadow:0 0 14px rgba(250,204,21,.55)}
.fill.done{background:var(--done)}
.fill.wait{background:rgba(96,165,250,.55)}
.state{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:11.5px;font-weight:700;color:#06101c;letter-spacing:.04em;mix-blend-mode:normal;text-shadow:0 0 3px rgba(255,255,255,.35)}
.state.dim{color:#9fb0c8;text-shadow:none}
tr.runrow{background:rgba(250,204,21,.06)}
.num{font-family:'JetBrains Mono',monospace}
.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:16px}
button,select{font-family:inherit;font-size:14px;font-weight:600;color:#fff;background:#3a4755;border:1px solid rgba(255,255,255,.12);border-radius:10px;padding:9px 16px;cursor:pointer}
button:hover,select:hover{border-color:var(--cy);color:#a5f3fc}
button.play{background:linear-gradient(90deg,#0891b2,#7c3aed);border:none;min-width:104px}
input[type=range]{flex:1;min-width:180px;accent-color:#22d3ee}
.sec{font-weight:700;font-size:15px;margin:0 0 12px;color:#cfdbea}
.gantt{display:flex;overflow-x:auto;padding-bottom:4px}
.cell{flex:1 0 24px;min-width:24px;height:42px;margin:0;display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;color:#06101c;background:rgba(148,163,184,.10);border-top:1px solid rgba(148,163,184,.12);border-bottom:1px solid rgba(148,163,184,.12);transition:background .2s}
.cell.cut{border-left:2px solid #09131f}
.cell.now{outline:2px solid #fff;outline-offset:-2px;z-index:2}
.ticks{display:flex;overflow:visible}
.tick{flex:1 0 24px;min-width:24px;font-size:10.5px;color:var(--mut);text-align:left;padding-top:4px;font-family:'JetBrains Mono',monospace}
.chips{display:flex;gap:8px;flex-wrap:wrap;align-items:center;min-height:34px}
.chip{padding:6px 12px;border-radius:9px;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:13px;color:#06101c}
.arrow{color:#52637d}
.banner{display:none;margin-top:14px;padding:12px 16px;border-radius:12px;background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.45);color:#bbf7d0;font-size:14px;line-height:1.5}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
</style></head><body>
<div class="grid">
  <div class="col">
    <div class="card">
      <div class="row"><span class="k">Algorithm:</span><span class="big" id="algo"></span></div>
      <div class="row"><span class="k">CPU:</span><span class="cpu" id="cpu">—</span><span class="mut" id="next"></span></div>
      <div class="row"><span class="k">Timer:</span><span class="timer" id="timer">0 s</span></div>
      <div class="banner" id="banner"></div>
    </div>
    <div class="card avg">
      <div class="row"><span class="k">Average Waiting Time:</span><b id="awt">—</b></div>
      <div class="row"><span class="k">Average Turn-around Time:</span><b id="atat">—</b></div>
      <div class="mini">
        <span class="pill">Completed <b id="comp">0/0</b></span>
        <span class="pill">Context switches <b id="cs">0</b></span>
        <span class="pill">CPU busy <b id="util">0%</b></span>
      </div>
      <div class="mut" style="margin-top:10px">Averages cover processes completed so far.</div>
    </div>
  </div>
  <div class="card">
    <table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table>
    <div class="controls">
      <button id="bReset" title="Back to 0">⏮</button>
      <button id="bBack" title="Step back 1 s">◀ 1s</button>
      <button id="bPlay" class="play">⏸ Pause</button>
      <button id="bFwd" title="Step forward 1 s">1s ▶</button>
      <select id="speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option><option value="8">8×</option></select>
      <input type="range" id="scrub" min="0" max="1" value="0">
      <span class="mut num" id="tlabel"></span>
    </div>
  </div>
</div>
<div class="card" style="margin-top:16px">
  <div class="sec">Gantt chart · one block per second</div>
  <div class="gantt" id="gantt"></div><div class="ticks" id="ticks"></div>
  <div class="sec" style="margin-top:18px">Ready queue <span class="mut" id="qnote"></span></div>
  <div class="chips" id="queue"></div>
</div>
<script>
const D = __DATA__;
const P = D.procs, N = D.run.length, run = D.run;
const col = {}; P.forEach((p,i)=>col[p.pid]=D.palette[i%D.palette.length]);
const ct = {}; run.forEach((pid,i)=>{ if(pid) ct[pid]=i+1; });
const cuts = new Set(D.cuts);
const showPri = D.showPri;
const $ = id => document.getElementById(id);
let t = 0, playing = false, speed = 1, iv = null;

$('algo').textContent = D.algo + (D.rr ? ' (Q = ' + D.quantum + ' s)' : '');
$('scrub').max = N;

// header + rows
const heads = ['PID','AT','BT'].concat(showPri?['Priority']:[]).concat(['Status Bar','Remaining BT','WT','TAT','CT']);
$('head').innerHTML = heads.map(h=>'<th>'+h+'</th>').join('');
$('body').innerHTML = P.map((p,i)=>
  '<tr id="r'+i+'"><td class="pid" style="color:'+col[p.pid]+'">'+p.pid+'</td><td class="num">'+p.at+' s</td><td class="num">'+p.bt+' s</td>'+
  (showPri?'<td class="num">'+p.pr+'</td>':'')+
  '<td><div class="bar"><div class="fill" id="f'+i+'"></div><div class="state dim" id="s'+i+'"></div></div></td>'+
  '<td class="num" id="rem'+i+'"></td><td class="num" id="wt'+i+'"></td><td class="num" id="tat'+i+'"></td><td class="num" id="ct'+i+'"></td></tr>').join('');

// gantt
let g = '', tk = '';
const step = N<=30 ? 1 : (N<=80 ? 5 : 10);
for(let i=0;i<N;i++){
  const isCut = cuts.has(i);
  g += '<div class="cell'+(isCut?' cut':'')+'" id="c'+i+'"></div>';
  tk += '<div class="tick">'+((i%step===0)?i:'')+'</div>';
}
$('gantt').innerHTML = g; $('ticks').innerHTML = tk;

function execAt(pid,tt){let c=0;for(let i=0;i<tt;i++) if(run[i]===pid) c++;return c;}
const f2 = x => Number.isInteger(x)?String(x):x.toFixed(2);

function render(){
  const ran = t>0 ? run[t-1] : null;
  const cpu = $('cpu');
  if(t===0){cpu.textContent='—';cpu.className='cpu idle';}
  else if(t>=N){cpu.textContent='DONE';cpu.className='cpu done';}
  else if(ran){cpu.textContent=ran;cpu.className='cpu';}
  else {cpu.textContent='IDLE';cpu.className='cpu idle';}
  $('next').textContent = t<N ? ('next second → ' + (run[t]||'idle')) : '';
  $('timer').textContent = t + ' s';

  let sumW=0,sumT=0,nd=0, busy=0;
  const ready=[];
  P.forEach((p,i)=>{
    const ex = execAt(p.pid,t), rem = p.bt-ex, done = ex>=p.bt, arrived = t>=p.at;
    const running = !done && ran===p.pid;
    const f=$('f'+i), s=$('s'+i);
    f.style.width = (ex/p.bt*100)+'%';
    f.className = 'fill' + (done?' done':(running?' run':(arrived && ex>0?' wait':'')));
    if(!arrived){s.textContent='NOT ARRIVED';s.className='state dim';}
    else if(done){s.textContent='DONE';s.className='state';}
    else if(running){s.textContent='RUNNING';s.className='state';}
    else {s.textContent='READY';s.className=(ex>0?'state dim':'state dim');}
    $('r'+i).className = running?'runrow':'';
    $('rem'+i).textContent = rem+' s';
    let wt='-',tat='-',cts='-';
    if(arrived){ wt = done ? (ct[p.pid]-p.at-p.bt) : ((t-p.at)-ex); }
    if(done){ tat = ct[p.pid]-p.at; cts = ct[p.pid]+' s'; sumW += wt; sumT += tat; nd++; }
    $('wt'+i).textContent = wt==='-'?'-':wt+' s';
    $('tat'+i).textContent = tat==='-'?'-':tat+' s';
    $('ct'+i).textContent = cts;
    if(arrived && !done && !running) ready.push({p,ex,rem});
  });
  for(let i=0;i<t;i++) if(run[i]) busy++;
  $('awt').textContent = nd? f2(sumW/nd)+' s' : '—';
  $('atat').textContent = nd? f2(sumT/nd)+' s' : '—';
  $('comp').textContent = nd+'/'+P.length;
  $('util').textContent = t? Math.round(100*busy/t)+'%' : '0%';
  let cs=0,prev=null; for(let i=0;i<t;i++){ if(run[i]){ if(prev && prev!==run[i]) cs++; prev=run[i]; } }
  $('cs').textContent = cs;

  // gantt
  for(let i=0;i<N;i++){
    const c=$('c'+i);
    if(i<t){
      const pid=run[i];
      c.style.background = pid? col[pid] : '#1e293b';
      c.textContent = (cuts.has(i) || i===0 || run[i]!==run[i-1]) ? (pid||'') : '';
    } else { c.style.background=''; c.textContent=''; }
    c.classList.toggle('now', i===t-1);
  }
  // ready queue
  const pol = D.policy;
  const last = pid => { for(let i=t-1;i>=0;i--) if(run[i]===pid) return i+1; return -1; };
  ready.sort((a,b)=>{
    if(pol==='burst') return a.p.bt-b.p.bt || a.p.at-b.p.at;
    if(pol==='remaining') return a.rem-b.rem || a.p.at-b.p.at;
    if(pol==='priority') return a.p.pr-b.p.pr || a.p.at-b.p.at;
    if(pol==='hrrn') return -(((t-b.p.at)+b.p.bt)/b.p.bt) + (((t-a.p.at)+a.p.bt)/a.p.bt) > 0 ? -1 : 1;
    if(pol==='rr'){ const la=last(a.p.pid), lb=last(b.p.pid);
      const ka = la<0? a.p.at : la, kb = lb<0? b.p.at : lb;
      return ka-kb || ((la<0?0:1)-(lb<0?0:1)) || a.p.at-b.p.at; }
    return a.p.at-b.p.at;
  });
  const note = {arrival:'(first come, first served)',burst:'(shortest burst first)',remaining:'(shortest remaining first)',priority:'(highest priority first)',hrrn:'(highest response ratio first)',rr:'(front → back)'}[pol];
  $('qnote').textContent = note;
  $('queue').innerHTML = ready.length ? ready.map(r=>'<span class="chip" style="background:'+col[r.p.pid]+'">'+r.p.pid+' · '+r.rem+'s left</span>').join('<span class="arrow">→</span>') : '<span class="mut">empty</span>';

  $('scrub').value = t; $('tlabel').textContent = t+' / '+N+' s';
  const b=$('banner');
  if(t>=N){
    const util = Math.round(100*busy/N);
    b.style.display='block';
    b.innerHTML = '✅ <b>Simulation complete</b> — all '+P.length+' processes finished at '+N+' s. Avg WT <b>'+f2(sumW/nd)+' s</b>, Avg TAT <b>'+f2(sumT/nd)+' s</b>, '+cs+' context switches.';
  } else b.style.display='none';
}

function setPlay(on){
  playing = on; clearInterval(iv);
  if(on){ if(t>=N) t=0; iv=setInterval(()=>{ if(t<N){t++;render();} if(t>=N) setPlay(false); }, 1000/speed); }
  $('bPlay').textContent = playing ? '⏸ Pause' : '▶ Play';
  render();
}
$('bPlay').onclick = ()=>setPlay(!playing);
$('bReset').onclick = ()=>{ t=0; setPlay(false); };
$('bBack').onclick = ()=>{ setPlay(false); t=Math.max(0,t-1); render(); };
$('bFwd').onclick = ()=>{ setPlay(false); t=Math.min(N,t+1); render(); };
$('speed').onchange = e=>{ speed=parseFloat(e.target.value); if(playing) setPlay(true); };
$('scrub').oninput = e=>{ setPlay(false); t=parseInt(e.target.value); render(); };
render(); setTimeout(()=>setPlay(true), 400);
</script></body></html>"""


def live_dashboard(df: pd.DataFrame, res: Result, algo: str, quantum: int, show_pri: bool):
    run = []
    cuts = []
    for s in res.slices:
        cuts.append(s["start"])
        run += [None if s["pid"] == "Idle" else s["pid"]] * (s["end"] - s["start"])
    procs = [{"pid": r.Process, "at": int(r.Arrival), "bt": int(r.Burst), "pr": int(r.Priority)}
             for r in df.sort_values("Process", key=lambda c: c.str.extract(r"(\d+)")[0].astype(float)).itertuples()]
    data = {"algo": algo, "rr": algo == "Round Robin", "quantum": quantum, "policy": POLICY[algo],
            "procs": procs, "run": run, "cuts": cuts, "palette": PALETTE, "showPri": show_pri}
    html = TEMPLATE.replace("__DATA__", json.dumps(data))
    height = 130 + 58 * len(procs) + 150 + 330
    components.html(html, height=height, scrolling=True)
