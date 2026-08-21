import html as _html

import streamlit as st

from core.data_loader import load_man_status, load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import compute_ms_summary, ms_winner_state
from core.utils import safe_int, FIRST_YEAR, CURRENT_YEAR, format_round
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
    f'<div class="tb-ms-divider"><span>🥊 MOMENTUM STRIP · {FIRST_YEAR} → {CURRENT_YEAR}</span></div>',
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

# =============================================================================
# SECTION 6 — BUILD YOUR OWN BATTLE (V2 feature)
# Free-choice player comparison, not limited to the pre-curated same-position
# matchups above. Pulls straight from the full 354-player roster.
# =============================================================================

st.markdown(
    '<div class="tb-ms-divider"><span>⚔️ BUILD YOUR OWN BATTLE</span></div>',
    unsafe_allow_html=True,
)

_players_df = load_players()
_matt_pool  = _players_df[_players_df["OWNER"] == "Matt"].dropna(subset=["OVERALL SCORE"]).sort_values("PLAYER")
_ryan_pool  = _players_df[_players_df["OWNER"] == "Ryan"].dropna(subset=["OVERALL SCORE"]).sort_values("PLAYER")

_bb_c1, _bb_c2 = st.columns(2)
with _bb_c1:
    matt_pick_name = st.selectbox(
        "Matt's player", options=_matt_pool["PLAYER"].tolist(), key="bb_matt",
    )
with _bb_c2:
    ryan_pick_name = st.selectbox(
        "Ryan's player", options=_ryan_pool["PLAYER"].tolist(), key="bb_ryan",
    )

_m_row = _matt_pool[_matt_pool["PLAYER"] == matt_pick_name].iloc[0]
_r_row = _ryan_pool[_ryan_pool["PLAYER"] == ryan_pick_name].iloc[0]

_ORDINAL = {"Elite": 4, "High": 3, "Moderate": 2, "Low": 1, "Minimal": 0}
_AWARD_COLS_BB = ["MVP", "OPOY", "DPOY", "OROY", "DROY", "ALL_PRO", "SB Win", "SB_MVP"]

def _bb_winner_numeric(m_val: float, r_val: float) -> str:
    if m_val > r_val:
        return "Matt"
    if r_val > m_val:
        return "Ryan"
    return ""

def _bb_winner_ordinal(m_val: str, r_val: str) -> str:
    return _bb_winner_numeric(_ORDINAL.get(m_val, -1), _ORDINAL.get(r_val, -1))

m_score = float(_m_row["OVERALL SCORE"])
r_score = float(_r_row["OVERALL SCORE"])
m_awards = int(sum(safe_int(_m_row.get(c, 0)) for c in _AWARD_COLS_BB))
r_awards = int(sum(safe_int(_r_row.get(c, 0)) for c in _AWARD_COLS_BB))

_bb_rows = [
    rivalry_stat_row("Overall Score", f"{m_score:.1f}", f"{r_score:.1f}", _bb_winner_numeric(m_score, r_score)),
    rivalry_stat_row("Career Tier", str(_m_row["CAREER_TIER"]), str(_r_row["CAREER_TIER"]), ""),
    rivalry_stat_row(
        "Production", str(_m_row["PRODUCTION"]), str(_r_row["PRODUCTION"]),
        _bb_winner_ordinal(str(_m_row["PRODUCTION"]), str(_r_row["PRODUCTION"])),
    ),
    rivalry_stat_row(
        "Longevity", str(_m_row["LONGEVITY"]), str(_r_row["LONGEVITY"]),
        _bb_winner_ordinal(str(_m_row["LONGEVITY"]), str(_r_row["LONGEVITY"])),
    ),
    rivalry_stat_row(
        "Championship Impact", str(_m_row["CHAMPIONSHIP_IMPACT"]), str(_r_row["CHAMPIONSHIP_IMPACT"]),
        _bb_winner_ordinal(str(_m_row["CHAMPIONSHIP_IMPACT"]), str(_r_row["CHAMPIONSHIP_IMPACT"])),
    ),
    rivalry_stat_row("Total Awards", str(m_awards), str(r_awards), _bb_winner_numeric(m_awards, r_awards)),
    rivalry_stat_row(
        "Draft Capital", f"{format_round(_m_row['ROUND'])} · {int(_m_row['YEAR'])}",
        f"{format_round(_r_row['ROUND'])} · {int(_r_row['YEAR'])}", "",
    ),
]

# Tally wins across the rows that produced a determinable winner
_row_winners = [
    _bb_winner_numeric(m_score, r_score),
    _bb_winner_ordinal(str(_m_row["PRODUCTION"]), str(_r_row["PRODUCTION"])),
    _bb_winner_ordinal(str(_m_row["LONGEVITY"]), str(_r_row["LONGEVITY"])),
    _bb_winner_ordinal(str(_m_row["CHAMPIONSHIP_IMPACT"]), str(_r_row["CHAMPIONSHIP_IMPACT"])),
    _bb_winner_numeric(m_awards, r_awards),
]
_matt_wins = _row_winners.count("Matt")
_ryan_wins = _row_winners.count("Ryan")

if _matt_wins > _ryan_wins:
    _verdict, _v_winner = f"VERDICT: {matt_pick_name} wins {_matt_wins}–{_ryan_wins}", "Matt"
elif _ryan_wins > _matt_wins:
    _verdict, _v_winner = f"VERDICT: {ryan_pick_name} wins {_ryan_wins}–{_matt_wins}", "Ryan"
else:
    _verdict, _v_winner = f"VERDICT: Dead even, {_matt_wins}–{_ryan_wins}", "Tie"

st.markdown(
    comparison_panel(f"{matt_pick_name} vs {ryan_pick_name}", "".join(_bb_rows)),
    unsafe_allow_html=True,
)
st.markdown(
    f'<div style="text-align:center;margin-top:10px;font-size:15px;font-weight:900;'
    f'letter-spacing:1px;">{winner_badge(_v_winner)} &nbsp; {_verdict}</div>',
    unsafe_allow_html=True,
)
