"""CPU scheduling: FCFS, SJF, SRTF, Priority (NP/P), HRRN, Round Robin + Round Robin quantum lab."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui import PALETTE, kpi, sect, shade, style_fig

ALGOS = [
    "FCFS",
    "Priority Preemptive",
    "Priority Non-Preemptive",
    "Round Robin",
    "Shortest Job First Preemptive",
    "Shortest Job First Non-Preemptive",
    "Highest Response Ratio Next (HRRN)",
]
POLICY = {  # how the ready queue is ordered in the live view
    "FCFS": "arrival", "Priority Preemptive": "priority", "Priority Non-Preemptive": "priority",
    "Round Robin": "rr", "Shortest Job First Preemptive": "remaining",
    "Shortest Job First Non-Preemptive": "burst", "Highest Response Ratio Next (HRRN)": "hrrn",
}

DEFAULT = pd.DataFrame(
    {
        "Process": ["P1", "P2", "P3", "P4"],
        "Task": ["Water-quality monitoring", "Waste-collection scheduling",
                 "Traffic-pollution analysis", "Public energy-use monitoring"],
        "Arrival": [0, 1, 2, 3],
        "Burst": [5, 3, 4, 2],
        "Priority": [2, 3, 1, 4],
    }
)


@dataclass
class Result:
    algo: str
    quantum: int | None
    slices: list
    table: pd.DataFrame
    avg_tat: float
    avg_wt: float
    avg_rt: float
    avg_ct: float
    switches: int
    end: int
    cpu_util: float


# ───────────────────────────── algorithms ─────────────────────────────
def _finalize(df: pd.DataFrame, slices: list, algo: str, q=None) -> Result:
    first, comp = {}, {}
    for s in slices:
        if s["pid"] == "Idle":
            continue
        first.setdefault(s["pid"], s["start"])
        comp[s["pid"]] = s["end"]
    rows = []
    for r in df.itertuples():
        ct = comp[r.Process]
        tat = ct - r.Arrival
        rows.append({"Process": r.Process, "Task": r.Task, "Arrival": r.Arrival, "Burst": r.Burst,
                     "Priority": r.Priority, "Completion": ct, "Turnaround": tat,
                     "Waiting": tat - r.Burst, "Response": first[r.Process] - r.Arrival})
    t = pd.DataFrame(rows).sort_values("Process").reset_index(drop=True)
    real = [s for s in slices if s["pid"] != "Idle"]
    sw = sum(1 for a, b in zip(real, real[1:]) if a["pid"] != b["pid"])
    end = slices[-1]["end"]
    busy = sum(s["end"] - s["start"] for s in real)
    return Result(algo, q, slices, t, t.Turnaround.mean(), t.Waiting.mean(), t.Response.mean(),
                  t.Completion.mean(), sw, end, 100 * busy / max(1, end))


def _nonpreemptive(df, key):
    procs = df.to_dict("records")
    done, slices, t = set(), [], 0
    while len(done) < len(procs):
        ready = [p for p in procs if p["Process"] not in done and p["Arrival"] <= t]
        if not ready:
            nxt = min(p["Arrival"] for p in procs if p["Process"] not in done)
            slices.append({"pid": "Idle", "start": t, "end": nxt})
            t = nxt
            continue
        p = min(ready, key=lambda x: key(x, t))
        slices.append({"pid": p["Process"], "start": t, "end": t + p["Burst"]})
        t += p["Burst"]
        done.add(p["Process"])
    return slices


def _preemptive(df, key):
    procs = df.to_dict("records")
    rem = {p["Process"]: p["Burst"] for p in procs}
    slices, t, last = [], 0, None
    while any(v > 0 for v in rem.values()):
        ready = [p for p in procs if rem[p["Process"]] > 0 and p["Arrival"] <= t]
        if not ready:
            nxt = min(p["Arrival"] for p in procs if rem[p["Process"]] > 0)
            slices.append({"pid": "Idle", "start": t, "end": nxt})
            t, last = nxt, None
            continue
        p = min(ready, key=lambda x: (key(x, rem), 0 if x["Process"] == last else 1, x["Arrival"]))
        pid = p["Process"]
        if slices and slices[-1]["pid"] == pid and slices[-1]["end"] == t:
            slices[-1]["end"] += 1
        else:
            slices.append({"pid": pid, "start": t, "end": t + 1})
        rem[pid] -= 1
        t += 1
        last = pid
    return slices


def _round_robin(df, q):
    procs = df.sort_values(["Arrival", "Process"], kind="stable").to_dict("records")
    n = len(procs)
    rem = {p["Process"]: p["Burst"] for p in procs}
    queue, slices, idx, t, finished = deque(), [], 0, 0, 0

    def admit(upto):
        nonlocal idx
        while idx < n and procs[idx]["Arrival"] <= upto:
            queue.append(procs[idx]["Process"])
            idx += 1

    admit(t)
    while finished < n:
        if not queue:
            nxt = procs[idx]["Arrival"]
            slices.append({"pid": "Idle", "start": t, "end": nxt})
            t = nxt
            admit(t)
            continue
        pid = queue.popleft()
        run = min(q, rem[pid])
        slices.append({"pid": pid, "start": t, "end": t + run})
        t += run
        rem[pid] -= run
        admit(t)  # new arrivals are queued BEFORE the pre-empted process
        if rem[pid] > 0:
            queue.append(pid)
        else:
            finished += 1
    return slices


def run_algo(df: pd.DataFrame, algo: str, q: int = 2) -> Result:
    df = df.sort_values(["Arrival", "Process"], kind="stable").reset_index(drop=True)
    if algo == "FCFS":
        s = _nonpreemptive(df, lambda p, t: (p["Arrival"], p["Process"]))
    elif algo == "Shortest Job First Non-Preemptive":
        s = _nonpreemptive(df, lambda p, t: (p["Burst"], p["Arrival"], p["Process"]))
    elif algo == "Priority Non-Preemptive":
        s = _nonpreemptive(df, lambda p, t: (p["Priority"], p["Arrival"], p["Process"]))
    elif algo == "Highest Response Ratio Next (HRRN)":
        s = _nonpreemptive(df, lambda p, t: (-((t - p["Arrival"]) + p["Burst"]) / p["Burst"], p["Arrival"]))
    elif algo == "Shortest Job First Preemptive":
        s = _preemptive(df, lambda p, rem: rem[p["Process"]])
    elif algo == "Priority Preemptive":
        s = _preemptive(df, lambda p, rem: p["Priority"])
    else:
        s = _round_robin(df, q)
    return _finalize(df, s, algo, q if algo == "Round Robin" else None)


# ───────────────────────────── visuals ─────────────────────────────
def cmap_for(pids):
    return {p: PALETTE[i % len(PALETTE)] for i, p in enumerate(sorted(pids))}


def gantt(res: Result, cmap, upto=None, height=240):
    fig = go.Figure()
    shown = set()
    for s in res.slices:
        end = s["end"] if upto is None else min(s["end"], upto)
        if end <= s["start"]:
            continue
        idle = s["pid"] == "Idle"
        fig.add_trace(go.Bar(
            x=[end - s["start"]], base=[s["start"]], y=["CPU"], orientation="h", name=s["pid"],
            legendgroup=s["pid"], showlegend=(s["pid"] not in shown and not idle),
            marker=dict(color="#1e293b" if idle else cmap[s["pid"]], line=dict(color="#070b14", width=2.5)),
            text=f"<b>{'idle' if idle else s['pid']}</b>", textposition="inside", insidetextanchor="middle",
            textfont=dict(color="#94a3b8" if idle else "#06101c", size=14, family="JetBrains Mono"),
            hovertemplate=f"<b>{s['pid']}</b><br>{s['start']} → {s['end']} ms<extra></extra>"))
        shown.add(s["pid"])
    ticks = sorted({s["start"] for s in res.slices} | {res.end})
    style_fig(fig, height)
    fig.update_layout(barmode="overlay", bargap=0.25, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(title="Time (ms)", tickmode="array", tickvals=ticks, range=[0, res.end + 0.3]),
                      yaxis=dict(showticklabels=False, fixedrange=True))
    if upto is not None:
        fig.add_vline(x=upto, line=dict(color="#f472b6", width=2, dash="dot"))
    return fig


def styled(df):
    return (df.style.apply(shade("34,211,238"), subset=["Waiting"])
            .apply(shade("167,139,250"), subset=["Turnaround"]))


def validate(df):
    if df.empty:
        return "Add at least one process."
    if df[["Process", "Arrival", "Burst", "Priority"]].isnull().any().any():
        return "Process, Arrival, Burst and Priority cannot be empty."
    if df["Process"].duplicated().any():
        return "Process IDs must be unique."
    if (df["Burst"] <= 0).any():
        return "Burst time must be at least 1 ms."
    if (df["Arrival"] < 0).any():
        return "Arrival time cannot be negative."
    return None


def replay(res: Result, df: pd.DataFrame, cmap, key):
    t = st.slider("Scrub through time (ms)", 0.0, float(res.end), float(res.end), 1.0, key=f"t_{key}")
    st.plotly_chart(gantt(res, cmap, upto=t, height=200), width="stretch", key=f"gr_{key}")
    rem = dict(zip(df.Process, df.Burst))
    arr = dict(zip(df.Process, df.Arrival))
    last = {p: (arr[p], 0) for p in rem}
    running = None
    for s in res.slices:
        if s["pid"] == "Idle" or s["start"] >= t:
            continue
        rem[s["pid"]] -= min(s["end"], t) - s["start"]
        if s["end"] <= t:
            last[s["pid"]] = (s["end"], 1)
        if s["start"] <= t < s["end"]:
            running = s["pid"]
    ready = sorted([p for p in rem if rem[p] > 0 and p != running and arr[p] <= t], key=lambda p: last[p])
    done = [p for p in rem if rem[p] <= 0]
    a, b, c = st.columns([1, 3, 1.4])
    a.markdown("**CPU now**")
    a.markdown(f'<div class="running">{running or "idle / finished"}</div>', unsafe_allow_html=True)
    b.markdown("**Ready queue** (front → back)")
    b.markdown('<div class="qbox">' + ('<span class="qarrow">→</span>'.join(
        f'<span class="qitem" style="background:{cmap[p]}">{p} · {rem[p]}ms left</span>' for p in ready)
        or '<span style="color:#64748b">empty</span>') + "</div>", unsafe_allow_html=True)
    c.markdown("**Completed**")
    c.markdown(", ".join(done) if done else "—")


def kpis(res: Result):
    c = st.columns(5)
    c[0].markdown(kpi("Avg turnaround", f"{res.avg_tat:.2f}", "ms", True), unsafe_allow_html=True)
    c[1].markdown(kpi("Avg waiting", f"{res.avg_wt:.2f}", "ms", True), unsafe_allow_html=True)
    c[2].markdown(kpi("Avg response", f"{res.avg_rt:.2f}", "ms"), unsafe_allow_html=True)
    c[3].markdown(kpi("Context switches", res.switches, "CPU hand-overs", True), unsafe_allow_html=True)
    c[4].markdown(kpi("Total time", res.end, f"ms · util {res.cpu_util:.0f}%"), unsafe_allow_html=True)


# ───────────────────────────── tabs ─────────────────────────────
def results_tab(res: Result, df, cmap):
    kpis(res)
    sect("Gantt chart · execution sequence")
    st.plotly_chart(gantt(res, cmap), width="stretch", key="res_g")
    st.code(" → ".join(f"{s['pid']}({s['start']}-{s['end']})" for s in res.slices if s["pid"] != "Idle"), language=None)
    sect("Per-process results")
    cols = ["Process", "Task", "Arrival", "Burst", "Priority", "Completion", "Turnaround", "Waiting", "Response"]
    st.dataframe(styled(res.table[cols]), width="stretch", hide_index=True)
    st.download_button("⬇ Download results (CSV)", res.table.to_csv(index=False).encode(), "cpu_results.csv", "text/csv")
    sect("Time-travel replay")
    replay(res, df, cmap, "res")


def compare_tab(df, cmap, q):
    qc = st.number_input("Quantum used for Round Robin (ms)", 1, 20, int(q), key="cmp_q")
    results = [run_algo(df, a, int(qc)) for a in ALGOS]
    cmp_df = pd.DataFrame([{"Algorithm": r.algo, "Avg turnaround": r.avg_tat, "Avg waiting": r.avg_wt,
                            "Avg response": r.avg_rt, "Context switches": r.switches, "Total time": r.end} for r in results])
    best = cmp_df.loc[cmp_df["Avg waiting"].idxmin(), "Algorithm"]
    st.markdown(f'<div class="verdict"><h3>⏱ Lowest average waiting time: {best}</h3>'
                "<p>Shortest-job-first is provably optimal for average waiting, but it can starve long jobs "
                "and needs burst-time knowledge in advance.</p></div>", unsafe_allow_html=True)
    st.write("")
    st.dataframe(cmp_df.style.format({c: "{:.2f}" for c in cmp_df.columns[1:4]})
                 .highlight_min(subset=["Avg turnaround", "Avg waiting", "Avg response", "Context switches"],
                                color="rgba(52,211,153,.30)"), width="stretch", hide_index=True)
    fig = go.Figure()
    for col, color in (("Avg turnaround", "#22d3ee"), ("Avg waiting", "#a78bfa"), ("Avg response", "#fbbf24")):
        fig.add_bar(name=col, x=cmp_df.Algorithm, y=cmp_df[col], marker_color=color)
    style_fig(fig, 380, "Average times (ms) · lower is better").update_layout(barmode="group")
    st.plotly_chart(fig, width="stretch", key="cmp_bar")
    sect("Gantt charts side by side")
    for i, r in enumerate(results):
        st.markdown(f"**{r.algo}**" + (f" · Q = {qc} ms" if r.quantum else ""))
        st.plotly_chart(gantt(r, cmap, height=150), width="stretch", key=f"cmp_g{i}")


def theory_tab():
    st.markdown("""
