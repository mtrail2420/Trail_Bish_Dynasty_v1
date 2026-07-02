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

# ── Player Comparison ─────────────────────────────────────────────────────────

st.markdown(section_header("COMPARE PLAYERS", "Head-to-head stat breakdown"), unsafe_allow_html=True)

st.markdown("""<style>
.pl-cmp-wrap{display:flex;gap:0;background:rgba(10,14,25,.7);border:1px solid rgba(255,255,255,.07);
border-radius:10px;overflow:hidden;margin-bottom:8px;}
.pl-cmp-side{flex:1;padding:22px 24px;}
.pl-cmp-divider{width:1px;background:rgba(255,255,255,.07);flex-shrink:0;align-self:stretch;}
.pl-cmp-owner{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;}
.pl-cmp-owner.matt{color:#2E7DF7;}
.pl-cmp-owner.ryan{color:#E63B3B;}
.pl-cmp-name{font-size:20px;font-weight:900;color:#fff;margin-bottom:4px;line-height:1.15;}
.pl-cmp-meta{font-size:11px;color:#4a6080;margin-bottom:16px;}
.pl-cmp-score-block{display:flex;align-items:baseline;gap:8px;margin-bottom:4px;}
.pl-cmp-score{font-size:42px;font-weight:900;color:#fff;line-height:1;}
.pl-cmp-score.winner{color:#D4AF37;}
.pl-cmp-tier{font-size:10px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;padding:3px 9px;
border-radius:4px;margin-left:4px;}
.pl-cmp-stat-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;
border-bottom:1px solid rgba(255,255,255,.04);}
.pl-cmp-stat-row:last-child{border-bottom:none;}
.pl-cmp-stat-lbl{font-size:10px;color:#4a6080;font-weight:600;}
.pl-cmp-stat-val{font-size:11px;font-weight:800;color:#c0cce0;}
.pl-cmp-stat-val.winner{color:#D4AF37;}
.pl-cmp-awards{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px;}
</style>""", unsafe_allow_html=True)

_cmp_players = (
    df.dropna(subset=["OVERALL SCORE"])
    .sort_values("OVERALL SCORE", ascending=False)["PLAYER"]
    .tolist()
)

_cmp_col1, _cmp_col2 = st.columns(2)
with _cmp_col1:
    cmp_a = st.selectbox("Player A", [""] + _cmp_players, format_func=lambda x: "— Select player A —" if x == "" else x, key="cmp_a")
with _cmp_col2:
    cmp_b = st.selectbox("Player B", [""] + _cmp_players, format_func=lambda x: "— Select player B —" if x == "" else x, key="cmp_b")

_TIER_COLORS_CMP: dict[str, str] = {
    "Legend": "#D4AF37", "Franchise": "#F59E0B",
    "High-End Starter": "#2E7DFF", "Starter": "#22c55e",
    "Contributor": "#94a3b8", "Bust": "#E63B3B",
}
_CMP_AWARD_WEIGHTS = {"MVP": 6, "SB_MVP": 4, "OPOY": 3, "DPOY": 3, "ALL_PRO": 2.5, "SB Win": 2.5, "OROY": 1, "DROY": 1}
_CMP_AWARD_LABELS  = {"MVP": "MVP", "SB_MVP": "SB MVP", "OPOY": "OPOY", "DPOY": "DPOY", "ALL_PRO": "All-Pro", "SB Win": "SB Win", "OROY": "OROY", "DROY": "DROY"}
_CMP_AWARD_ICONS   = {"MVP": "🏆", "SB_MVP": "🌟", "OPOY": "⭐", "DPOY": "🛡️", "ALL_PRO": "🥇", "SB Win": "🏈", "OROY": "🌱", "DROY": "🌱"}

def _cmp_award_total(row) -> float:
    import pandas as pd
    return sum(float(row[c]) * w for c, w in _CMP_AWARD_WEIGHTS.items() if c in row.index and pd.notna(row[c]) and float(row[c]) > 0)

