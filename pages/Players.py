import streamlit as st

from core.data_loader import load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import compute_league_stats, compute_owner_stats, POSITION_GROUPS as _POS_GROUPS
from core.utils import safe_int, safe_str, is_score_pending, fmt_score
from core.components import (
    page_header,
    section_header,
    stat_card,
    callout,
    owner_chip,
    award_badges,
    elite_player_card,
    player_detail_card,
    roster_table_header,
    player_roster_row,
)

st.set_page_config(
    page_title="Players — Trail & Bish Dynasty",
    page_icon="🏈",
    layout="wide",
)

render_sidebar(active="Players")

# ── Guard ─────────────────────────────────────────────────────────────────────

if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────

df = load_players().copy()

# Award totals for insight cards (modify copy — do not mutate cached DataFrame)
_AWARD_COLS = ["MVP", "OPOY", "DPOY", "OROY", "DROY", "ALL_PRO", "SB Win", "SB_MVP"]
df["_award_total"] = df[_AWARD_COLS].fillna(0).sum(axis=1)

matt_df = df[df["OWNER"] == "Matt"]
ryan_df = df[df["OWNER"] == "Ryan"]

ls         = compute_league_stats(df)
matt_stats = compute_owner_stats(df, "Matt")
ryan_stats = compute_owner_stats(df, "Ryan")
_scored_count = int(df["OVERALL SCORE"].notna().sum())

# ── Position groups for filter ─────────────────────────────────────────────────

POSITION_GROUPS: dict[str, list[str] | None] = {"All": None, **_POS_GROUPS}

SORT_MAP: dict[str, tuple[str, bool]] = {
    "Score ↓":  ("OVERALL SCORE", False),
    "Score ↑":  ("OVERALL SCORE", True),
    "Year ↓":   ("YEAR", False),
    "Year ↑":   ("YEAR", True),
    "Name A→Z": ("PLAYER", True),
    "Round ↑":  ("ROUND", True),
}

# ── Insight players (pre-filter; insight cards always show best per category) ──

best_qb     = df[df["POSITION"] == "QB"].dropna(subset=["OVERALL SCORE"]).sort_values("OVERALL SCORE", ascending=False).iloc[0]
best_wr     = df[df["POSITION"] == "WR"].dropna(subset=["OVERALL SCORE"]).sort_values("OVERALL SCORE", ascending=False).iloc[0]
best_late   = df[df["ROUND"] >= 4].dropna(subset=["OVERALL SCORE"]).sort_values("OVERALL SCORE", ascending=False).iloc[0]
most_awards = df.sort_values("_award_total", ascending=False).iloc[0]

# ── Top 10 for elite cards ─────────────────────────────────────────────────────

top10 = (
    df.dropna(subset=["OVERALL SCORE"])
    .sort_values("OVERALL SCORE", ascending=False)
    .head(10)
    .reset_index(drop=True)
)

# =============================================================================
# PAGE RENDER
# =============================================================================

# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown(
    page_header(
        "🗂️ Players",
        f"{ls['total_players']} players · {ls['draft_classes']} draft classes · {ls['year_range']}",
    ),
    unsafe_allow_html=True,
)

# ── Summary Cards ──────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        stat_card("TOTAL PLAYERS", str(ls["total_players"]), f"{ls['draft_classes']} draft classes", "blue"),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        stat_card("SCORED", str(_scored_count), f"{ls['total_players'] - _scored_count} TBD · pending careers", "blue"),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        stat_card("POSITION GROUPS", str(len(_POS_GROUPS)), "filterable roster groups", "blue"),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        stat_card(
            "FRANCHISE PLAYERS",
            str(ls["franchise_total"]),
            f"{round(ls['franchise_total'] / ls['total_players'] * 100)}% of all drafted",
            "gold",
        ),
        unsafe_allow_html=True,
    )

# ── Quick Insights ─────────────────────────────────────────────────────────────

