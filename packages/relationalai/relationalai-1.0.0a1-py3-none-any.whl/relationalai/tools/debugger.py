# debug_snapshot.py
from __future__ import annotations
import os, json, time, tempfile
from typing import List

def _tail_lines(path: str, max_lines: int) -> List[str]:
    """Tail last N lines efficiently; fine for small/medium files."""
    if not os.path.exists(path): return []
    # simple approach: read and slice; optimize later if needed
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()[-max_lines:]

def write_snapshot(spans_jsonl: str, out_html: str, last: int = 5000):
    lines = _tail_lines(spans_jsonl, last)
    spans = [json.loads(x) for x in lines if x.strip()]
    html = _HTML_TEMPLATE.replace("/*__EMBED__*/", json.dumps(spans, separators=(",", ":")))
    os.makedirs(os.path.dirname(out_html) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(out_html) or ".", prefix=".part-", suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, out_html)

def start_background_snapshots(spans_jsonl: str, out_html: str, interval_ms: int = 1000, last: int = 5000):
    import threading, atexit
    stop = threading.Event()

    def loop():
        next_t = time.monotonic()
        while not stop.is_set():
            try:
                write_snapshot(spans_jsonl, out_html, last=last)
            except Exception:
                pass
            next_t += interval_ms / 1000.0
            delay = max(0.0, next_t - time.monotonic())
            stop.wait(delay)

    th = threading.Thread(target=loop, name="debug-snapshot", daemon=True)
    th.start()
    atexit.register(stop.set)
    return stop