def _cmp_award_chips(row) -> str:
    import pandas as pd
    chips = ""
    for c, w in _CMP_AWARD_WEIGHTS.items():
        if c in row.index and pd.notna(row[c]) and float(row[c]) > 0:
            cnt = int(row[c])
            lbl = f"{_CMP_AWARD_ICONS[c]}&nbsp;{_CMP_AWARD_LABELS[c]}" + (f" ×{cnt}" if cnt > 1 else "")
            chips += f'<div style="font-size:9px;font-weight:700;padding:3px 8px;border-radius:4px;background:rgba(212,175,55,.1);border:1px solid rgba(212,175,55,.2);color:#D4AF37;">{lbl}</div>'
    return chips or '<span style="font-size:10px;color:#4a6080;">No awards</span>'

def _render_cmp_side(row, is_winner: bool) -> str:
    import pandas as pd
    owner     = str(row["OWNER"])
    owner_cls = "matt" if owner == "Matt" else "ryan"
    score     = float(row["OVERALL SCORE"])
    tier      = str(row["CAREER_TIER"])
    tier_col  = _TIER_COLORS_CMP.get(tier, "#fff")
    pos       = str(row["POSITION"])
    year      = int(row["YEAR"])
    rnd       = int(row["ROUND"]) if str(row["ROUND"]) != "nan" else "?"
    aw_pts    = _cmp_award_total(row)
    score_cls = "winner" if is_winner else ""
    aw_cls    = "winner" if is_winner else ""
    stats_html = (
        f'<div class="pl-cmp-stat-row"><span class="pl-cmp-stat-lbl">Position</span><span class="pl-cmp-stat-val">{pos}</span></div>'
        f'<div class="pl-cmp-stat-row"><span class="pl-cmp-stat-lbl">Draft Class</span><span class="pl-cmp-stat-val">{year}</span></div>'
        f'<div class="pl-cmp-stat-row"><span class="pl-cmp-stat-lbl">Round</span><span class="pl-cmp-stat-val">{rnd}</span></div>'
        f'<div class="pl-cmp-stat-row"><span class="pl-cmp-stat-lbl">Award Points</span><span class="pl-cmp-stat-val {aw_cls}">{aw_pts:g}</span></div>'
        f'<div class="pl-cmp-stat-row"><span class="pl-cmp-stat-lbl">Tier</span><span class="pl-cmp-stat-val" style="color:{tier_col};">{tier}</span></div>'
    )
    prod  = safe_str(row.get("PRODUCTION", ""))
    notes = safe_str(row.get("NOTES", ""))
    if prod:
        stats_html += f'<div class="pl-cmp-stat-row"><span class="pl-cmp-stat-lbl">Production</span><span class="pl-cmp-stat-val" style="font-weight:600;font-size:10px;max-width:180px;text-align:right;">{prod[:60]}{"…" if len(prod)>60 else ""}</span></div>'
    return (
        f'<div class="pl-cmp-side">'
        f'<div class="pl-cmp-owner {owner_cls}">{owner}</div>'
        f'<div class="pl-cmp-name">{row["PLAYER"]}</div>'
        f'<div class="pl-cmp-score-block">'
        f'<span class="pl-cmp-score {score_cls}">{score:g}</span>'
        f'<span class="pl-cmp-tier" style="background:rgba(0,0,0,.3);color:{tier_col};border:1px solid {tier_col}33;">{tier}</span>'
        f'</div>'
        f'<div style="height:12px;"></div>'
        + stats_html +
        f'<div class="pl-cmp-awards">{_cmp_award_chips(row)}</div>'
        f'</div>'
    )

if cmp_a and cmp_b and cmp_a != cmp_b:
    _ra = df[df["PLAYER"] == cmp_a].iloc[0]
    _rb = df[df["PLAYER"] == cmp_b].iloc[0]
    _sa = float(_ra["OVERALL SCORE"])
    _sb = float(_rb["OVERALL SCORE"])
    _a_wins = _sa > _sb
    _b_wins = _sb > _sa
    st.markdown(
        '<div class="pl-cmp-wrap">'
        + _render_cmp_side(_ra, _a_wins)
        + '<div class="pl-cmp-divider"></div>'
        + _render_cmp_side(_rb, _b_wins)
        + '</div>',
        unsafe_allow_html=True,
    )
