import streamlit as st

from core.data_loader import load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import (
    compute_league_stats,
    compute_owner_stats,
    score_leader,
    rank_players,
    rank_players_by_position,
    POSITION_GROUPS,
    MIN_RANKED_SAMPLE,
)
from core.utils import safe_int, is_score_pending
from core.components import (
    page_header,
    section_header,
    stat_card,
    player_row,
    player_table,
    owner_chip,
    tier_badge,
    position_chip,
    rivalry_stat_row,
    comparison_panel,
    grade_badge,
    winner_badge,
)

st.set_page_config(
    page_title="Rankings — Trail & Bish Dynasty",
    page_icon="📊",
    layout="wide",
)

render_sidebar(active="Rankings")

# ── Guard ─────────────────────────────────────────────────────────────────────

if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────

df          = load_players()
ls          = compute_league_stats(df)
matt_stats  = compute_owner_stats(df, "Matt")
ryan_stats  = compute_owner_stats(df, "Ryan")
leader, _delta = score_leader(matt_stats, ryan_stats)

ranked      = rank_players(df)
scored      = ranked[ranked["RANK"] > 0].reset_index(drop=True)

# =============================================================================
# PAGE RENDER
# =============================================================================

# ── Hero Header ───────────────────────────────────────────────────────────────

st.markdown(
    page_header(
        "📊 Rankings",
        f"{len(scored)} players ranked · {ls['draft_classes']} classes · {ls['year_range']}",
    ),
    unsafe_allow_html=True,
)

# ── Rankings scoped CSS ────────────────────────────────────────────────────────

st.markdown("""<style>
.rk-lead-featured{padding:16px 20px;background:rgba(243,188,46,.04);
border-left:3px solid rgba(243,188,46,.55);margin-bottom:1px;}
.rk-lead-featured .tb-pr-name{font-size:17px;font-weight:800;}
.rk-lead-featured .tb-pr-score-num{font-size:22px;}
.rk-lead-featured .tb-pr-rank{font-size:14px;font-weight:900;}
.rk-field-break{font-size:18px;font-weight:900;letter-spacing:3px;color:var(--text-label);
text-transform:uppercase;text-align:center;padding:20px 0 10px;
border-top:1px solid var(--border);margin-top:4px;}
.rk-overall-header{text-align:center;margin:28px 0 20px;}
.rk-overall-title{font-size:20px;font-weight:900;letter-spacing:3px;
text-transform:uppercase;color:var(--text-label);}
.rk-overall-sub{display:block;font-size:12px;color:#4A6280;margin-top:5px;letter-spacing:1px;}
.rk-overall-rule{display:block;width:48px;height:2px;background:var(--primary);margin:8px auto 0;}
</style>""", unsafe_allow_html=True)

# ── Overall Leaderboard ───────────────────────────────────────────────────────

st.markdown(
    f'<div class="rk-overall-header">'
    f'<div class="rk-overall-title">OVERALL LEADERBOARD</div>'
    f'<span class="rk-overall-sub">Top 25 of {len(scored)} ranked players</span>'
    f'<span class="rk-overall-rule"></span>'
    f'</div>',
    unsafe_allow_html=True,
)

# Tie-aware featured cutoff: everyone at or above the 5th player's true score is featured.
# Comparing on raw float prevents two players with identical true scores straddling the divide.
_cutoff_score = float(scored.iloc[4]["OVERALL SCORE"]) if len(scored) >= 5 else 0.0

top25      = scored.head(25)
rows_html  = ""
_field_break_inserted = False
for _, p in top25.iterrows():
    _rank  = int(p["RANK"])
    _score = float(p["OVERALL SCORE"])
    _is_featured = _score >= _cutoff_score
    if not _is_featured and not _field_break_inserted:
        rows_html += '<div class="rk-field-break">THE FIELD</div>'
        _field_break_inserted = True
    rows_html += player_row(
        rank     = _rank,
        name     = str(p["PLAYER"]),
        owner    = str(p["OWNER"]),
        position = str(p["POSITION"]),
        year     = safe_int(p["YEAR"]),
        score    = _score,
        tier     = str(p["CAREER_TIER"]),
        featured = _is_featured,
    )

st.markdown(player_table(rows_html), unsafe_allow_html=True)