st.markdown(section_header("QUICK INSIGHTS", "Live facts from the dynasty"), unsafe_allow_html=True)

i1, i2, i3 = st.columns(3)

with i1:
    qb_color = "blue" if best_qb["OWNER"] == "Matt" else "red"
    st.markdown(
        callout(
            "DYNASTY QB",
            str(best_qb["PLAYER"]),
            f"{best_qb['OWNER']} · {safe_int(best_qb['YEAR'])} · Score {fmt_score(best_qb['OVERALL SCORE'])}",
            qb_color,
        ),
        unsafe_allow_html=True,
    )
    wr_color = "blue" if best_wr["OWNER"] == "Matt" else "red"
    st.markdown(
        callout(
            "DYNASTY WR",
            str(best_wr["PLAYER"]),
            f"{best_wr['OWNER']} · {safe_int(best_wr['YEAR'])} · Score {fmt_score(best_wr['OVERALL SCORE'])}",
            wr_color,
        ),
        unsafe_allow_html=True,
    )

with i2:
    late_color = "blue" if best_late["OWNER"] == "Matt" else "red"
    st.markdown(
        callout(
            "BIGGEST LATE-ROUND STEAL",
            str(best_late["PLAYER"]),
            f"{best_late['OWNER']} · Rd {safe_int(best_late['ROUND'])} · Score {fmt_score(best_late['OVERALL SCORE'])}",
            late_color,
        ),
        unsafe_allow_html=True,
    )
    best_year_count = len(df[df["YEAR"] == ls["best_year"]])
    st.markdown(
        callout(
            "BEST DRAFT CLASS",
            str(ls["best_year"]),
            f"Avg score {ls['best_year_avg']:.1f} · {best_year_count} players",
            "green",
        ),
        unsafe_allow_html=True,
    )

