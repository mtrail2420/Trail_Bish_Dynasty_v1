import streamlit as st

from core.data_loader import load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import (
    compute_league_stats,
    compute_owner_stats,
    score_leader,
    rank_players,
    compute_class_stats,
    class_grade,
    compute_award_totals,
    compute_mount_rushmore,
    compute_all_franchise,
    compute_hall_of_fame,
    compute_greatest_classes,
    compute_legacy_moments,
)
from core.utils import safe_int, fmt_score
from core.components import (
    section_header,
    owner_chip,
    tier_badge,
    position_chip,
    award_badges,
    grade_badge,
    winner_badge,
    legacy_leaderboard_row,
    exhibit_card,
    award_count_tile,
    timeline_node,
    legacy_spotlight_card,
)

st.set_page_config(
    page_title="Legacy Center — Trail & Bish Dynasty",
    page_icon="🏛️",
    layout="wide",
)

render_sidebar(active="Legacy")

# Museum background — warm near-black replaces the standard blue-navy gradient
st.markdown(
    "<style>.stApp{"
    "background:radial-gradient(circle at top,#130900 0%,#0A0600 40%,#040200 100%)"
    "!important}</style>",
    unsafe_allow_html=True,
)

# ── Guard ─────────────────────────────────────────────────────────────────────

if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────

df = load_players()

ls           = compute_league_stats(df)
matt_s       = compute_owner_stats(df, "Matt")
ryan_s       = compute_owner_stats(df, "Ryan")
leader, _    = score_leader(matt_s, ryan_s)
ranked       = rank_players(df)
scored_all   = ranked[ranked["RANK"] > 0].reset_index(drop=True)

award_totals  = compute_award_totals(df)
rushmore      = compute_mount_rushmore(df)
all_franchise = compute_all_franchise(df)
hof_df        = compute_hall_of_fame(df)
greatest_cls  = compute_greatest_classes(df, 5)
moments       = compute_legacy_moments(df)
cs            = compute_class_stats(df)

# Derived scalars
matt_sb   = int(df[df["OWNER"] == "Matt"]["SB Win"].fillna(0).sum())
ryan_sb   = int(df[df["OWNER"] == "Ryan"]["SB Win"].fillna(0).sum())
matt_avg  = matt_s["avg_score"]
ryan_avg  = ryan_s["avg_score"]
top1      = scored_all.iloc[0]

# Timeline winner + label per year
_year_winner: dict[int, str] = {}
_year_grade:  dict[int, str] = {}
for year in sorted(df["YEAR"].unique()):
    yr = cs[cs["YEAR"] == year]
    m_row = yr[yr["OWNER"] == "Matt"]
    r_row = yr[yr["OWNER"] == "Ryan"]
    m_avg = float(m_row["avg_score"].values[0]) if len(m_row) and int(m_row["scored"].values[0]) > 0 else 0.0
    r_avg = float(r_row["avg_score"].values[0]) if len(r_row) and int(r_row["scored"].values[0]) > 0 else 0.0
    if m_avg > 0 or r_avg > 0:
        _year_winner[year] = "Matt" if m_avg > r_avg else "Ryan" if r_avg > m_avg else "Tie"
        _year_grade[year]  = class_grade((m_avg + r_avg) / 2)
    else:
        _year_winner[year] = "Pending"

_best_class_year = int(
    cs[cs["scored"] > 0].groupby("YEAR")["avg_score"].mean().idxmax()
)
_min_year = int(df["YEAR"].min())
_max_year = int(df["YEAR"].max())

# =============================================================================
# SECTION 1 — HERO WELCOME HALL
# =============================================================================

