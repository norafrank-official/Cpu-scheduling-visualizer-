"""Shared theme + small UI helpers for the OS Algorithm Lab."""
import plotly.graph_objects as go
import streamlit as st

PALETTE = ["#22d3ee", "#a78bfa", "#fbbf24", "#34d399", "#f472b6", "#fb923c", "#60a5fa", "#f87171",
           "#2dd4bf", "#c084fc"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Space Grotesk', sans-serif; }
.stApp {
  background:
    radial-gradient(900px 500px at 8% -10%, rgba(34,211,238,.13), transparent 60%),
    radial-gradient(800px 500px at 100% 0%, rgba(167,139,250,.14), transparent 60%), #070b14;
  color: #e6edf7;
}
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: #0a1020; border-right: 1px solid rgba(148,163,184,.12); }
.block-container { padding-top: 1.6rem; max-width: 1280px; }
.hero { position: relative; overflow: hidden; padding: 26px 32px; border-radius: 22px; margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(34,211,238,.10), rgba(167,139,250,.10));
  border: 1px solid rgba(148,163,184,.18); }
.hero:after { content:""; position:absolute; right:-60px; top:-60px; width:260px; height:260px; border-radius:50%;
  background: conic-gradient(from 0deg,#22d3ee,#a78bfa,#f472b6,#fbbf24,#22d3ee); filter: blur(70px); opacity:.28; }
.hero .eyebrow { font-family:'JetBrains Mono',monospace; font-size:12px; letter-spacing:.18em; color:#22d3ee; text-transform:uppercase; }
.hero h1 { font-size: 2.1rem; font-weight:700; margin:6px 0 6px;
  background: linear-gradient(90deg,#fff,#a5f3fc 55%,#c4b5fd); -webkit-background-clip:text; color:transparent; }
.hero p { color:#9fb0c8; margin:0; max-width: 820px; line-height:1.55; }
.chip { display:inline-block; padding:3px 11px; border-radius:999px; font-size:12px; font-weight:600; margin-right:6px; margin-top:12px; color:#06101c; }
.kpi { padding:15px 18px; border-radius:16px; background:rgba(15,23,42,.7); border:1px solid rgba(148,163,184,.16); height:100%; }
.kpi .l { font-size:11.5px; color:#8ea0ba; text-transform:uppercase; letter-spacing:.12em; }
.kpi .v { font-family:'JetBrains Mono',monospace; font-size:1.8rem; font-weight:600; margin-top:4px; }
.kpi .s { font-size:12px; color:#6f819b; margin-top:2px; }
.kpi.accent { border-color: rgba(34,211,238,.45); box-shadow: 0 0 0 1px rgba(34,211,238,.15) inset; }
.sect { font-size:1.15rem; font-weight:600; margin:24px 0 10px; display:flex; align-items:center; gap:10px; }
.sect:before { content:""; width:4px; height:20px; border-radius:2px; background:linear-gradient(#22d3ee,#a78bfa); }
.verdict { padding:22px 26px; border-radius:18px; background:linear-gradient(135deg, rgba(52,211,153,.12), rgba(34,211,238,.08));
  border:1px solid rgba(52,211,153,.4); }
.verdict h3 { margin:0 0 6px; font-size:1.3rem; color:#6ee7b7; }
.verdict p { margin:4px 0; color:#cbd5e1; line-height:1.6; }
.bad { padding:18px 24px; border-radius:18px; background:rgba(248,113,113,.10); border:1px solid rgba(248,113,113,.45); }
.bad h3 { margin:0 0 6px; color:#fca5a5; }
.qbox { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.qitem { padding:6px 14px; border-radius:10px; font-family:'JetBrains Mono',monospace; font-weight:600; color:#06101c; font-size:14px; }
.qarrow { color:#52637d; }
.running { border:1px dashed #22d3ee; background:rgba(34,211,238,.08); color:#a5f3fc; padding:6px 14px; border-radius:10px;
  font-family:'JetBrains Mono',monospace; font-weight:600; display:inline-block; }
/* page-replacement grid */
.pgrid { overflow-x:auto; padding-bottom:6px; }
.pgrid table { border-collapse:separate; border-spacing:5px; font-family:'JetBrains Mono',monospace; }
.pgrid td, .pgrid th { min-width:38px; height:38px; text-align:center; border-radius:9px; font-size:14px; font-weight:600; }
.pgrid th { color:#8ea0ba; background:transparent; font-weight:500; }
.pgrid td.ref { background:#1e293b; color:#e2e8f0; }
.pgrid td.frame { background:rgba(148,163,184,.10); color:#cbd5e1; }
.pgrid td.new { background:#f87171; color:#2b0a0a; }
.pgrid td.hitc { background:rgba(52,211,153,.30); color:#a7f3d0; }
.pgrid td.res { font-size:12px; }
.pgrid td.F { background:rgba(248,113,113,.25); color:#fecaca; }
.pgrid td.H { background:rgba(52,211,153,.25); color:#a7f3d0; }
.pgrid td.lbl { background:transparent; color:#8ea0ba; font-weight:500; min-width:70px; text-align:right; padding-right:6px; }
div[data-testid="stTabs"] button { font-weight:600; }
div[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }
</style>
"""


def _bg_url() -> str:
    from urllib.parse import quote
    svg = """<svg xmlns='http://www.w3.org/2000/svg' width='1920' height='1080' viewBox='0 0 1920 1080' preserveAspectRatio='xMidYMid slice'>
<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#09131f'/><stop offset='1' stop-color='#0e2740'/></linearGradient>
<pattern id='d' width='14' height='14' patternUnits='userSpaceOnUse'><circle cx='2' cy='2' r='1.5' fill='#9fb6d0' fill-opacity='.30'/></pattern></defs>
<rect width='1920' height='1080' fill='url(#g)'/>
<circle cx='400' cy='140' r='125' fill='#14395b' fill-opacity='.85'/>
<rect x='30' y='60' width='300' height='210' fill='url(#d)'/>
<rect x='1560' y='640' width='260' height='230' fill='url(#d)'/>
<rect x='60' y='560' width='200' height='260' fill='url(#d)'/>
<path d='M380 150 q25 -62 50 0 t50 0 t50 0 t50 0' stroke='#cfe0f2' stroke-opacity='.30' fill='none' stroke-width='2.5'/>
<path d='M1560 110 l35 -45 l35 45 l35 -45 l35 45 l35 -45 l35 45' stroke='#ffffff' stroke-opacity='.8' fill='none' stroke-width='3'/>
<path d='M1730 590 q22 -55 44 0 t44 0 t44 0' stroke='#cfe0f2' stroke-opacity='.30' fill='none' stroke-width='2.5'/>
<circle cx='260' cy='960' r='420' fill='#11304f' fill-opacity='.55'/>
<circle cx='1620' cy='1000' r='190' fill='#16406a' fill-opacity='.55'/>
<path d='M800 0 A700 700 0 0 1 1500 700 L1920 700 L1920 0 Z' fill='#0c2038' fill-opacity='.55'/>
<polygon points='1150,150 1500,235 1380,560 1000,420' fill='#27506f' fill-opacity='.35'/>
<polygon points='1500,235 1620,210 1500,540 1380,560' fill='#1b3a56' fill-opacity='.45'/>
<polygon points='390,450 640,350 750,610 490,710' fill='#27506f' fill-opacity='.30'/>
<polygon points='330,520 390,450 490,710 430,790' fill='#17344f' fill-opacity='.45'/>
<g stroke='#e2edf8' stroke-opacity='.55' stroke-width='1.8' fill='none'>
<polygon points='1090,215 1165,190 1355,280 1245,300'/><polyline points='1165,190 1245,300 1215,400 1060,305 1090,215'/><line x1='1090' y1='215' x2='1245' y2='300'/><line x1='1355' y1='280' x2='1215' y2='400'/>
<polygon points='525,385 640,335 672,475 562,588'/><polyline points='525,385 585,465 672,475'/><line x1='640' y1='335' x2='585' y2='465'/><line x1='585' y1='465' x2='562' y2='588'/><line x1='525' y1='385' x2='562' y2='588'/>
<polygon points='1675,740 1800,810 1700,830 1605,840'/><polyline points='1675,740 1700,830 1745,960'/><line x1='1700' y1='830' x2='1800' y2='810'/><line x1='1605' y1='840' x2='1745' y2='960'/><line x1='1800' y1='810' x2='1745' y2='960'/>
</g>
<polygon points='1035,760 1130,735 1165,830 1060,880' fill='#27506f' fill-opacity='.45'/>
</svg>"""
    return "data:image/svg+xml;utf8," + quote(svg)


CARD_CSS = """
<style>
.block-container { max-width: 560px !important; margin-top: 7vh; padding: 2.3rem 2.7rem 2.2rem !important;
  background: rgba(10,22,38,.84); border: 1px solid rgba(255,255,255,.08); border-radius: 22px;
  box-shadow: 0 30px 80px rgba(0,0,0,.5), 0 0 0 1px rgba(34,211,238,.07) inset; backdrop-filter: blur(6px); }
.block-container .stButton > button { width:100%; height:46px; border-radius:10px; font-weight:600;
  background:#3a4755; color:#fff; border:1px solid rgba(255,255,255,.10); }
.block-container .stButton > button:hover { border-color:#22d3ee; color:#a5f3fc; background:#42505f; }
.block-container .stButton > button[kind="primary"] { background:linear-gradient(90deg,#0891b2,#7c3aed); border:none; }
.brand { font-size:2.3rem; font-weight:700; margin:0 0 14px; color:#fff; letter-spacing:-.02em; }
.brand small { display:block; font-size:.9rem; font-weight:500; color:#8fa3bb; letter-spacing:0; margin-top:2px; }
label p { font-weight:600 !important; color:#e8eef7 !important; }
</style>
"""


def inject_css(mode: str = "wide"):
    """mode='card' → centred glass card (start / input pages); 'wide' → full dashboard."""
    st.markdown(CSS.replace("</style>", "").replace("<style>", "<style>") + "</style>", unsafe_allow_html=True)
    st.markdown(f'<style>.stApp {{ background: url("{_bg_url()}") center/cover fixed no-repeat, #09131f !important; }}</style>',
                unsafe_allow_html=True)
    if mode == "card":
        st.markdown(CARD_CSS, unsafe_allow_html=True)


def hero(eyebrow: str, title: str, text: str, chips=()):
    ch = "".join(f'<span class="chip" style="background:{c}">{t}</span>' for t, c in chips)
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{text}</p>{ch}</div>',
        unsafe_allow_html=True,
    )


def sect(text: str):
    st.markdown(f'<div class="sect">{text}</div>', unsafe_allow_html=True)


def kpi(label, value, sub="", accent=False):
    cls = "kpi accent" if accent else "kpi"
    return f'<div class="{cls}"><div class="l">{label}</div><div class="v">{value}</div><div class="s">{sub}</div></div>'


def style_fig(fig: go.Figure, height=340, title=None) -> go.Figure:
    fig.update_layout(
        height=height,
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1", family="Space Grotesk"),
        margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        legend=dict(orientation="h", y=1.15, x=0),
    )
    fig.update_xaxes(gridcolor="rgba(148,163,184,.12)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,.12)", zeroline=False)
    return fig


def shade(rgb):
    """Column styler shading cells by value (no matplotlib needed)."""
    def f(col):
        hi = max(col.max(), 1)
        return [f"background-color: rgba({rgb},{0.10 + 0.50 * v / hi:.2f}); color: #f1f5f9" for v in col]
    return f


def parse_ints(text: str, sep_hint="space or comma separated"):
    """Parse '7 0 1, 2' → [7,0,1,2]; raises ValueError with friendly message."""
    try:
        return [int(x) for x in text.replace(",", " ").split()]
    except ValueError:
        raise ValueError(f"Please enter whole numbers ({sep_hint}).")
