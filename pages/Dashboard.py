import streamlit as st

from core.data_loader import load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import compute_league_stats, compute_owner_stats, score_leader, POSITION_GROUPS
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
