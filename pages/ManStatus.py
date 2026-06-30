import html as _html

import streamlit as st

from core.data_loader import load_man_status, workbook_exists
from core.sidebar import render_sidebar
from core.stats import compute_ms_summary, ms_winner_state
from core.utils import safe_int
from core.components import (
    owner_chip,
    position_chip,
    comparison_panel,
    rivalry_stat_row,
    winner_badge,
    timeline_node,
    ms_scoreboard_hero,
    ms_tale_header,
    ms_bout_card,
)

st.set_page_config(
    page_title="Man Status — Trail & Bish Dynasty",
    page_icon="🥊",
    layout="wide",
)

render_sidebar(active="Man Status")

# Arena background — near-black with blue-left / red-right atmospheric split.
# --ms-blue / --ms-red are MAN STATUS-SCOPED HOT TOKENS injected here intentionally.
# ISOLATION RULE: these MUST remain in this file as the sole injector.
# DO NOT move them to :root, theme.css, or any shared init — the hot vs base owner
# color separation (Man Status runs hotter than all other pages) depends on this
# being the only place they are defined. See DECISIONS log for rationale.
st.markdown(
    "<style>"
    ".stApp{"
    "--ms-blue:#1696FF;"
    "--ms-blue-rgb:22,150,255;"
    "--ms-red:#FF4C43;"
    "--ms-red-rgb:255,76,67;"
    "background:"
    "radial-gradient(ellipse at 15% 50%,rgba(8,18,60,.45) 0%,transparent 55%),"
    "radial-gradient(ellipse at 85% 50%,rgba(60,8,8,.45) 0%,transparent 55%),"
    "linear-gradient(180deg,#010208 0%,#000000 100%)"
    "!important}"
    "</style>",
    unsafe_allow_html=True,
)

# ── Guard ─────────────────────────────────────────────────────────────────────

if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────

ms_df   = load_man_status()
summary = compute_ms_summary(ms_df)

# ── Helper ────────────────────────────────────────────────────────────────────

def _safe_str(val) -> str:
    """Return empty string for NaN/None, else stripped string."""
    s = str(val).strip()
    return "" if s in ("nan", "None", "") else s


# =============================================================================
# SECTION 1 — MAIN EVENT HERO
# =============================================================================

st.markdown(
    ms_scoreboard_hero(
        matt_wins = summary["matt_wins"],
        ryan_wins = summary["ryan_wins"],
        ties      = summary["ties"],
        pending   = summary["pending"],
        leader    = summary["leader"],
    ),
    unsafe_allow_html=True,
)

# =============================================================================
# SECTION 2 — SERIES SCORECARD STRIP
# =============================================================================

def _sc_cls(owner: str) -> str:
    return "tb-ms-sc-val-matt" if owner == "Matt" else "tb-ms-sc-val-ryan"

scorecard_html = (
    '<div class="tb-ms-scorecard">'
    f'<div class="tb-ms-sc-tile">'
    f'<div class="tb-ms-sc-label">LONGEST WIN STREAK</div>'
    f'<div class="tb-ms-sc-val {_sc_cls(summary["best_streak_owner"])}">'
    f'{summary["best_streak_len"]}W</div>'
    f'<div class="tb-ms-sc-detail">{summary["best_streak_owner"]}</div>'
    f'</div>'
    f'<div class="tb-ms-sc-tile">'
    f'<div class="tb-ms-sc-label">BIGGEST BLOWOUT</div>'
    f'<div class="tb-ms-sc-val {_sc_cls(summary["biggest_margin_winner"])}">'
    f'+{summary["biggest_margin"]}</div>'
    f'<div class="tb-ms-sc-detail">'
    f'{summary["biggest_margin_winner"]} · {summary["biggest_margin_year"]}</div>'
    f'</div>'
    f'<div class="tb-ms-sc-tile">'
    f'<div class="tb-ms-sc-label">CLOSEST BOUT</div>'
    f'<div class="tb-ms-sc-val {_sc_cls(summary["closest_margin_winner"])}">'
    f'+{summary["closest_margin"]}</div>'
    f'<div class="tb-ms-sc-detail">'
    f'{summary["closest_margin_winner"]} · {summary["closest_margin_year"]}</div>'
    f'</div>'
    f'<div class="tb-ms-sc-tile">'
    f'<div class="tb-ms-sc-label">ACTIVE STREAK</div>'
    f'<div class="tb-ms-sc-val {_sc_cls(summary["cur_streak_owner"])}">'
    f'{summary["cur_streak_len"]}W</div>'
    f'<div class="tb-ms-sc-detail">{summary["cur_streak_owner"]} · current run</div>'
    f'</div>'
    '</div>'
)
st.markdown(scorecard_html, unsafe_allow_html=True)

# =============================================================================
# SECTION 3 — TALE OF THE TAPE (selected bout)
# =============================================================================

st.markdown(
    '<div class="tb-ms-divider"><span>🥊 TALE OF THE TAPE</span></div>',
    unsafe_allow_html=True,
)

# Bout picker — defaults to most recent decided bout
_bout_years = sorted(ms_df["YEAR"].astype(int).tolist())

def _bout_label(y: int) -> str:
    row = ms_df[ms_df["YEAR"].astype(int) == y].iloc[0]
    w = ms_winner_state(str(row["WINNER"]))
    if w == "Matt":  return f"{y} · Matt wins"
    if w == "Ryan":  return f"{y} · Ryan wins"
    if w == "Tie":   return f"{y} · Draw"
    return f"{y} · Pending"

