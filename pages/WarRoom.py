import pandas as pd
import streamlit as st

from core.data_loader import load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import (
    compute_league_stats,
    compute_owner_stats,
    score_leader,
    compute_class_stats,
    compute_series_record,
)
from core.utils import safe_int, safe_str, is_score_pending
from core.components import (
    page_header,
    section_header,
    stat_card,
    callout,
    owner_chip,
    award_badges,
    winner_badge,
    grade_badge,
    rivalry_stat_row,
    comparison_panel,
    draft_class_card,
    class_dive_row,
    tier_badge,
    position_chip,
)

st.set_page_config(
    page_title="War Room — Trail & Bish Dynasty",
    page_icon="⚔️",
    layout="wide",
)

render_sidebar(active="War Room")

# --wr-brass / --wr-brass-rgb / --wr-brass-light / --wr-brass-dark are WAR-ROOM-SCOPED
# TOKENS injected here intentionally. ISOLATION RULE: these MUST remain in this file
# as the sole injector. DO NOT move them to :root, theme.css, or any shared init —
# the S-grade prestige brass treatment is a War Room-only elevation and must not bleed
# to Rankings or Legacy (both also render .tb-grade-S). See DECISIONS D017 for rationale.
# Note: --wr-brass intentionally equals --gold (#F3BC2E); the metallic identity comes
# from the gradient sweep + glow below, not from a different base hue.
st.markdown(
    "<style>"
    ".stApp{"
    "--wr-brass:#F3BC2E;"
    "--wr-brass-rgb:243,188,46;"
    "--wr-brass-light:#F9D366;"
    "--wr-brass-dark:#9A7521;"
    "}"
    ".stApp .tb-grade-S{"
    "background:linear-gradient(90deg,var(--wr-brass-dark) 0%,var(--wr-brass-light) 50%,var(--wr-brass-dark) 100%);"
    "border:1px solid var(--wr-brass);"
    "color:var(--bg-app);"
    "box-shadow:0 0 22px rgba(var(--wr-brass-rgb),.28);"
    "}"
    "</style>",
    unsafe_allow_html=True,
)

# ── Guard ─────────────────────────────────────────────────────────────────────

if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────

df = load_players()

_AWARD_COLS = ["MVP", "OPOY", "DPOY", "OROY", "DROY", "ALL_PRO", "SB Win", "SB_MVP"]

ls          = compute_league_stats(df)
matt_stats  = compute_owner_stats(df, "Matt")
ryan_stats  = compute_owner_stats(df, "Ryan")
leader, _delta = score_leader(matt_stats, ryan_stats)

class_df  = compute_class_stats(df)
record    = compute_series_record(class_df)

# Build per-year dict: year → {Matt: row_dict, Ryan: row_dict}
class_by_year: dict[int, dict[str, dict]] = {}
for _, row in class_df.iterrows():
    year  = int(row["YEAR"])
    owner = str(row["OWNER"])
    class_by_year.setdefault(year, {})[owner] = row.to_dict()

# Derive class winner for each year
def _class_winner(m: dict, r: dict) -> str:
    if m.get("scored", 0) == 0 and r.get("scored", 0) == 0:
        return "Tie"
    if m.get("avg_score", 0) > r.get("avg_score", 0):
        return "Matt"
    if r.get("avg_score", 0) > m.get("avg_score", 0):
        return "Ryan"
    return "Tie"

# Overall series leader
def _series_leader(rec: dict) -> tuple[str, str]:
    if rec["matt_wins"] > rec["ryan_wins"]:
        return "Matt", f"{rec['matt_wins']}–{rec['ryan_wins']}–{rec['ties']}"
    if rec["ryan_wins"] > rec["matt_wins"]:
        return "Ryan", f"{rec['ryan_wins']}–{rec['matt_wins']}–{rec['ties']}"
    return "Tied", f"{rec['matt_wins']}–{rec['ryan_wins']}–{rec['ties']}"

series_leader, series_record_str = _series_leader(record)

# Bust winner: fewer busts is better
bust_winner = (
    "Matt" if matt_stats["busts"] < ryan_stats["busts"]
    else "Ryan" if ryan_stats["busts"] < matt_stats["busts"]
    else ""
)

franchise_winner = (
    "Matt" if matt_stats["franchise"] > ryan_stats["franchise"]
    else "Ryan" if ryan_stats["franchise"] > matt_stats["franchise"]
    else ""
)

score_winner = leader  # already computed

high_score_winner = (
    "Matt" if matt_stats["high_score"] > ryan_stats["high_score"]
    else "Ryan" if ryan_stats["high_score"] > matt_stats["high_score"]
    else ""
)