_HTML_TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>Rel Debugger</title>
<meta http-equiv="refresh" content="1">
<style>
  :root { --ok:#22c55e; --err:#ef4444; --run:#a3a3a3; --bg:#0b0c0e; --fg:#e5e7eb; --mut:#9ca3af; }
  html, body { height:100%; background:var(--bg); color:var(--fg); font:14px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto; margin:0; }
  header { padding:10px 14px; border-bottom:1px solid #1f2937; display:flex; gap:12px; align-items:center; }
  .chip { padding:2px 8px; border-radius:999px; background:#111827; color:var(--mut); border:1px solid #1f2937; }
  .wrap { display:grid; grid-template-columns: 380px 1fr; height:calc(100% - 48px); }
  aside { overflow:auto; border-right:1px solid #1f2937; }
  main { overflow:auto; position:relative; }
  ul { list-style:none; margin:0; padding-left:12px; }
  li { padding:4px 8px; border-left:2px solid transparent; }
  li.ok { border-color: var(--ok); }
  li.err { border-color: var(--err); }
  li.run { border-color: var(--run); }
  .name { font-weight:600; }
  .meta { color:var(--mut); font-size:12px; }
  .tl { position:relative; margin:10px; height:24px; background:#111827; border:1px solid #1f2937; border-radius:6px; }
  .bar { position:absolute; top:0; bottom:0; border-radius:6px; }
  .ok .bar { background:linear-gradient(90deg, #14532d, var(--ok)); }
  .err .bar { background:linear-gradient(90deg, #7f1d1d, var(--err)); }
  .run .bar { background:linear-gradient(90deg, #374151, var(--run)); }
  details > summary { cursor:pointer; }
  code { background:#111827; border:1px solid #1f2937; padding:1px 4px; border-radius:4px; }
</style>
<header>
  <div class="chip" id="c-traces">0 traces</div>
  <div class="chip" id="c-spans">0 spans</div>
  <div class="chip" id="c-open">0 running</div>
  <div class="chip" id="c-warn">0 warnings</div>
</header>
<div class="wrap">
  <aside id="tree"></aside>
  <main id="timelines"></main>
</div>

<script>
const STATE_KEY = `rel-debugger:${location.pathname}`;

function loadState(){
  try {
    const raw = localStorage.getItem(STATE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (_) {
    return {};
  }
}

const state = loadState();
if (!state.scroll || typeof state.scroll !== 'object') state.scroll = {};
if (!Array.isArray(state.detailsOpen)) state.detailsOpen = [];
const detailsOpen = new Set(state.detailsOpen);
let saveTimer = null;

function persistState(){
  try { localStorage.setItem(STATE_KEY, JSON.stringify(state)); }
  catch (_) {}
}

function queueSave(){
  if (saveTimer) return;
  saveTimer = setTimeout(() => { saveTimer = null; persistState(); }, 120);
}

function rememberScroll(el, key){
  if (!el) return;
  const saved = state.scroll[key];
  if (saved && typeof saved === 'object') {
    if (Number.isFinite(saved.top)) el.scrollTop = saved.top;
    if (Number.isFinite(saved.left)) el.scrollLeft = saved.left;
  } else if (Number.isFinite(saved)) {
    el.scrollTop = saved;
  }
  el.addEventListener('scroll', () => {
    const next = state.scroll[key];
    if (!next || typeof next !== 'object') {
      state.scroll[key] = {top: el.scrollTop, left: el.scrollLeft};
    } else {
      next.top = el.scrollTop;
      next.left = el.scrollLeft;
    }
    queueSave();
  }, {passive:true});
}

function rememberDetails(spanId, el){
  if (!spanId || !el) return;
  el.dataset.spanId = spanId;
  if (detailsOpen.has(spanId)) el.open = true;
  el.addEventListener('toggle', () => {
    if (el.open) detailsOpen.add(spanId); else detailsOpen.delete(spanId);
    state.detailsOpen = Array.from(detailsOpen);
    queueSave();
  });
}

window.addEventListener('beforeunload', persistState);

const RAW = /*__EMBED__*/;
// Build maps by span_id and group by trace_id, merging span_start + finished span
const spans = new Map();
const traces = new Map();
let warnCount = 0;

for (const rec of RAW) {
  if (rec.type === "span_start") {
    const s = spans.get(rec.span_id) || {};
    spans.set(rec.span_id, Object.assign(s, rec, {events: s.events || []}));
  } else {
    // finished span
    const s = spans.get(rec.span_id) || {};
    const merged = Object.assign(s, rec);
    spans.set(rec.span_id, merged);
    if (merged.events) {
      for (const e of merged.events) {
        if (e.name === "warning") warnCount++;
      }
    }
  }
}

// index by trace, also compute min/max times
for (const s of spans.values()) {
  const tid = s.trace_id;
  if (!traces.has(tid)) traces.set(tid, {spans:[], min:s.start_time_unix_nano||s.start||0, max:s.end_time_unix_nano||s.start_time_unix_nano||0});
  const t = traces.get(tid);
  t.spans.push(s);
  const st = s.start_time_unix_nano || s.start || 0;
  const en = s.end_time_unix_nano || st;
  if (st && st < t.min) t.min = st;
  if (en && en > t.max) t.max = en;
}

document.getElementById('c-traces').textContent = `${traces.size} traces`;
document.getElementById('c-spans').textContent = `${spans.size} spans`;
document.getElementById('c-warn').textContent  = `${warnCount} warnings`;

// Render tree + timelines per trace
const tree = document.getElementById('tree');
const timelines = document.getElementById('timelines');

function nsToMs(ns){ return ns ? (ns/1e6).toFixed(1) : "0.0"; }

for (const [tid, tinfo] of traces.entries()) {
  // build tree: parent -> children
  const kids = new Map();
  const nodes = new Map();
  let roots = [];
  for (const s of tinfo.spans) {
    nodes.set(s.span_id, s);
    if (s.parent_span_id) {
      if (!kids.has(s.parent_span_id)) kids.set(s.parent_span_id, []);
      kids.get(s.parent_span_id).push(s);
    } else {
      roots.push(s);
    }
  }

  // tree panel
  const sec = document.createElement('section');
  const h = document.createElement('h3');
  h.textContent = `trace ${tid.slice(0,8)}…`;
  h.style.padding = "8px 10px"; h.style.margin = "0"; h.style.borderBottom = "1px solid #1f2937";
  sec.appendChild(h);

  const ul = document.createElement('ul'); sec.appendChild(ul);

  function statusClass(s){
    if (!s.end_time_unix_nano) return "run";
    if (s.status === "ERROR") return "err";
    return "ok";
  }

  function liFor(s, depth=0){
    const li = document.createElement('li'); li.className = statusClass(s);
    const nm = document.createElement('div'); nm.className = 'name';
    nm.textContent = s.name || '(unnamed)';
    const meta = document.createElement('div'); meta.className = 'meta';
    const dur = (s.end_time_unix_nano ? (s.end_time_unix_nano - (s.start_time_unix_nano||0))
               : ((Date.now()*1e6) - (s.start_time_unix_nano||0)));
    meta.innerHTML = `span <code>${s.span_id.slice(0,8)}…</code> • ${nsToMs(dur)} ms • ${s.kind||'INTERNAL'}${s.status?(' • '+s.status):''}`;
    li.appendChild(nm); li.appendChild(meta);

    const evc = (s.events||[]).length;
    if (evc) {
      const det = document.createElement('details'); const sum = document.createElement('summary');
      sum.textContent = `${evc} event${evc>1?'s':''}`; det.appendChild(sum);
      const inner = document.createElement('div'); inner.style.padding="4px 8px";
      for (const e of s.events) {
        const line = document.createElement('div');
        line.innerHTML = `<code>${e.name}</code> @ ${nsToMs(e.ts - (s.start_time_unix_nano||0))}ms ${e.attributes?JSON.stringify(e.attributes):''}`;
        inner.appendChild(line);
      }
      det.appendChild(inner); li.appendChild(det);
      rememberDetails(s.span_id, det);
    }

    const ch = kids.get(s.span_id) || [];
    if (ch.length){
      const u = document.createElement('ul');
      for (const c of ch) u.appendChild(liFor(c, depth+1));
      li.appendChild(u);
    }
    return li;
  }

  for (const r of roots) ul.appendChild(liFor(r));

  tree.appendChild(sec);

  // timeline (simple horizontal bars, relative to trace window)
  const tl = document.createElement('section');
  const h2 = document.createElement('h3');
  h2.textContent = `timeline ${tid.slice(0,8)}…`;
  h2.style.padding = "8px 10px"; h2.style.margin = "0"; h2.style.borderBottom = "1px solid #1f2937";
  tl.appendChild(h2);

  const win = (tinfo.max - tinfo.min) || 1;
  for (const s of tinfo.spans) {
    const row = document.createElement('div'); row.className = `tl ${statusClass(s)}`;
    const st = (s.start_time_unix_nano||0) - tinfo.min;
    const en = (s.end_time_unix_nano||Date.now()*1e6) - tinfo.min;
    const left = (100*st/win); const width = Math.max(0.8, 100*(en-st)/win);
    const bar = document.createElement('div'); bar.className = 'bar';
    bar.style.left = left+"%"; bar.style.width = width+"%";
    row.appendChild(bar);
    const meta = document.createElement('div');
    meta.className = 'meta'; meta.style.position='absolute'; meta.style.left='8px'; meta.style.top='2px';
    meta.textContent = `${s.name} (${nsToMs(en-st)} ms)`;
    row.appendChild(meta);
    tl.appendChild(row);
  }

  timelines.appendChild(tl);
}

rememberScroll(tree, 'tree');
rememberScroll(timelines, 'timelines');

// running count
let open = 0;
for (const s of spans.values()) if (!s.end_time_unix_nano) open++;
document.getElementById('c-open').textContent = `${open} running`;
</script>
"""