elif cmp_a and cmp_b and cmp_a == cmp_b:
    st.markdown(
        '<div style="color:#4a6080;font-size:12px;padding:10px;">Select two different players to compare.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div style="color:#4a6080;font-size:12px;padding:10px;">Select two players above to see a head-to-head breakdown.</div>',
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

# ── Flex Card ──────────────────────────────────────────────────────────────────
# Screenshot-ready card — send to Ryan mid-argument.

st.markdown(section_header("FLEX CARD", "Screenshot-ready · send mid-argument"), unsafe_allow_html=True)

st.markdown("""<style>
.fc-wrap{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;}
.fc-card{width:320px;background:#070B13;border:1px solid rgba(255,255,255,.12);
border-radius:14px;overflow:hidden;flex-shrink:0;}
.fc-card-header{padding:14px 18px 10px;border-bottom:1px solid rgba(255,255,255,.07);}
.fc-branding{font-size:8px;font-weight:800;letter-spacing:3px;text-transform:uppercase;
color:#4a6080;margin-bottom:4px;}
.fc-card-title{font-size:10px;font-weight:700;color:#6070a0;letter-spacing:1px;}
.fc-card-body{padding:18px 18px 20px;}
.fc-player-name{font-size:22px;font-weight:900;color:#fff;line-height:1.1;margin-bottom:6px;}
.fc-owner-pill{display:inline-block;font-size:8px;font-weight:800;letter-spacing:1.5px;
text-transform:uppercase;padding:3px 9px;border-radius:4px;margin-bottom:12px;}
.fc-owner-pill.matt{background:rgba(46,125,247,.15);color:#2E7DF7;border:1px solid rgba(46,125,247,.3);}
.fc-owner-pill.ryan{background:rgba(230,59,59,.15);color:#E63B3B;border:1px solid rgba(230,59,59,.3);}
.fc-score-line{display:flex;align-items:baseline;gap:10px;margin-bottom:6px;}
.fc-score-big{font-size:52px;font-weight:900;color:#fff;line-height:1;}
.fc-score-label{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#4a6080;}
.fc-tier-badge{display:inline-block;font-size:9px;font-weight:800;letter-spacing:1.5px;
text-transform:uppercase;padding:4px 11px;border-radius:5px;margin-bottom:12px;}
.fc-stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;}
.fc-stat{background:rgba(255,255,255,.04);border-radius:6px;padding:8px 10px;}
.fc-stat-val{font-size:14px;font-weight:800;color:#c0cce0;}
.fc-stat-lbl{font-size:8px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#4a6080;margin-top:2px;}
.fc-awards-row{display:flex;flex-wrap:wrap;gap:5px;}
.fc-award-chip{font-size:9px;font-weight:700;padding:3px 8px;border-radius:4px;
background:rgba(212,175,55,.1);border:1px solid rgba(212,175,55,.2);color:#D4AF37;}
.fc-footer{background:rgba(0,0,0,.3);padding:8px 18px;display:flex;
justify-content:space-between;align-items:center;}
.fc-footer-brand{font-size:8px;font-weight:800;letter-spacing:2px;
text-transform:uppercase;color:#4a6080;}
.fc-vs-card{width:320px;background:#070B13;border:1px solid rgba(255,255,255,.12);
border-radius:14px;overflow:hidden;flex-shrink:0;}
.fc-vs-top{padding:14px 18px 8px;border-bottom:1px solid rgba(255,255,255,.07);}
.fc-vs-title{font-size:8px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#4a6080;}
.fc-vs-body{padding:14px 18px;}
.fc-vs-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;
border-bottom:1px solid rgba(255,255,255,.04);}
.fc-vs-row:last-child{border-bottom:none;}
.fc-vs-lbl{font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#4a6080;
width:80px;text-align:center;flex-shrink:0;}
.fc-vs-matt{font-size:12px;font-weight:800;color:#2E7DF7;flex:1;text-align:right;}
.fc-vs-ryan{font-size:12px;font-weight:800;color:#E63B3B;flex:1;}
.fc-vs-divider-mid{width:1px;height:18px;background:rgba(255,255,255,.07);flex-shrink:0;margin:0 6px;}
.fc-vs-winner{color:#D4AF37 !important;}
.fc-vs-owner-hdr{font-size:10px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;
padding:8px 12px 6px;text-align:center;}
.fc-vs-owner-hdr.matt{color:#2E7DF7;}
.fc-vs-owner-hdr.ryan{color:#E63B3B;}
</style>""", unsafe_allow_html=True)

_fc_tab1, _fc_tab2 = st.tabs(["Single Player Card", "Head-to-Head Card"])

# ─── Single Player Card ────────────────────────────────────────────────────────
with _fc_tab1:
    _fc_all = df.sort_values("OVERALL SCORE", ascending=False, na_position="last")["PLAYER"].tolist()
    _fc_sel = st.selectbox("Select player for card", [""] + _fc_all,
                           format_func=lambda x: "— Choose a player —" if x == "" else x,
                           key="fc_single")
    if _fc_sel:
        _fp = df[df["PLAYER"] == _fc_sel].iloc[0]
        _fp_owner  = str(_fp["OWNER"])
        _fp_cls    = "matt" if _fp_owner == "Matt" else "ryan"
        _fp_score  = float(_fp["OVERALL SCORE"]) if not is_score_pending(_fp["OVERALL SCORE"]) else None
        _fp_tier   = str(_fp["CAREER_TIER"])
        _fp_tc     = _TIER_COLORS_CMP.get(_fp_tier, "#fff")
        _fp_aw     = _cmp_award_chips(_fp)
        _fp_rd     = int(_fp["ROUND"]) if str(_fp["ROUND"]) != "nan" else "?"
        _fp_score_html = f'<div class="fc-score-big">{_fp_score:g}</div>' if _fp_score else '<div class="fc-score-big" style="color:#4a6080;">TBD</div>'
        st.markdown(
            f'<div class="fc-card">'
            f'  <div class="fc-card-header">'
            f'    <div class="fc-branding">🏈 Trail &amp; Bish Dynasty</div>'
            f'    <div class="fc-card-title">PLAYER CARD · {int(_fp["YEAR"])} DRAFT CLASS</div>'
            f'  </div>'
            f'  <div class="fc-card-body">'
            f'    <div class="fc-player-name">{_fc_sel}</div>'
            f'    <div class="fc-owner-pill {_fp_cls}">{_fp_owner}</div>'
            f'    <div class="fc-score-line">'
            f'      {_fp_score_html}'
            f'      <div><div class="fc-score-label">Overall Score</div></div>'
            f'    </div>'
            f'    <div class="fc-tier-badge" style="background:rgba(0,0,0,.3);color:{_fp_tc};border:1px solid {_fp_tc}44;">{_fp_tier}</div>'
            f'    <div class="fc-stat-grid">'
            f'      <div class="fc-stat"><div class="fc-stat-val">{str(_fp["POSITION"])}</div><div class="fc-stat-lbl">Position</div></div>'
            f'      <div class="fc-stat"><div class="fc-stat-val">Rd {_fp_rd}</div><div class="fc-stat-lbl">Draft Round</div></div>'
            f'    </div>'
            f'    <div class="fc-score-label" style="margin-bottom:6px;">Awards</div>'
            f'    <div class="fc-awards-row">{_fp_aw}</div>'
            f'  </div>'
            f'  <div class="fc-footer">'
            f'    <span class="fc-footer-brand">Trail &amp; Bish Boys Dynasty</span>'
            f'    <span class="fc-footer-brand">2007–2026</span>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.caption("Screenshot the card above to share it.")

# ─── Head-to-Head Card ─────────────────────────────────────────────────────────
with _fc_tab2:
    _fc_h2h_opts = df.dropna(subset=["OVERALL SCORE"]).sort_values("OVERALL SCORE", ascending=False)["PLAYER"].tolist()
    _hh1, _hh2 = st.columns(2)
    with _hh1:
        _fc_h2h_a = st.selectbox("Matt's player", [""] + _fc_h2h_opts,
                                  format_func=lambda x: "— Select —" if x == "" else x,
                                  key="fc_h2h_a")
    with _hh2:
        _fc_h2h_b = st.selectbox("Ryan's player", [""] + _fc_h2h_opts,
                                  format_func=lambda x: "— Select —" if x == "" else x,
                                  key="fc_h2h_b")

    if _fc_h2h_a and _fc_h2h_b:
        _fa = df[df["PLAYER"] == _fc_h2h_a].iloc[0]
        _fb = df[df["PLAYER"] == _fc_h2h_b].iloc[0]
        _sa2 = float(_fa["OVERALL SCORE"]) if not is_score_pending(_fa["OVERALL SCORE"]) else 0.0
        _sb2 = float(_fb["OVERALL SCORE"]) if not is_score_pending(_fb["OVERALL SCORE"]) else 0.0

        def _vs_val(row, col):
            import pandas as pd
            v = row.get(col, None)
            if v is None or (hasattr(v, '__class__') and str(v) == "nan"): return "—"
            try: return str(int(float(str(v)))) if float(str(v)) == int(float(str(v))) else f"{float(str(v)):.1f}"
            except: return str(v)

        _vs_rows = [
            ("Overall Score",
             f'{_sa2:g}' if _sa2 else "TBD",
             f'{_sb2:g}' if _sb2 else "TBD",
             _sa2 > _sb2, _sb2 > _sa2),
            ("Position",  str(_fa["POSITION"]), str(_fb["POSITION"]), False, False),
            ("Draft Year", str(int(_fa["YEAR"])), str(int(_fb["YEAR"])), False, False),
            ("Round",      f'Rd {_vs_val(_fa, "ROUND")}', f'Rd {_vs_val(_fb, "ROUND")}', False, False),
            ("Award Pts",
             f'{_cmp_award_total(_fa):g}', f'{_cmp_award_total(_fb):g}',
             _cmp_award_total(_fa) > _cmp_award_total(_fb),
             _cmp_award_total(_fb) > _cmp_award_total(_fa)),
            ("Tier",       str(_fa["CAREER_TIER"]), str(_fb["CAREER_TIER"]), False, False),
        ]
        _vs_rows_html = (
            f'<div class="fc-vs-row">'
            f'<div class="fc-vs-owner-hdr matt" style="flex:1;">Matt</div>'
            f'<div class="fc-vs-lbl">⚔️</div>'
            f'<div class="fc-vs-owner-hdr ryan" style="flex:1;text-align:right;">Ryan</div>'
            f'</div>'
        )
        for _lbl, _va, _vb, _a_w, _b_w in _vs_rows:
            _va_cls = "fc-vs-matt fc-vs-winner" if _a_w else "fc-vs-matt"
            _vb_cls = "fc-vs-ryan fc-vs-winner" if _b_w else "fc-vs-ryan"
            _vs_rows_html += (
                f'<div class="fc-vs-row">'
                f'<div class="{_va_cls}">{_va}</div>'
                f'<div class="fc-vs-divider-mid"></div>'
                f'<div class="fc-vs-lbl">{_lbl}</div>'
                f'<div class="fc-vs-divider-mid"></div>'
                f'<div class="{_vb_cls}" style="text-align:right;">{_vb}</div>'
                f'</div>'
            )
        st.markdown(
            f'<div class="fc-vs-card">'
            f'  <div class="fc-vs-top">'
            f'    <div class="fc-vs-title">🏈 Trail &amp; Bish Dynasty · Head-to-Head</div>'
            f'  </div>'
            f'  <div class="fc-vs-body">{_vs_rows_html}</div>'
            f'  <div class="fc-footer">'
            f'    <span class="fc-footer-brand">Trail &amp; Bish Boys Dynasty</span>'
            f'    <span class="fc-footer-brand">2007–2026</span>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.caption("Screenshot the card above and send it.")
