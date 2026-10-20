"""
OS Visualiser · CPU scheduling, live second by second.
Run locally :  streamlit run app.py
"""
import random

import pandas as pd
import streamlit as st

st.set_page_config(page_title="OS Visualiser", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

import engine  # noqa: E402
from live import live_dashboard  # noqa: E402
from ui import hero, inject_css  # noqa: E402

PRIORITY_ALGOS = ("Priority Preemptive", "Priority Non-Preemptive")
S = st.session_state
S.setdefault("page", "home")
S.setdefault("algo", engine.ALGOS[0])
S.setdefault("n", 4)
S.setdefault("quantum", 2)


def goto(page):
    S["page"] = page
    st.rerun()


def random_df(n: int) -> pd.DataFrame:
    prios = random.sample(range(1, n + 1), n)
    return pd.DataFrame({
        "Process": [f"P{i + 1}" for i in range(n)],
        "Task": ["Random task"] * n,
        "Arrival": [random.randint(0, 8) for _ in range(n)],
        "Burst": [random.randint(1, 7) for _ in range(n)],
        "Priority": prios,
    })


def blank_df(n: int) -> pd.DataFrame:
    base = engine.DEFAULT
    rows = []
    for i in range(n):
        if i < len(base):
            r = base.iloc[i].to_dict()
        else:
            r = {"Task": "Custom task", "Arrival": i, "Burst": 3, "Priority": i + 1}
        r["Process"] = f"P{i + 1}"
        rows.append(r)
    return pd.DataFrame(rows)[["Process", "Task", "Arrival", "Burst", "Priority"]]


# ───────────────────────────── page 1 · start card ─────────────────────────────
def home():
    inject_css("card")
    st.markdown('<div class="brand">OS Visualiser<small>Watch CPU scheduling happen, second by second</small></div>',
                unsafe_allow_html=True)
    S["algo"] = st.selectbox("Algorithm:", engine.ALGOS, index=engine.ALGOS.index(S["algo"]))
    S["n"] = int(st.number_input("Process Count:", 1, 10, S["n"]))
    if S["algo"] == "Round Robin":
        S["quantum"] = int(st.number_input("Time Quantum (s):", 1, 20, S["quantum"]))
    st.write("")
    if st.button("Enter Input", key="b_enter"):
        S["df"] = blank_df(S["n"])
        goto("input")
    if st.button("Visualise Random", key="b_rand"):
        S["df"] = random_df(S["n"])
        goto("viz")
    st.markdown("---")
    if st.button("📘 Load Practical Activity 1 (Round Robin, Q = 2)", key="b_act"):
        S.update(algo="Round Robin", n=4, quantum=2, df=blank_df(4))
        goto("viz")


# ───────────────────────────── page 2 · enter input ─────────────────────────────
def input_page():
    inject_css("card")
    st.markdown(f'<div class="brand">Enter Input<small>{S["algo"]} · {S["n"]} processes</small></div>', unsafe_allow_html=True)
    show_pri = S["algo"] in PRIORITY_ALGOS
    cols = ["Process", "Arrival", "Burst"] + (["Priority"] if show_pri else [])
    edited = st.data_editor(
        S["df"][cols], hide_index=True, num_rows="fixed", width="stretch", key="inp",
        column_config={
            "Process": st.column_config.TextColumn("PID", disabled=True),
            "Arrival": st.column_config.NumberColumn("Arrival Time (s)", min_value=0, step=1, format="%d"),
            "Burst": st.column_config.NumberColumn("Burst Time (s)", min_value=1, step=1, format="%d"),
            "Priority": st.column_config.NumberColumn("Priority (1 = highest)", min_value=1, step=1, format="%d"),
        })
    if S["algo"] == "Round Robin":
        S["quantum"] = int(st.number_input("Time Quantum (s):", 1, 20, S["quantum"]))
    c1, c2 = st.columns(2)
    if c1.button("← Back"):
        goto("home")
    if c2.button("Visualise ▶", type="primary"):
        out = S["df"].copy()
        for c in cols:
            out[c] = edited[c]
        err = None
        if out[["Arrival", "Burst"]].isnull().any().any():
            err = "Fill in every Arrival and Burst time."
        elif show_pri and out["Priority"].isnull().any():
            err = "Fill in every Priority."
        if err:
            st.error(err)
        else:
            for c in ("Arrival", "Burst", "Priority"):
                out[c] = out[c].astype(int)
            S["df"] = out
            goto("viz")


# ───────────────────────────── page 3 · live visualiser ─────────────────────────────
def viz():
    inject_css("wide")
    algo, df, q = S["algo"], S["df"], S["quantum"]
    top = st.columns([5, 1.3])
    top[0].markdown(f"### 🧠 OS Visualiser · <span style='color:#22d3ee'>{algo}</span>", unsafe_allow_html=True)
    if top[1].button("↺ Reset and Restart", width="stretch"):
        goto("home")
    res = engine.run_algo(df, algo, q)
    cmap = engine.cmap_for(df.Process.tolist())

    tabs = st.tabs(["▶ Live simulation", "📊 Results & Gantt", "🔄 Round Robin lab", "🏁 Compare algorithms", "📘 Theory"])
    with tabs[0]:
        live_dashboard(df, res, algo, q, algo in PRIORITY_ALGOS)
    with tabs[1]:
        engine.results_tab(res, df, cmap)
    with tabs[2]:
        engine.rr_lab(df, cmap)
    with tabs[3]:
        engine.compare_tab(df, cmap, q)
    with tabs[4]:
        engine.theory_tab()


{"home": home, "input": input_page, "viz": viz}[S["page"]]()
