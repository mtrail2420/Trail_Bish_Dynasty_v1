import streamlit as st

from core.data_loader import load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import compute_league_stats, compute_owner_stats, score_leader, compute_class_stats, POSITION_GROUPS
from core.utils import fmt_score
from core.components import (
    page_header,
    section_header,
    stat_card,
    rivalry_banner,
    player_row,
    player_table,
    callout,
)

st.set_page_config(
    page_title="Trail & Bish Boys Dynasty",
    page_icon="🏈",
    layout="wide",
)

render_sidebar(active="Dashboard")

# ── Guard ─────────────────────────────────────────────────────────────────────

if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────

df      = load_players()
matt_df = df[df["OWNER"] == "Matt"]
ryan_df = df[df["OWNER"] == "Ryan"]

ls          = compute_league_stats(df)
matt_stats  = compute_owner_stats(df, "Matt")
ryan_stats  = compute_owner_stats(df, "Ryan")
leader, delta = score_leader(matt_stats, ryan_stats)

top3 = (
    df.dropna(subset=["OVERALL SCORE"])
    .sort_values("OVERALL SCORE", ascending=False)
    .head(3)
    .reset_index(drop=True)
)

value_picks = (
    df[df["ROUND"] >= 3]
    .dropna(subset=["OVERALL SCORE"])
    .sort_values("OVERALL SCORE", ascending=False)
    .head(3)
    .reset_index(drop=True)
)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown(
    page_header(
        "🏈 Trail &amp; Bish Boys Dynasty",
        "Every Pick · Every Play · Every Legacy",
    ),
    unsafe_allow_html=True,
)

# ── Rivalry Banner ────────────────────────────────────────────────────────────

st.markdown(rivalry_banner(matt_df, ryan_df), unsafe_allow_html=True)

# ── League Snapshot ───────────────────────────────────────────────────────────

st.markdown(
    section_header("LEAGUE SNAPSHOT", f"{ls['draft_classes']} seasons · {ls['year_range']}"),
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        stat_card("TOTAL PLAYERS", str(ls["total_players"]), f"{len(POSITION_GROUPS)} position groups", "blue"),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        stat_card("DRAFT CLASSES", str(ls["draft_classes"]), ls["year_range"], "blue"),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        stat_card("FRANCHISE PLAYERS", str(ls["franchise_total"]), f"{round(ls['franchise_total']/ls['total_players']*100)}% of all drafted", "gold"),
        unsafe_allow_html=True,
    )
with c4:
    leader_color = "blue" if leader == "Matt" else "red"
    st.markdown(
        stat_card("SCORING LEADER", leader.upper(), f"+{delta:.1f} avg score edge", leader_color),
        unsafe_allow_html=True,
    )

# ── GOAT Race ─────────────────────────────────────────────────────────────────

st.markdown("""<style>
.db-goat-mini-row{display:flex;align-items:center;gap:14px;padding:10px 0;border-bottom:1px solid var(--border);}
.db-goat-mini-row:last-child{border-bottom:none;}
.db-goat-mini-rank{width:22px;flex-shrink:0;font-size:11px;font-weight:900;letter-spacing:1px;color:var(--text-label);}
.db-goat-mini-name{flex:1;font-size:14px;font-weight:700;color:var(--text-primary);}
.db-goat-mini-score{font-size:16px;font-weight:900;color:var(--gold);}
</style>""", unsafe_allow_html=True)

st.markdown(section_header("GOAT RACE", "All-time dynasty leaders — top 3"), unsafe_allow_html=True)

teaser_html = ""
for i, row in top3.iterrows():
    chip_cls = "tb-chip tb-chip-matt" if row["OWNER"] == "Matt" else "tb-chip tb-chip-ryan"
    teaser_html += (
        f'<div class="db-goat-mini-row">'
        f'<span class="db-goat-mini-rank">#{i + 1}</span>'
        f'<span class="db-goat-mini-name">{row["PLAYER"]}</span>'
        f'<span class="{chip_cls}">{row["OWNER"]}</span>'
        f'<span class="db-goat-mini-score">{fmt_score(row["OVERALL SCORE"])}</span>'
        f'</div>'
    )
st.markdown(teaser_html, unsafe_allow_html=True)
st.page_link("pages/Rankings.py", label="View full rankings →", icon="📊")

# ── Best Value Picks ──────────────────────────────────────────────────────────

st.markdown(
    section_header("BEST VALUE PICKS", "Round 3+ players who outperformed their draft slot"),
    unsafe_allow_html=True,
)

v1, v2, v3 = st.columns(3)

for col, (_, vrow) in zip([v1, v2, v3], value_picks.iterrows()):
    color = "blue" if vrow["OWNER"] == "Matt" else "red"
    col.markdown(
        callout(
            label  = f"Rd {int(vrow['ROUND'])} · {vrow['OWNER']} · {int(vrow['YEAR'])}",
            value  = vrow["PLAYER"],
            detail = f"{vrow['POSITION']} · Score {fmt_score(vrow['OVERALL SCORE'])} · {vrow['CAREER_TIER']}",
            color  = color,
        ),
        unsafe_allow_html=True,
    )