st.markdown(
    f"""
<div class="tb-lc-hero">
  <div class="tb-lc-banner tb-lc-banner-matt">
    <div class="tb-lc-banner-owner-name">MATT</div>
    <div class="tb-lc-banner-dynasty">DYNASTY</div>
    <div class="tb-lc-banner-est">EST. 2007</div>
    <div class="tb-lc-banner-icon">🏆</div>
    <div class="tb-lc-banner-count">{matt_sb}</div>
    <div class="tb-lc-banner-count-label">SB RINGS</div>
  </div>

  <div class="tb-lc-hero-center">
    <div class="tb-lc-welcome-line">★ WELCOME TO THE ★</div>
    <div class="tb-lc-hero-title">LEGACY CENTER</div>
    <div class="tb-lc-hero-subtitle">WHERE BOYS BECOME LEGENDS</div>
    <div class="tb-lc-trophy-pedestal">
      <div class="tb-lc-trophy-glow"></div>
      <div class="tb-lc-hero-trophy">🏆</div>
    </div>
    <div class="tb-lc-hero-tagline">
      Every pick. Every play. Every championship.<br>
      The full history of the greatest dynasty rivalry ever created.
    </div>
    <div class="tb-lc-explore-cue">▼ EXPLORE THE LEGACY ▼</div>
  </div>

  <div class="tb-lc-banner tb-lc-banner-ryan">
    <div class="tb-lc-banner-owner-name">RYAN</div>
    <div class="tb-lc-banner-dynasty">DYNASTY</div>
    <div class="tb-lc-banner-est">EST. 2007</div>
    <div class="tb-lc-banner-icon">🏆</div>
    <div class="tb-lc-banner-count">{ryan_sb}</div>
    <div class="tb-lc-banner-count-label">SB RINGS</div>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)



# ── Legacy Facts ──────────────────────────────────────────────────────────────
moments_html = ""
for m in moments:
    owner = m["owner"]
    dot_cls = (
        "tb-lc-moment-dot-matt" if owner == "Matt"
        else "tb-lc-moment-dot-ryan" if owner == "Ryan"
        else "tb-lc-moment-dot-dynasty"
    )
    moments_html += (
        f'<div class="tb-lc-moment">'
        f'<div class="tb-lc-moment-dot {dot_cls}"></div>'
        f'<div class="tb-lc-moment-text">{m["text"]}</div>'
        f'</div>'
    )

_award_display_items = [
    ("🏆", award_totals.get("MVP",    0), "MVP"),
    ("⭐", award_totals.get("OPOY",   0), "OPOY"),
    ("🛡️", award_totals.get("DPOY",  0), "DPOY"),
    ("🌱", award_totals.get("OROY",   0), "OROY"),
    ("🌱", award_totals.get("DROY",   0), "DROY"),
    ("🥇", award_totals.get("ALL_PRO",0), "ALL-PRO"),
    ("🏈", award_totals.get("SB Win", 0), "SB WINS"),
    ("🌟", award_totals.get("SB_MVP", 0), "SB MVP"),
]
_award_tiles_html = '<div class="tb-award-grid tb-award-grid-2col">'
for _ico, _cnt, _lbl in _award_display_items:
    _award_tiles_html += award_count_tile(_ico, _cnt, _lbl)
_award_tiles_html += "</div>"

_pulse_items = [
    (str(ls["total_players"]),          "TOTAL PLAYERS",    "#D4AF37"),
    (str(ls["draft_classes"]),           "DRAFT CLASSES",    "#D4AF37"),
    (str(ls["franchise_total"]),         "FRANCHISE",        "#D4AF37"),
    (f"{matt_s['avg_score']:.1f}",       "MATT AVG",         "#2E7DF7"),
    (f"{ls['avg_score']:.1f}",           "LEAGUE AVG",       "#D4AF37"),
    (f"{ryan_s['avg_score']:.1f}",       "RYAN AVG",         "#E63B3B"),
]
_pulse_html = '<div class="tb-lc-pulse-grid">'
for _pv, _pl, _pc in _pulse_items:
    _pulse_html += (
        f'<div class="tb-lc-pulse-tile">'
        f'<div class="tb-lc-pulse-val" style="color:{_pc};">{_pv}</div>'
        f'<div class="tb-lc-pulse-lbl">{_pl}</div>'
        f'</div>'
    )
_pulse_html += '</div>'

_lf_col, _da_col = st.columns([1.5, 1])
with _lf_col:
    st.markdown(
        f'<div class="tb-lc-rivalry-box">'
        f'<div class="tb-lc-panel-title">📰 LEGACY FACTS</div>'
        f'<div class="tb-lc-moments-wrap">{moments_html}</div>'
        f'<div class="tb-lc-pulse-divider">DYNASTY PULSE</div>'
        f'{_pulse_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
with _da_col:
    st.markdown(
        f'<div class="tb-lc-rivalry-box">'
        f'<div class="tb-lc-panel-title">🏆 DYNASTY AWARDS</div>'
        f'{_award_tiles_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

# =============================================================================
# SECTION 2 — EXHIBIT CARDS
# =============================================================================

st.markdown(
    '<div class="tb-lc-divider"><span>★ EXPLORE THE LEGACY EXHIBITS ★</span></div>',
    unsafe_allow_html=True,
)

_cards = [
    ("🐐", "GOAT RACE",         "The all-time chase",       "goat-race"),
    ("🗿", "MOUNT RUSHMORE",    "4 greatest per dynasty",   "mount-rushmore"),
    ("🏆", "LEGACY HALL",       "The Franchise legends",    "legacy-hall"),
    ("📖", "RECORD BOOK",       "All-time dynasty records", "record-book"),
    ("🏈", "ALL-FRANCHISE",     "Best at each position",    "all-franchise"),
    ("📋", "GREATEST CLASSES",  "Top 5 draft hauls",        "greatest-classes"),
    ("💀", "HALL OF SHAME",     "The dynasty busts",        "hall-of-shame"),
    ("⏳", "DYNASTY TIMELINE",  "Every era, every class",   "dynasty-timeline"),
]

cards_html = '<div class="tb-exhibit-grid">'
for icon, title, sub, anchor in _cards:
    cards_html += exhibit_card(icon, title, sub, is_available=True, anchor=anchor)
cards_html += "</div>"

st.markdown(cards_html, unsafe_allow_html=True)

# =============================================================================
# SECTION 3 — THE LOBBY (4 data panels)
# =============================================================================

st.markdown(
    '<div class="tb-lc-divider"><span>★ THE LOBBY ★</span></div>',
    unsafe_allow_html=True,
)

lc1, lc2, lc3 = st.columns([1.6, 2.0, 1.2])

# ── GOAT Race Leaders ──────────────────────────────────────────────────────
with lc1:
    top5_html = (
        '<div class="tb-lc-room-header">🐐 GOAT RACE LEADERS</div>'
        '<div class="tb-lc-room-sub">ALL-TIME DYNASTY TOP 5</div>'
    )
    for _, p in scored_all.head(5).iterrows():
        top5_html += legacy_leaderboard_row(
            rank  = int(p["RANK"]),
            name  = str(p["PLAYER"]),
            owner = str(p["OWNER"]),
            score = float(p["OVERALL SCORE"]),
        )
    st.markdown(top5_html, unsafe_allow_html=True)

# ── Greatest Draft Classes ─────────────────────────────────────────────────
with lc2:
    classes_html = (
        '<div class="tb-lc-room-header">📋 GREATEST CLASSES</div>'
        '<div class="tb-lc-room-sub">TOP 5 BY COMBINED AVG SCORE</div>'
    )
    for gc in greatest_cls:
        gb = grade_badge(gc["grade"])
        wb = winner_badge(gc["winner"])
        classes_html += (
            f'<div class="tb-lc-class-row">'
            f'<div class="tb-lc-class-rank">{gc["rank"]}</div>'
            f'<div class="tb-lc-class-year">{gc["year"]}</div>'
            f'<div class="tb-lc-class-avgs">'
            f'Matt {gc["matt_avg"]:.1f} · Ryan {gc["ryan_avg"]:.1f}'
            f'</div>'
            f'{gb}&nbsp;{wb}'
            f'</div>'
        )
    st.markdown(classes_html, unsafe_allow_html=True)

# ── Legacy Spotlight ───────────────────────────────────────────────────────
with lc3:
    sp = top1
    sp_awards_html = award_badges(sp.to_dict())
    sp_facts = [
        f"Production: {sp['PRODUCTION']}" if str(sp.get("PRODUCTION", "")) not in ("nan", "") else None,
        f"Longevity: {sp['LONGEVITY']}" if str(sp.get("LONGEVITY", "")) not in ("nan", "") else None,
        f"All-Pro: {safe_int(sp['ALL_PRO'])}×" if safe_int(sp.get("ALL_PRO", 0)) > 0 else None,
        f"SB Rings: {safe_int(sp['SB Win'])}" if safe_int(sp.get("SB Win", 0)) > 0 else None,
    ]
    sp_facts = [f for f in sp_facts if f]
    st.markdown(
        legacy_spotlight_card(
            name      = str(sp["PLAYER"]),
            owner     = str(sp["OWNER"]),
            position  = str(sp["POSITION"]),
            year      = safe_int(sp["YEAR"]),
            round_    = safe_int(sp["ROUND"]),
            score     = float(sp["OVERALL SCORE"]),
            tier      = str(sp["CAREER_TIER"]),
            facts     = sp_facts[:4],
            awards_html = sp_awards_html,
        ),
        unsafe_allow_html=True,
    )

# =============================================================================
# SECTION 4 — DYNASTY EXHIBIT ROOMS
# =============================================================================

st.markdown(
    '<div class="tb-lc-divider"><span>★ DYNASTY EXHIBIT ROOMS ★</span></div>',
    unsafe_allow_html=True,
)

# ── 4A · GOAT Race — full top 20 ──────────────────────────────────────────
goat_html = (
    '<div id="goat-race" class="tb-lc-room">'
    '<div class="tb-lc-room-header">🐐 GOAT RACE — ALL-TIME LEADERBOARD</div>'
    '<div class="tb-lc-room-sub">TOP 20 PLAYERS BY OVERALL SCORE</div>'
)
for _, p in scored_all.head(20).iterrows():
    goat_html += legacy_leaderboard_row(
        rank  = int(p["RANK"]),
        name  = str(p["PLAYER"]),
        owner = str(p["OWNER"]),
        score = float(p["OVERALL SCORE"]),
    )
goat_html += "</div>"
st.markdown(goat_html, unsafe_allow_html=True)

# ── 4B · Mount Rushmore ───────────────────────────────────────────────────
st.markdown('<div id="mount-rushmore"></div>', unsafe_allow_html=True)
r_a, r_b = st.columns(2)

numerals = ["I", "II", "III", "IV"]
for col, owner in [(r_a, "Matt"), (r_b, "Ryan")]:
    with col:
        room_html = (
            f'<div class="tb-lc-room">'
            f'<div class="tb-lc-room-header">🗿 MOUNT RUSHMORE</div>'
            f'<div class="tb-lc-room-sub">{owner.upper()} DYNASTY · TOP 4 ALL-TIME</div>'
            f'<div class="tb-rushmore-grid">'
        )
        for i, p in enumerate(rushmore[owner]):
            pos_val = str(p.get("POSITION", ""))
            yr_val  = safe_int(p.get("YEAR", 0))
            room_html += (
                f'<div class="tb-rushmore-card">'
                f'<div class="tb-rushmore-rank">{numerals[i]}</div>'
                f'<div class="tb-rushmore-name">{p["PLAYER"]}</div>'
                f'<div class="tb-rushmore-score">{fmt_score(p.get("OVERALL SCORE"))}</div>'
                f'<div class="tb-rushmore-meta">{pos_val} · {yr_val}</div>'
                f'</div>'
            )
        room_html += "</div></div>"
        st.markdown(room_html, unsafe_allow_html=True)

# ── 4C · All-Franchise Teams ──────────────────────────────────────────────
st.markdown('<div id="all-franchise"></div>', unsafe_allow_html=True)
af_a, af_b = st.columns(2)

for col, owner in [(af_a, "Matt"), (af_b, "Ryan")]:
    with col:
        af_html = (
            f'<div class="tb-lc-room">'
            f'<div class="tb-lc-room-header">🏈 ALL-FRANCHISE</div>'
            f'<div class="tb-lc-room-sub">{owner.upper()} — BEST PER POSITION</div>'
            f'<div class="tb-af-table">'
        )
        for pos_label, entry in all_franchise.items():
            player = entry.get(owner)
            if player:
                name_str = str(player.get("PLAYER", "—"))
                sc_str   = fmt_score(player.get("OVERALL SCORE"))
                tier_str = str(player.get("CAREER_TIER", ""))
                af_html += (
                    f'<div class="tb-af-row">'
                    f'<div class="tb-af-pos">{pos_label}</div>'
                    f'<div class="tb-af-info">'
                    f'<div class="tb-af-name">{name_str}</div>'
                    f'<div class="tb-af-score">{sc_str} · {tier_badge(tier_str)}</div>'
                    f'</div>'
                    f'</div>'
                )
            else:
                af_html += (
                    f'<div class="tb-af-row">'
                    f'<div class="tb-af-pos">{pos_label}</div>'
                    f'<div class="tb-af-info">'
                    f'<div class="tb-af-name" style="color:#4A3810">No scored players</div>'
                    f'</div>'
                    f'</div>'
                )
        af_html += "</div></div>"
        st.markdown(af_html, unsafe_allow_html=True)

# ── 4D · Greatest Draft Classes — full room ───────────────────────────────
gc_room_html = (
    '<div id="greatest-classes" class="tb-lc-room">'
    '<div class="tb-lc-room-header">📋 GREATEST DRAFT CLASSES</div>'
    '<div class="tb-lc-room-sub">TOP 5 ALL-TIME BY COMBINED AVERAGE SCORE</div>'
)
for gc in greatest_cls:
    gc_room_html += (
        f'<div class="tb-lc-class-row">'
        f'<div class="tb-lc-class-rank">#{gc["rank"]}</div>'
        f'<div class="tb-lc-class-year">{gc["year"]}</div>'
        f'<div class="tb-lc-class-avgs">'
        f'Combined avg {gc["combined_avg"]:.1f} · '
        f'<span class="tb-matt">Matt {gc["matt_avg"]:.1f}</span> · '
        f'<span class="tb-ryan">Ryan {gc["ryan_avg"]:.1f}</span>'
        f'</div>'
        f'{grade_badge(gc["grade"])}&nbsp;{winner_badge(gc["winner"])}'
        f'</div>'
    )
gc_room_html += "</div>"
st.markdown(gc_room_html, unsafe_allow_html=True)

# ── 4E · Hall of Shame ────────────────────────────────────────────────────
busts = (
    df[(df["CAREER_TIER"] == "Bust")]
    .dropna(subset=["OVERALL SCORE"])
    .sort_values("OVERALL SCORE")
    .reset_index(drop=True)
)
shame_html = (
    '<div id="hall-of-shame" class="tb-lc-room">'
    '<div class="tb-lc-room-header">💀 HALL OF SHAME</div>'
    '<div class="tb-lc-room-sub">THE DYNASTY BUSTS — LOWEST OVERALL SCORES</div>'
)
for i, (_, p) in enumerate(busts.iterrows(), 1):
    shame_html += (
        f'<div class="tb-shame-row">'
        f'<div class="tb-shame-rank">#{i}</div>'
        f'<div class="tb-shame-name">{p["PLAYER"]}</div>'
        f'<div class="tb-shame-pos">{p["POSITION"]}</div>'
        f'<div class="tb-shame-owner">{owner_chip(str(p["OWNER"]))}</div>'
        f'<div class="tb-shame-score">{fmt_score(p["OVERALL SCORE"])}</div>'
        f'</div>'
    )
shame_html += "</div>"
st.markdown(shame_html, unsafe_allow_html=True)

# ── 4F · Legacy Hall — all 48 Franchise players ───────────────────────────
hof_html = (
    '<div id="legacy-hall" class="tb-lc-room">'
    '<div class="tb-lc-room-header">🏆 LEGACY HALL</div>'
    f'<div class="tb-lc-room-sub">ALL {len(hof_df)} FRANCHISE-TIER PLAYERS — THE DYNASTY LEGENDS</div>'
    '<div class="tb-hof-grid">'
)
for _, p in hof_df.iterrows():
    hof_html += (
        f'<div class="tb-hof-card">'
        f'<div class="tb-hof-name">{p["PLAYER"]}</div>'
        f'<div class="tb-hof-meta">'
        f'{owner_chip(str(p["OWNER"]))}&nbsp;{position_chip(str(p["POSITION"]))}'
        f'</div>'
        f'<div class="tb-hof-score">{fmt_score(p["OVERALL SCORE"])}</div>'
        f'</div>'
    )
hof_html += "</div></div>"
st.markdown(hof_html, unsafe_allow_html=True)

# ── 4G · Record Book ──────────────────────────────────────────────────────
# All-time records computed from players
_rec_top_scorer = scored_all.iloc[0]
_rec_worst      = busts.iloc[0] if len(busts) else None
_all_pro_col    = df["ALL_PRO"].fillna(0)
_rec_most_ap_idx = int(_all_pro_col.idxmax())
_rec_most_ap    = df.loc[_rec_most_ap_idx]
_sb_col         = df["SB Win"].fillna(0)
_rec_most_sb_idx = int(_sb_col.idxmax())
_rec_most_sb    = df.loc[_rec_most_sb_idx]

records = [
    ("ALL-TIME HIGH SCORE",
     fmt_score(_rec_top_scorer['OVERALL SCORE']),
     f"{_rec_top_scorer['PLAYER']} · {_rec_top_scorer['OWNER']} · {_rec_top_scorer['POSITION']}"),
    ("ALL-TIME LOW SCORE",
     fmt_score(_rec_worst['OVERALL SCORE']) if _rec_worst is not None else "—",
     f"{_rec_worst['PLAYER']} · {_rec_worst['OWNER']}" if _rec_worst is not None else "—"),
    ("MOST ALL-PRO SEASONS",
     f"{safe_int(_rec_most_ap['ALL_PRO'])}×",
     f"{_rec_most_ap['PLAYER']} · {_rec_most_ap['OWNER']}"),
    ("MOST SB RINGS",
     f"{safe_int(_rec_most_sb['SB Win'])}",
     f"{_rec_most_sb['PLAYER']} · {_rec_most_sb['OWNER']}"),
    ("GREATEST CLASS AVG",
     f"{greatest_cls[0]['combined_avg']:.1f}",
     f"{greatest_cls[0]['year']} Draft · Grade {greatest_cls[0]['grade']}"),
    ("TOTAL DYNASTY SB RINGS",
     f"{award_totals.get('SB Win', 0)}",
     f"Matt {matt_sb} · Ryan {ryan_sb}"),
]

rec_html = (
    '<div id="record-book" class="tb-lc-room">'
    '<div class="tb-lc-room-header">📖 RECORD BOOK</div>'
    '<div class="tb-lc-room-sub">ALL-TIME DYNASTY RECORDS</div>'
    '<div class="tb-record-grid">'
)
for lbl, val, detail in records:
    rec_html += (
        f'<div class="tb-record-card">'
        f'<div class="tb-record-label">{lbl}</div>'
        f'<div class="tb-record-val">{val}</div>'
        f'<div class="tb-record-detail">{detail}</div>'
        f'</div>'
    )
rec_html += "</div></div>"
st.markdown(rec_html, unsafe_allow_html=True)

# =============================================================================
# SECTION 5 — DYNASTY TIMELINE
# =============================================================================

st.markdown(
    '<div id="dynasty-timeline" class="tb-lc-divider"><span>★ DYNASTY TIMELINE ★</span></div>',
    unsafe_allow_html=True,
)

_special_labels: dict[int, str] = {
    _min_year:        "The Beginning",
    _best_class_year: "Greatest Class",
    _max_year:        "The Future",
}

timeline_html = '<div class="tb-timeline-wrap"><div class="tb-timeline-track">'
for year in sorted(df["YEAR"].unique()):
    winner  = _year_winner.get(year, "Pending")
    grade   = _year_grade.get(year, "—")
    is_mile = year in (_min_year, _best_class_year)
    label   = _special_labels.get(year, f"Grade {grade}" if grade != "—" else "Pending")
    timeline_html += timeline_node(year, label, winner, is_milestone=is_mile)

timeline_html += "</div></div>"
st.markdown(timeline_html, unsafe_allow_html=True)