# ── Position Leaderboards — Signature Feature ─────────────────────────────────

st.markdown(
    section_header("POSITION LEADERBOARDS", "Top 5 at each position · Owner comparison"),
    unsafe_allow_html=True,
)

pos_groups = list(POSITION_GROUPS.keys())

selected_pos = st.radio(
    "Position group",
    options=pos_groups,
    horizontal=True,
    key="rankings_pos",
    label_visibility="collapsed",
)

group_positions = POSITION_GROUPS[selected_pos]

# Ranked players for this group
pos_ranked = rank_players_by_position(df, group_positions)
scored_pos = pos_ranked[pos_ranked["RANK"] > 0].reset_index(drop=True)
top5       = scored_pos.head(5)

# Per-owner stats for this group
group_df   = df[df["POSITION"].isin(group_positions)]
matt_pos   = compute_owner_stats(group_df, "Matt")
ryan_pos   = compute_owner_stats(group_df, "Ryan")

# Helper: format avg with sample caveat when below MIN_RANKED_SAMPLE
def _avg_label(stats: dict) -> str:
    avg = stats["avg_score"]
    n   = stats["total"]
    if n < MIN_RANKED_SAMPLE:
        return f"{avg:.1f} (n={n})"
    return f"{avg:.1f}"

# Winner logic
avg_winner       = "Matt" if matt_pos["avg_score"] > ryan_pos["avg_score"] else "Ryan" if ryan_pos["avg_score"] > matt_pos["avg_score"] else ""
franchise_winner = "Matt" if matt_pos["franchise"] > ryan_pos["franchise"] else "Ryan" if ryan_pos["franchise"] > matt_pos["franchise"] else ""
high_winner      = "Matt" if matt_pos["high_score"] > ryan_pos["high_score"] else "Ryan" if ryan_pos["high_score"] > matt_pos["high_score"] else ""
total_winner     = ""  # Both owners always have equal total picks (177 each) — no per-position winner shown for total

# Group header with total counts
group_scored = len(scored_pos)
st.markdown(
    f'<div class="tb-pos-group-label">'
    f'<span class="tb-pos-group-name">{selected_pos}</span>'
    f'<span class="tb-pos-group-meta">{group_scored} ranked · {matt_pos["total"]} Matt / {ryan_pos["total"]} Ryan</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# Two-column layout: top-5 leaderboard | owner comparison
left_col, right_col = st.columns([2, 1.4])

with left_col:
    if len(top5) == 0:
        st.markdown(
            '<div class="tb-empty-state">No scored players at this position.</div>',
            unsafe_allow_html=True,
        )
    else:
        pos_rows = ""
        for _, p in top5.iterrows():
            pos_rows += player_row(
                rank     = int(p["RANK"]),
                name     = str(p["PLAYER"]),
                owner    = str(p["OWNER"]),
                position = str(p["POSITION"]),
                year     = safe_int(p["YEAR"]),
                score    = float(p["OVERALL SCORE"]),
                tier     = str(p["CAREER_TIER"]),
            )
        st.markdown(player_table(pos_rows), unsafe_allow_html=True)

with right_col:
    comp_rows = (
        rivalry_stat_row(
            "Players",
            str(matt_pos["total"]),
            str(ryan_pos["total"]),
            total_winner,
        )
        + rivalry_stat_row(
            "Avg Score",
            _avg_label(matt_pos),
            _avg_label(ryan_pos),
            avg_winner,
        )
        + rivalry_stat_row(
            "Franchise",
            str(matt_pos["franchise"]),
            str(ryan_pos["franchise"]),
            franchise_winner,
        )
        + rivalry_stat_row(
            "Best Score",
            str(matt_pos["high_score"]),
            str(ryan_pos["high_score"]),
            high_winner,
        )
    )
    st.markdown(
        comparison_panel(f"{selected_pos} — OWNER COMPARISON", comp_rows),
        unsafe_allow_html=True,
    )

    # Show who leads this position with a winner badge
    if avg_winner:
        st.markdown(
            f'<div style="margin-top:10px;text-align:center;">'
            f'{winner_badge(avg_winner, f"{avg_winner} leads {selected_pos}")}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="margin-top:10px;text-align:center;">'
            f'{winner_badge("Tie", "Tied")}'
            f'</div>',
            unsafe_allow_html=True,
        )