# =============================================================================
# PAGE RENDER
# =============================================================================

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown(
    page_header(
        "⚔️ Draft War Room",
        f"{ls['draft_classes']} draft classes · {ls['total_players']} picks · {ls['year_range']}",
    ),
    unsafe_allow_html=True,
)

# ── Series Record — stat cards ────────────────────────────────────────────────

series_leader_color = (
    "blue" if series_leader == "Matt"
    else "red" if series_leader == "Ryan"
    else "gold"
)
series_leader_sub = f"{series_record_str} W–L–T" if series_leader != "Tied" else "Dead even"

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        stat_card("MATT WINS", str(record["matt_wins"]), "Draft classes won", "blue"),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        stat_card("RYAN WINS", str(record["ryan_wins"]), "Draft classes won", "red"),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        stat_card("TIED", str(record["ties"]), "Classes equally matched", "gold"),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        stat_card(
            "SERIES LEADER",
            series_leader.upper(),
            series_leader_sub,
            series_leader_color,
        ),
        unsafe_allow_html=True,
    )

# ── Draft Class Report Cards — Signature Feature ──────────────────────────────

st.markdown(
    section_header("DRAFT CLASS REPORT CARDS", "All 20 classes graded by avg score"),
    unsafe_allow_html=True,
)

cards_html = ""
for year in sorted(class_by_year.keys()):
    m = class_by_year[year].get("Matt", {})
    r = class_by_year[year].get("Ryan", {})
    w = _class_winner(m, r)
    total = m.get("total", 0) + r.get("total", 0)
    cards_html += draft_class_card(year, total, w, m, r)

st.markdown(
    f'<div class="tb-war-room-grid">{cards_html}</div>',
    unsafe_allow_html=True,
)

# ── Class Deep Dive — select any year ────────────────────────────────────────

st.markdown(
    section_header("CLASS DEEP DIVE", "All picks from a single draft class"),
    unsafe_allow_html=True,
)

years_all    = sorted(df["YEAR"].unique().astype(int), reverse=True)
default_year = next(
    (y for y in years_all if y not in (2025, 2026)),
    years_all[0],
)

selected_year = st.selectbox(
    "Select draft class",
    options=years_all,
    index=years_all.index(default_year),
    format_func=lambda y: f"{y} Draft Class",
    key="dive_year",
)

year_df = df[df["YEAR"] == selected_year].copy()
year_df["_award_total"] = year_df[_AWARD_COLS].fillna(0).sum(axis=1)

# Sort: scored players by score desc, then pending
scored_df  = year_df.dropna(subset=["OVERALL SCORE"]).sort_values("OVERALL SCORE", ascending=False)
pending_df = year_df[year_df["OVERALL SCORE"].apply(is_score_pending)]
year_df = pd.concat([scored_df, pending_df]) if not pending_df.empty else scored_df

# Class summary line
m_row = class_by_year.get(selected_year, {}).get("Matt", {})
r_row = class_by_year.get(selected_year, {}).get("Ryan", {})
class_w = _class_winner(m_row, r_row)

m_avg_str = f"{m_row.get('avg_score', 0):.1f}" if m_row.get("scored", 0) else "TBD"
r_avg_str = f"{r_row.get('avg_score', 0):.1f}" if r_row.get("scored", 0) else "TBD"

st.markdown(
    f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;'
    f'font-size:13px;color:#4A6280;">'
    f'<span style="font-weight:800;color:#ffffff;font-size:18px;">{selected_year}</span>'
    f'<span>{len(year_df)} picks</span>'
    f'<span>Matt avg <b style="color:#2E7DF7">{m_avg_str}</b></span>'
    f'<span>Ryan avg <b style="color:#E63B3B">{r_avg_str}</b></span>'
    f'{winner_badge(class_w)}'
    f'</div>',
    unsafe_allow_html=True,
)

# Table header
st.markdown(
    f"""
    <div class="tb-class-dive-table">
        <div class="tb-class-dive-header">
            <div>#</div>
            <div>PLAYER</div>
            <div>OWNER</div>
            <div>POS</div>
            <div>ROUND</div>
            <div>SCORE</div>
            <div>TIER</div>
            <div>AWARDS</div>
        </div>
    """,
    unsafe_allow_html=True,
)

rows_html = ""
for rank, (_, p) in enumerate(year_df.iterrows(), start=1):
    score = float(p["OVERALL SCORE"]) if not is_score_pending(p["OVERALL SCORE"]) else float("nan")
    rows_html += class_dive_row(
        rank        = rank,
        name        = str(p["PLAYER"]),
        owner       = str(p["OWNER"]),
        position    = str(p["POSITION"]),
        round_      = safe_int(p["ROUND"]),
        score       = score,
        tier        = str(p["CAREER_TIER"]),
        awards_html = award_badges(p.to_dict()),
    )

st.markdown(f"{rows_html}</div>", unsafe_allow_html=True)