| Metric | Formula |
|---|---|
| Turnaround time (TAT) | `Completion − Arrival` |
| Waiting time (WT) | `Turnaround − Burst` |
| Response time (RT) | `First CPU start − Arrival` |

| Algorithm | Idea | Pros | Cons |
|---|---|---|---|
| **FCFS** | Run in arrival order | Simple, no starvation | Convoy effect |
| **SJF (non-preemptive)** | Shortest burst next | Optimal average waiting among non-preemptive | Starvation, needs burst estimate |
| **SJF (preemptive / SRTF)** | Shortest *remaining* time always runs | Best for short jobs | More switches, starvation |
| **Priority (NP / P)** | Lowest number = highest priority | Models urgency | Starvation (fix: aging) |
| **Round Robin** | Fixed time quantum, circular queue | Fair, good response | Switch overhead if Q too small |
| **HRRN** | Highest `(wait + burst) / burst` | Balances short and long jobs | Needs burst estimate |

**Conventions:** context-switch overhead = 0; a process arriving at the instant another is pre-empted is queued first;
the first dispatch and a process continuing on its own are not counted as context switches; lower priority number = higher priority.
""")


# ───────────────────────────── RR lab (Practical Activity 1) ─────────────────────────────
def rr_lab(df, cmap):
    st.markdown(
        '<div class="verdict" style="background:rgba(34,211,238,.07);border-color:rgba(34,211,238,.35)">'
        "<h3 style='color:#67e8f9'>Practical Activity 1 · Round Robin without context-switch overhead</h3>"
        "<p>Municipal control centre services (SDG 6, 11, 12). Compare two time quanta and pick the better balance of "
        "fair CPU access, waiting time and context switching.</p></div>", unsafe_allow_html=True)
    c = st.columns(5)
    qa = c[0].number_input("Quantum A (ms)", 1, 20, 2, key="qa")
    qb = c[1].number_input("Quantum B (ms)", 1, 20, 3, key="qb")
    w_wait = c[2].slider("Weight: waiting", 0, 10, 5, key="ww")
    w_fair = c[3].slider("Weight: fair access", 0, 10, 4, key="wf")
    w_cs = c[4].slider("Weight: switches", 0, 10, 3, key="wc")
    A, B = run_algo(df, "Round Robin", int(qa)), run_algo(df, "Round Robin", int(qb))

    sect(f"Gantt · Q = {qa} ms vs Q = {qb} ms")
    for i, r in enumerate((A, B)):
        st.markdown(f"**Time quantum = {r.quantum} ms**")
        st.plotly_chart(gantt(r, cmap, height=190), width="stretch", key=f"lab_g{i}")

    sect("Tool-generated comparison")

    def delta(a, b, lower=True):
        d = b - a
        if abs(d) < 1e-9:
            return "—"
        return f"{'▲' if d > 0 else '▼'} {abs(d):.2f} {'✅' if (d < 0) == lower else '⚠️'}"

    comp = pd.DataFrame({
        "Metric": ["Average turnaround (ms)", "Average waiting (ms)", "Average response (ms)",
                   "Average completion (ms)", "Context switches", "Schedule length (ms)", "CPU utilisation (%)"],
        f"Q = {A.quantum}": [A.avg_tat, A.avg_wt, A.avg_rt, A.avg_ct, A.switches, A.end, A.cpu_util],
        f"Q = {B.quantum}": [B.avg_tat, B.avg_wt, B.avg_rt, B.avg_ct, B.switches, B.end, B.cpu_util],
    })
    comp["Change (B vs A)"] = [delta(A.avg_tat, B.avg_tat), delta(A.avg_wt, B.avg_wt), delta(A.avg_rt, B.avg_rt),
                               delta(A.avg_ct, B.avg_ct), delta(A.switches, B.switches), delta(A.end, B.end),
                               delta(A.cpu_util, B.cpu_util, False)]
    st.dataframe(comp.style.format({comp.columns[1]: "{:.2f}", comp.columns[2]: "{:.2f}"}),
                 width="stretch", hide_index=True)
    st.download_button("⬇ Download comparison (CSV)", comp.to_csv(index=False).encode(), "rr_comparison.csv", "text/csv")

    g1, g2 = st.columns(2)
    f1 = go.Figure()
    for r, col in ((A, "#22d3ee"), (B, "#a78bfa")):
        f1.add_bar(name=f"Q = {r.quantum}", x=["Avg turnaround", "Avg waiting", "Avg response"],
                   y=[r.avg_tat, r.avg_wt, r.avg_rt], marker_color=col,
                   text=[f"{v:.2f}" for v in (r.avg_tat, r.avg_wt, r.avg_rt)], textposition="outside")
    style_fig(f1, 330, "Average times (ms) · lower is better").update_layout(barmode="group")
    g1.plotly_chart(f1, width="stretch", key="lab_f1")
    f2 = go.Figure()
    for r, col in ((A, "#22d3ee"), (B, "#a78bfa")):
        f2.add_bar(name=f"Q = {r.quantum}", x=r.table.Process, y=r.table.Waiting, marker_color=col)
    style_fig(f2, 330, "Waiting time per process (ms)").update_layout(barmode="group")
    g2.plotly_chart(f2, width="stretch", key="lab_f2")

    d1, d2 = st.columns(2)
    d1.caption(f"Q = {A.quantum} ms")
    d1.dataframe(styled(A.table.drop(columns=["Priority"])), width="stretch", hide_index=True)
    d2.caption(f"Q = {B.quantum} ms")
    d2.dataframe(styled(B.table.drop(columns=["Priority"])), width="stretch", hide_index=True)

    # decision
    sect("Decision · which quantum balances fairness, waiting and switching?")

    def norm(a, b):
        lo, hi = min(a, b), max(a, b)
        return (0.5, 0.5) if hi == lo else ((hi - a) / (hi - lo), (hi - b) / (hi - lo))

    wa, wb = norm(A.avg_wt, B.avg_wt)
    ra, rb = norm(A.avg_rt, B.avg_rt)
    ca, cb = norm(A.switches, B.switches)
    tw = max(1, w_wait + w_fair + w_cs)
    sa = 100 * (w_wait * wa + w_fair * ra + w_cs * ca) / tw
    sb = 100 * (w_wait * wb + w_fair * rb + w_cs * cb) / tw
    best, other = (A, B) if sa >= sb else (B, A)
    head = "Both quanta score equally under these weights" if abs(sa - sb) < 1e-9 else f"Recommended time quantum: {best.quantum} ms"
    reasons = []
    for label, a, b, unit in (("average waiting time", best.avg_wt, other.avg_wt, "ms"),
                              ("average response time (fair CPU access)", best.avg_rt, other.avg_rt, "ms"),
                              ("context switches", best.switches, other.switches, "")):
        if abs(a - b) < 1e-9:
            reasons.append(f"{label.capitalize()} is the same for both ({a:.2f}{unit}).")
        elif a < b:
            reasons.append(f"Q = {best.quantum} ms gives lower {label}: **{a:.2f}{unit}** vs {b:.2f}{unit}.")
        else:
            reasons.append(f"Q = {best.quantum} ms has higher {label} (**{a:.2f}{unit}** vs {b:.2f}{unit}) — a trade-off accepted for the other gains.")
    st.markdown(f'<div class="verdict"><h3>🏆 {head}</h3>' + "".join(f"<p>• {r}</p>" for r in reasons) +
                "<p style='margin-top:10px'>Short response times keep urgent monitoring (e.g. water-quality alerts) responsive, "
                "while fewer context switches reduce scheduling churn. Change the weights above to see how priorities shift the verdict.</p></div>",
                unsafe_allow_html=True)
    st.write("")
    r1, r2 = st.columns([1.1, 1])
    radar = go.Figure()
    cats = ["Waiting", "Fair access (response)", "Few switches", "Waiting"]
    for r, (w_, r_, c_), col in ((A, (wa, ra, ca), "#22d3ee"), (B, (wb, rb, cb), "#a78bfa")):
        radar.add_trace(go.Scatterpolar(r=[w_, r_, c_, w_], theta=cats, fill="toself", name=f"Q = {r.quantum}",
                                        line=dict(color=col, width=3), opacity=0.75))
    style_fig(radar, 370, "Balance profile (outer = better)").update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(range=[0, 1], showticklabels=False, gridcolor="rgba(148,163,184,.2)"),
                   angularaxis=dict(gridcolor="rgba(148,163,184,.2)")), margin=dict(t=60, b=20))
    r1.plotly_chart(radar, width="stretch", key="lab_radar")
    with r2:
        st.markdown("**Weighted balance score** (0–100)")
        st.markdown(kpi(f"Q = {A.quantum} ms", f"{sa:.0f}", "higher is better", sa >= sb), unsafe_allow_html=True)
        st.write("")
        st.markdown(kpi(f"Q = {B.quantum} ms", f"{sb:.0f}", "higher is better", sb > sa), unsafe_allow_html=True)
        st.caption("Metrics are min-max normalised between the two runs, then combined with your weights.")

    sect("Sweep every quantum (1 → max burst)")
    sweep = [run_algo(df, "Round Robin", k) for k in range(1, int(df.Burst.max()) + 1)]
    sf = go.Figure()
    xs = [r.quantum for r in sweep]
    sf.add_scatter(x=xs, y=[r.avg_wt for r in sweep], name="Avg waiting", mode="lines+markers", line=dict(color="#22d3ee", width=3))
    sf.add_scatter(x=xs, y=[r.avg_rt for r in sweep], name="Avg response", mode="lines+markers", line=dict(color="#fbbf24", width=3))
    sf.add_scatter(x=xs, y=[r.switches for r in sweep], name="Context switches", mode="lines+markers",
                   line=dict(color="#f472b6", width=3), yaxis="y2")
    style_fig(sf, 340).update_layout(xaxis=dict(title="Time quantum (ms)", dtick=1), yaxis=dict(title="ms"),
                                     yaxis2=dict(title="switches", overlaying="y", side="right", showgrid=False))
    st.plotly_chart(sf, width="stretch", key="lab_sweep")
    st.caption("Small quanta → fast response but many switches. Large quanta → few switches, Round Robin drifts toward FCFS.")