with i3:
    aw_color = "blue" if most_awards["OWNER"] == "Matt" else "red"
    st.markdown(
        callout(
            "MOST DECORATED",
            str(most_awards["PLAYER"]),
            f"{most_awards['OWNER']} · {int(most_awards['_award_total'])} total awards",
            "gold",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        callout(
            "AVG DRAFT ROUND",
            f"{ls['avg_round']:.2f}",
            f"Across all {ls['total_players']} picks",
            "blue",
        ),
        unsafe_allow_html=True,
    )

# ── Elite Players — Rankings link ─────────────────────────────────────────────

st.markdown(section_header("ELITE PLAYERS", "All-time leaders — full leaderboard on Rankings"), unsafe_allow_html=True)

st.markdown(
    '<div class="tb-results-count">All-time dynasty leaders by overall score · full top-25 on Rankings</div>',
    unsafe_allow_html=True,
)
st.page_link("pages/Rankings.py", label="View the Overall Leaderboard →", icon="📊")

# ── Player Spotlight ───────────────────────────────────────────────────────────

st.markdown(section_header("PLAYER SPOTLIGHT", "Full profile for any dynasty player"), unsafe_allow_html=True)

all_players = (
    df.sort_values("OVERALL SCORE", ascending=False, na_position="last")["PLAYER"]
    .tolist()
)

spotlight_name = st.selectbox(
    "Select a player",
    options=[""] + all_players,
    format_func=lambda x: "— Choose a player —" if x == "" else x,
    key="spotlight",
)

if spotlight_name:
    sp = df[df["PLAYER"] == spotlight_name].iloc[0]
    st.markdown(
        player_detail_card(
            name         = str(sp["PLAYER"]),
            owner        = str(sp["OWNER"]),
            position     = str(sp["POSITION"]),
            year         = safe_int(sp["YEAR"]),
            round_       = safe_int(sp["ROUND"]),
            score        = float(sp["OVERALL SCORE"]),
            tier         = str(sp["CAREER_TIER"]),
            awards_html  = award_badges(sp.to_dict()),
            notes        = safe_str(sp.get("NOTES", "")),
            production   = safe_str(sp.get("PRODUCTION", "")),
            longevity    = safe_str(sp.get("LONGEVITY", "")),
            champ_impact = safe_str(sp.get("CHAMPIONSHIP_IMPACT", "")),
        ),
        unsafe_allow_html=True,
    )

# ── Filters ────────────────────────────────────────────────────────────────────

st.markdown(section_header("ROSTER", "Every pick, every class"), unsafe_allow_html=True)

f1, f2, f3, f4, f5, f6, f7 = st.columns([2, 2, 2, 2, 2, 2, 3])

with f1:
    owner_filter = st.selectbox("Owner", ["All", "Matt", "Ryan"], key="f_owner")
with f2:
    pos_filter = st.selectbox("Position", list(POSITION_GROUPS.keys()), key="f_pos")
with f3:
    tier_filter = st.selectbox(
        "Tier",
        ["All", "Legend", "Franchise", "High-End Starter", "Starter", "Contributor", "Bust"],
        key="f_tier",
    )
with f4:
    year_opts   = ["All"] + [str(y) for y in sorted(df["YEAR"].unique().astype(int), reverse=True)]
    year_filter = st.selectbox("Draft Class", year_opts, key="f_year")
with f5:
    round_opts   = ["All"] + [f"Rd {r}" for r in sorted(df["ROUND"].dropna().unique().astype(int))]
    round_filter = st.selectbox("Round", round_opts, key="f_round")
with f6:
    sort_label = st.selectbox("Sort by", list(SORT_MAP.keys()), key="f_sort")
with f7:
    search = st.text_input("Search player", placeholder="e.g. Saquon Barkley", key="f_search")

# ── Apply Filters ──────────────────────────────────────────────────────────────

filtered = df.copy()

if owner_filter != "All":
    filtered = filtered[filtered["OWNER"] == owner_filter]

pos_positions = POSITION_GROUPS.get(pos_filter)
if pos_positions:
    filtered = filtered[filtered["POSITION"].isin(pos_positions)]

if tier_filter != "All":
    filtered = filtered[filtered["CAREER_TIER"] == tier_filter]

if year_filter != "All":
    filtered = filtered[filtered["YEAR"] == int(year_filter)]

if round_filter != "All":
    filtered = filtered[filtered["ROUND"] == int(round_filter.replace("Rd ", ""))]

if search.strip():
    filtered = filtered[
        filtered["PLAYER"].str.contains(search.strip(), case=False, na=False)
    ]

sort_col, sort_asc = SORT_MAP[sort_label]
filtered = filtered.sort_values(sort_col, ascending=sort_asc, na_position="last").reset_index(drop=True)

# ── Results + Roster Table ─────────────────────────────────────────────────────

n     = len(filtered)
label = "player" if n == 1 else "players"
st.markdown(
    f'<div class="tb-results-count">{n} {label} · {sort_label}</div>',
    unsafe_allow_html=True,
)

if n == 0:
    st.markdown(
        '<div class="tb-empty-state">No players match the current filters.</div>',
        unsafe_allow_html=True,
    )
else:
    rows_html = ""
    for rank, (_, p) in enumerate(filtered.iterrows(), start=1):
        rows_html += player_roster_row(
            rank        = rank,
            name        = str(p["PLAYER"]),
            owner       = str(p["OWNER"]),
            position    = str(p["POSITION"]),
            year        = safe_int(p["YEAR"]),
            round_      = safe_int(p["ROUND"]),
            score       = float(p["OVERALL SCORE"]) if not is_score_pending(p["OVERALL SCORE"]) else float("nan"),
            tier        = str(p["CAREER_TIER"]),
            awards_html = award_badges(p.to_dict()),
        )

    st.markdown(
        f'<div class="tb-full-roster">{roster_table_header()}{rows_html}</div>',
        unsafe_allow_html=True,
    )