# ── Momentum Meter ─────────────────────────────────────────────────────────────
# Shows each owner's avg score trend across the last 5 scored draft classes.

st.markdown("""<style>
.db-momentum-wrap{display:flex;gap:24px;margin-bottom:8px;}
.db-momentum-card{flex:1;background:rgba(10,14,25,.7);border:1px solid rgba(255,255,255,.07);
border-radius:10px;padding:18px 20px;}
.db-momentum-owner{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
margin-bottom:12px;}
.db-momentum-owner.matt{color:#2E7DF7;}
.db-momentum-owner.ryan{color:#E63B3B;}
.db-momentum-rows{display:flex;flex-direction:column;gap:6px;}
.db-momentum-row{display:flex;align-items:center;gap:10px;}
.db-momentum-yr{font-size:11px;font-weight:700;color:#6070a0;width:36px;flex-shrink:0;}
.db-momentum-bar-wrap{flex:1;height:6px;background:rgba(255,255,255,.05);border-radius:3px;}
.db-momentum-bar{height:6px;border-radius:3px;}
.db-momentum-bar.matt{background:#2E7DF7;}
.db-momentum-bar.ryan{background:#E63B3B;}
.db-momentum-val{font-size:11px;font-weight:800;color:#c0cce0;width:36px;text-align:right;flex-shrink:0;}
.db-momentum-arrow{font-size:18px;font-weight:900;margin-left:8px;}
.db-momentum-trend{display:flex;align-items:center;margin-top:12px;padding-top:10px;
border-top:1px solid rgba(255,255,255,.06);}
.db-momentum-trend-lbl{font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
color:#4a6080;flex:1;}
.db-momentum-trend-val{font-size:12px;font-weight:800;}
.db-momentum-trend-val.up{color:#22c55e;}
.db-momentum-trend-val.down{color:#E63B3B;}
.db-momentum-trend-val.flat{color:#94a3b8;}
</style>""", unsafe_allow_html=True)

st.markdown(
    section_header("MOMENTUM METER", "Avg score trend · last 5 scored draft classes per owner"),
    unsafe_allow_html=True,
)

_cs = compute_class_stats(df)

def _build_momentum_card(owner: str, cls_name: str) -> str:
    """Build the momentum card HTML for one owner."""
    odf = _cs[(_cs["OWNER"] == owner) & (_cs["scored"] > 0)].sort_values("YEAR")
    last5 = odf.tail(5)
    if len(last5) == 0:
        return ""
    max_avg = max(last5["avg_score"].max(), 1)
    rows_html = ""
    for _, r in last5.iterrows():
        bar_w = round(r["avg_score"] / max_avg * 100)
        rows_html += (
            f'<div class="db-momentum-row">'
            f'<span class="db-momentum-yr">{int(r["YEAR"])}</span>'
            f'<div class="db-momentum-bar-wrap">'
            f'<div class="db-momentum-bar {cls_name}" style="width:{bar_w}%"></div>'
            f'</div>'
            f'<span class="db-momentum-val">{r["avg_score"]:.1f}</span>'
            f'</div>'
        )
    # Trend: compare last vs previous
    avgs = last5["avg_score"].tolist()
    if len(avgs) >= 2:
        delta_val = avgs[-1] - avgs[-2]
        if delta_val > 1:
            arrow, trend_cls, trend_txt = "↑", "up", f"+{delta_val:.1f} vs prior class"
        elif delta_val < -1:
            arrow, trend_cls, trend_txt = "↓", "down", f"{delta_val:.1f} vs prior class"
        else:
            arrow, trend_cls, trend_txt = "→", "flat", "Holding steady"
        trend_html = (
            f'<div class="db-momentum-trend">'
            f'<span class="db-momentum-trend-lbl">Recent trend</span>'
            f'<span class="db-momentum-trend-val {trend_cls}">{arrow} {trend_txt}</span>'
            f'</div>'
        )
    else:
        trend_html = ""
    return (
        f'<div class="db-momentum-card">'
        f'<div class="db-momentum-owner {cls_name}">{owner} — Momentum</div>'
        f'<div class="db-momentum-rows">{rows_html}</div>'
        f'{trend_html}'
        f'</div>'
    )

_m_html = (
    '<div class="db-momentum-wrap">'
    + _build_momentum_card("Matt", "matt")
    + _build_momentum_card("Ryan", "ryan")
    + '</div>'
)
st.markdown(_m_html, unsafe_allow_html=True)

# ── What's Coming ──────────────────────────────────────────────────────────────
# Forward-looking section: 2026 class status.