_default_idx = (
    _bout_years.index(summary["featured_bout_year"])
    if summary["featured_bout_year"] in _bout_years
    else len(_bout_years) - 1
)

_picker_col, _spacer = st.columns([1, 2])
with _picker_col:
    _selected_year = st.selectbox(
        "SELECT BOUT",
        options=_bout_years,
        index=_default_idx,
        format_func=_bout_label,
        key="ms_bout_year",
    )

feat_row    = ms_df[ms_df["YEAR"].astype(int) == _selected_year].iloc[0]
feat_year   = int(feat_row["YEAR"])
feat_winner = ms_winner_state(str(feat_row["WINNER"]))
feat_margin = safe_int(feat_row["MARGIN"])
feat_m_score = safe_int(feat_row["MATT_SCORE"])
feat_r_score = safe_int(feat_row["RYAN_SCORE"])
feat_m_pos   = _safe_str(feat_row["MATT_POS"])
feat_r_pos   = _safe_str(feat_row["RYAN_POS"])
feat_m_pick  = _safe_str(feat_row["MATT_PICK"])
feat_r_pick  = _safe_str(feat_row["RYAN_PICK"])
feat_m_res   = _safe_str(feat_row["MATT_RESUME"])
feat_r_res   = _safe_str(feat_row["RYAN_RESUME"])
feat_m_notes = _safe_str(feat_row["MATT_NOTES"])
feat_r_notes = _safe_str(feat_row["RYAN_NOTES"])

w_matt = "Matt" if feat_winner == "Matt" else ""
w_ryan = "Ryan" if feat_winner == "Ryan" else ""

# Build tale-of-the-tape: header + comparison rows in one markdown
tot_rows = (
    rivalry_stat_row("PICK",     feat_m_pick,             feat_r_pick,             "")
    + rivalry_stat_row("POSITION", feat_m_pos,            feat_r_pos,              "")
    + rivalry_stat_row("SCORE",    str(feat_m_score),     str(feat_r_score),       feat_winner)
    + rivalry_stat_row("RÉSUMÉ",   feat_m_res or "—",     feat_r_res or "—",       "")
    + rivalry_stat_row("WINNER",
        ("✓ MATT" if feat_winner == "Matt" else "—"),
        ("✓ RYAN" if feat_winner == "Ryan" else "—"),
        feat_winner)
)
if feat_m_notes or feat_r_notes:
    tot_rows += rivalry_stat_row("NOTES", feat_m_notes or "—", feat_r_notes or "—", "")

# Single markdown: header div (open) + comparison_panel + closing div
tot_html = (
    ms_tale_header(feat_year, feat_m_pick, feat_m_pos,
                   feat_r_pick, feat_r_pos, feat_winner, feat_margin)
    + comparison_panel(f"FEATURED BOUT · {feat_year}", tot_rows)
    + "</div>"   # closes tb-ms-tot-wrap opened by ms_tale_header
)
st.markdown(tot_html, unsafe_allow_html=True)

# =============================================================================
# SECTION 4 — THE FIGHT CARD (all 20 bouts)
# =============================================================================

st.markdown(
    '<div class="tb-ms-divider"><span>🥊 THE FIGHT CARD · ALL 20 BOUTS</span></div>',
    unsafe_allow_html=True,
)

# Build entire fight card as one HTML string — single st.markdown() call
fight_card_html = '<div class="tb-ms-fight-card">'
for _, row in ms_df.sort_values("YEAR", ascending=False).iterrows():
    fight_card_html += ms_bout_card(
        year        = int(row["YEAR"]),
        matt_pick   = _safe_str(row["MATT_PICK"])   or "TBD",
        matt_pos    = _safe_str(row["MATT_POS"])    or "—",
        matt_score  = row["MATT_SCORE"],
        matt_resume = _safe_str(row["MATT_RESUME"]),
        ryan_pick   = _safe_str(row["RYAN_PICK"])   or "TBD",
        ryan_pos    = _safe_str(row["RYAN_POS"])    or "—",
        ryan_score  = row["RYAN_SCORE"],
        ryan_resume = _safe_str(row["RYAN_RESUME"]),
        winner      = ms_winner_state(str(row["WINNER"])),
        margin      = row["MARGIN"],
        matt_notes  = _safe_str(row["MATT_NOTES"]),
        ryan_notes  = _safe_str(row["RYAN_NOTES"]),
    )
fight_card_html += "</div>"
st.markdown(fight_card_html, unsafe_allow_html=True)

# =============================================================================
# SECTION 5 — MOMENTUM STRIP
# =============================================================================

st.markdown(
    '<div class="tb-ms-divider"><span>🥊 MOMENTUM STRIP · 2007 → 2026</span></div>',
    unsafe_allow_html=True,
)

momentum_html = '<div class="tb-ms-momentum"><div class="tb-timeline-wrap"><div class="tb-timeline-track">'
for _, row in ms_df.sort_values("YEAR").iterrows():
    year    = int(row["YEAR"])
    winner  = ms_winner_state(str(row["WINNER"]))
    m_pick  = _safe_str(row["MATT_PICK"])
    r_pick  = _safe_str(row["RYAN_PICK"])
    if winner == "Pending":
        label = "TBD"
    elif winner == "Tie":
        label = "Draw"
    else:
        label = f"{winner} wins"
    momentum_html += timeline_node(year, label, winner, is_milestone=False)
momentum_html += "</div></div></div>"

st.markdown(momentum_html, unsafe_allow_html=True)