st.markdown("""<style>
.db-coming-wrap{background:rgba(10,14,25,.65);border:1px solid rgba(255,255,255,.07);
border-radius:10px;padding:20px 24px;margin-top:4px;}
.db-coming-header{display:flex;align-items:center;gap:16px;margin-bottom:16px;
padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,.06);}
.db-coming-title{font-size:16px;font-weight:900;color:#fff;}
.db-coming-badge{font-size:8px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
padding:4px 10px;border-radius:4px;background:rgba(212,175,55,.12);
color:#D4AF37;border:1px solid rgba(212,175,55,.25);}
.db-coming-meta{font-size:11px;color:#4a6080;margin-left:auto;}
.db-coming-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
.db-coming-stat{text-align:center;padding:12px 0;}
.db-coming-stat-val{font-size:28px;font-weight:900;color:#fff;line-height:1;}
.db-coming-stat-lbl{font-size:8px;font-weight:700;letter-spacing:1.5px;
text-transform:uppercase;color:#4a6080;margin-top:4px;}
.db-coming-picks{margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.06);}
.db-coming-picks-lbl{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
color:#4a6080;margin-bottom:10px;}
.db-coming-pick-row{display:flex;align-items:center;gap:10px;padding:7px 0;
border-bottom:1px solid rgba(255,255,255,.04);}
.db-coming-pick-row:last-child{border-bottom:none;}
.db-coming-pick-name{flex:1;font-size:13px;font-weight:700;color:#c0cce0;}
.db-coming-pick-pos{font-size:9px;font-weight:800;letter-spacing:1px;
text-transform:uppercase;color:#4a6080;width:32px;}
.db-coming-pick-rd{font-size:10px;color:#4a6080;width:38px;text-align:right;}
.db-coming-tbd{font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;
padding:3px 8px;border-radius:4px;background:rgba(148,163,184,.1);
color:#94a3b8;border:1px solid rgba(148,163,184,.2);}
</style>""", unsafe_allow_html=True)

st.markdown(
    section_header("WHAT'S COMING", "2026 draft class · season in progress"),
    unsafe_allow_html=True,
)

_class26 = df[df["YEAR"] == 2026]
if len(_class26) > 0:
    _c26_total   = len(_class26)
    _c26_scored  = int(_class26["OVERALL SCORE"].notna().sum())
    _c26_tbd     = _c26_total - _c26_scored
    _c26_matt    = len(_class26[_class26["OWNER"] == "Matt"])
    _c26_ryan    = len(_class26[_class26["OWNER"] == "Ryan"])

    # Stats grid
    _coming_html = (
        '<div class="db-coming-wrap">'
        '<div class="db-coming-header">'
        '<div class="db-coming-title">2026 Draft Class</div>'
        '<span class="db-coming-badge">Season Active</span>'
        f'<span class="db-coming-meta">{_c26_total} picks · {_c26_tbd} pending</span>'
        '</div>'
        '<div class="db-coming-grid">'
        f'<div class="db-coming-stat"><div class="db-coming-stat-val">{_c26_total}</div>'
        f'<div class="db-coming-stat-lbl">Total Picks</div></div>'
        f'<div class="db-coming-stat"><div class="db-coming-stat-val tb-matt">{_c26_matt}</div>'
        f'<div class="db-coming-stat-lbl">Matt Picks</div></div>'
        f'<div class="db-coming-stat"><div class="db-coming-stat-val tb-ryan">{_c26_ryan}</div>'
        f'<div class="db-coming-stat-lbl">Ryan Picks</div></div>'
        f'<div class="db-coming-stat"><div class="db-coming-stat-val" style="color:#D4AF37;">{_c26_tbd}</div>'
        f'<div class="db-coming-stat-lbl">Scores TBD</div></div>'
        '</div>'
    )

    # Pick list
    _c26_sorted = _class26.sort_values(["OWNER", "ROUND"]).reset_index(drop=True)
    if len(_c26_sorted) > 0:
        _rows_html = ""
        for _, pr in _c26_sorted.iterrows():
            _owner_cls = "tb-matt" if pr["OWNER"] == "Matt" else "tb-ryan"
            _rows_html += (
                f'<div class="db-coming-pick-row">'
                f'<span class="db-coming-pick-pos">{pr["POSITION"]}</span>'
                f'<span class="db-coming-pick-name {_owner_cls}">{pr["PLAYER"]}</span>'
                f'<span class="db-coming-pick-rd">Rd {int(pr["ROUND"]) if str(pr["ROUND"]) != "nan" else "?"}</span>'
                f'<span class="db-coming-tbd">TBD</span>'
                f'</div>'
            )
        _coming_html += (
            '<div class="db-coming-picks">'
            '<div class="db-coming-picks-lbl">Draft picks this class</div>'
            + _rows_html +
            '</div>'
        )
    _coming_html += '</div>'
    st.markdown(_coming_html, unsafe_allow_html=True)
else:
    st.markdown(
        '<div style="color:#4a6080;font-size:12px;padding:12px;">2026 class data not yet available.</div>',
        unsafe_allow_html=True,
    )
