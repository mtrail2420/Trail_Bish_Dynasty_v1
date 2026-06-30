"""
pages/Analytics.py — Analytics (Fire 5, Phase 1)
Bloomberg terminal identity. 7 real-data stat panels.
"""
import streamlit as st

from core.data_loader import load_players, load_man_status, workbook_exists
from core.sidebar import render_sidebar
from core.stats import (
    compute_league_stats,
    compute_owner_stats,
    compute_ms_summary,
    POSITION_GROUPS,
)
from core.components import page_header

st.set_page_config(
    page_title="Analytics — Trail & Bish Dynasty",
    page_icon="📈",
    layout="wide",
)

render_sidebar(active="Analytics")

# ── Analytics-scoped token + CSS injection ─────────────────────────────────────
# --an-teal / --an-teal-bright / --an-teal-deep / --an-glow / --an-success /
# --an-warning / --an-danger / --an-info / --an-shadow-card / --an-shadow-elevated
# are ANALYTICS-SCOPED TOKENS injected here intentionally.
# ISOLATION RULE: these MUST remain in this file as the sole injector.
# DO NOT move to :root, theme.css, or any shared init — the Analytics Bloomberg
# terminal palette must not bleed to other pages.
# See Analytics.md §2a. Same isolation pattern as ManStatus.py / WarRoom.py.
st.markdown("""<style>
.stApp{
--an-teal:#18C2A8;--an-teal-bright:#2FE0C4;--an-teal-deep:#0E8A78;
--an-glow:0 0 18px rgba(24,194,168,.24);
--an-success:#3ED598;--an-warning:#F6C453;--an-danger:#FF6B6B;--an-info:#56B7FF;
--an-shadow-card:0 10px 30px rgba(0,0,0,.28);--an-shadow-elevated:0 18px 45px rgba(0,0,0,.34);
}
.an-panel{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;
padding:22px 24px;box-shadow:var(--an-shadow-card);box-sizing:border-box;}
.an-label{font-size:9px;font-weight:800;letter-spacing:2.5px;color:var(--an-teal);
text-transform:uppercase;border-bottom:1px solid var(--border);padding-bottom:10px;margin-bottom:18px;
display:flex;justify-content:center;text-align:center!important;}
.an-val-teal{color:var(--an-teal);}.an-val-gold{color:var(--gold);}
.an-val-matt{color:#2E7DF7;}.an-val-ryan{color:#E63B3B;}.an-val-neutral{color:var(--text-label);}
.an-snap-hero{font-size:52px;font-weight:900;color:var(--an-teal);line-height:1;margin-bottom:2px;}
.an-snap-hero-sub{font-size:9px;font-weight:700;letter-spacing:2px;color:var(--text-label);
text-transform:uppercase;margin-bottom:16px;}
.an-snap-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px;}
.an-snap-tile{background:var(--bg-panel);border:1px solid var(--border);border-radius:10px;padding:10px 12px;}
.an-snap-val{font-size:20px;font-weight:900;line-height:1;margin-bottom:3px;color:var(--text-primary);}
.an-snap-sub{font-size:8px;font-weight:700;letter-spacing:1.5px;color:var(--text-label);text-transform:uppercase;}
.an-snap-foot{font-size:9px;color:var(--text-label);}
.an-cmp-section{margin-bottom:18px;}
.an-cmp-metric{font-size:9px;font-weight:800;letter-spacing:2px;color:var(--text-label);
text-transform:uppercase;margin-bottom:10px;}
.an-cmp-bar-row{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
.an-cmp-name{font-size:9px;font-weight:800;letter-spacing:1.5px;width:36px;flex-shrink:0;text-transform:uppercase;}
.an-cmp-name.matt{color:#2E7DF7;}.an-cmp-name.ryan{color:#E63B3B;}
.an-cmp-track{flex:1;background:var(--bg-panel);border-radius:5px;height:10px;overflow:hidden;}
.an-cmp-fill{height:100%;border-radius:5px;}
.an-cmp-fill.matt{background:linear-gradient(90deg,#1C63D5,#2E7DF7);}
.an-cmp-fill.ryan{background:linear-gradient(90deg,#C9272A,#E63B3B);}
.an-cmp-val{font-size:12px;font-weight:800;width:38px;text-align:right;flex-shrink:0;}
.an-cmp-val.matt{color:#2E7DF7;}.an-cmp-val.ryan{color:#E63B3B;}
.an-ms-total{font-size:9px;font-weight:700;letter-spacing:2px;color:var(--text-label);
text-transform:uppercase;text-align:center;margin-bottom:16px;}
.an-ms-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:14px;}
.an-ms-tile{background:var(--bg-panel);border:1px solid var(--border);border-radius:10px;
padding:14px;text-align:center;}
.an-ms-val{font-size:36px;font-weight:900;line-height:1;margin-bottom:6px;}
.an-ms-val.matt{color:#2E7DF7;}.an-ms-val.ryan{color:#E63B3B;}
.an-ms-val.tie{color:var(--gold);}.an-ms-val.pending{color:var(--text-label);}
.an-ms-tile-label{font-size:9px;font-weight:700;letter-spacing:1.5px;color:var(--text-label);text-transform:uppercase;}
.an-ms-leader{text-align:center;font-size:11px;font-weight:700;color:var(--text-secondary);}
.an-pos-hdr{display:flex;justify-content:flex-end;gap:8px;margin-bottom:8px;
font-size:9px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;}
.an-pos-hdr-matt{color:#2E7DF7;width:32px;text-align:right;}
.an-pos-hdr-ryan{color:#E63B3B;width:32px;text-align:right;}
.an-pos-hdr-n{color:var(--text-label);width:52px;text-align:right;}
.an-pos-row{display:flex;align-items:center;gap:10px;margin-bottom:8px;}
.an-pos-name{font-size:10px;font-weight:800;letter-spacing:.5px;color:var(--text-secondary);width:52px;flex-shrink:0;}
.an-pos-bars{flex:1;}
.an-pos-bar-line{display:flex;align-items:center;gap:6px;margin-bottom:3px;}
.an-pos-bar-track{flex:1;background:var(--bg-panel);border-radius:3px;height:6px;overflow:hidden;}
.an-pos-bar-fill{height:100%;border-radius:3px;}
.an-pos-bar-fill.matt{background:#2E7DF7;}.an-pos-bar-fill.ryan{background:#E63B3B;}
.an-pos-val{font-size:10px;font-weight:700;width:32px;text-align:right;flex-shrink:0;}
.an-pos-val.matt{color:#2E7DF7;}.an-pos-val.ryan{color:#E63B3B;}
.an-pos-n{font-size:8px;color:var(--text-label);width:52px;text-align:right;flex-shrink:0;}
.an-kpi-hero{text-align:center;padding:14px 0 20px;border-bottom:1px solid var(--border);margin-bottom:20px;}
.an-kpi-hero-val{font-size:56px;font-weight:900;color:var(--an-teal);line-height:1;margin-bottom:6px;}
.an-kpi-hero-label{font-size:10px;font-weight:700;letter-spacing:2px;color:var(--text-label);text-transform:uppercase;}
.an-kpi-minis{display:flex;justify-content:space-around;}
.an-kpi-mini{text-align:center;}
.an-kpi-mini-val{font-size:22px;font-weight:900;line-height:1;margin-bottom:4px;}
.an-kpi-mini-label{font-size:8px;font-weight:700;letter-spacing:1.5px;color:var(--text-label);text-transform:uppercase;}
.an-badge-hdr-row{display:flex;align-items:center;padding-bottom:12px;
border-bottom:1px solid var(--border);margin-bottom:4px;}
.an-badge-hdr-name{flex:1;font-size:10px;font-weight:800;letter-spacing:2px;color:var(--text-label);text-transform:uppercase;}
.an-badge-hdr-col{width:56px;text-align:center;font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;}
.an-badge-hdr-col.matt{color:#2E7DF7;}.an-badge-hdr-col.ryan{color:#E63B3B;}
.an-badge-row{display:flex;align-items:center;padding:16px 0;border-bottom:1px solid rgba(34,50,71,.4);}
.an-badge-name{flex:1;font-size:13px;font-weight:700;color:var(--text-secondary);}
.an-badge-val{width:56px;text-align:center;font-size:20px;font-weight:900;}
.an-badge-val.matt{color:#2E7DF7;}.an-badge-val.ryan{color:#E63B3B;}.an-badge-val.zero{color:var(--text-label);}
.an-badge-story{font-size:10px;color:var(--text-label);margin-top:18px;line-height:1.7;}
.an-fran-strip{display:flex;border-radius:8px;overflow:hidden;height:32px;margin:16px 0 6px;}
.an-fran-seg{display:flex;align-items:center;font-size:11px;font-weight:800;color:#fff;letter-spacing:.5px;}
.an-fran-seg.matt{background:linear-gradient(90deg,#1C63D5,#2E7DF7);justify-content:flex-end;padding-right:10px;}
.an-fran-seg.ryan{background:linear-gradient(90deg,#C9272A,#E63B3B);justify-content:flex-start;padding-left:10px;}
.an-fran-legend{display:flex;justify-content:space-between;margin-top:16px;}
.an-fran-leg{text-align:center;}
.an-fran-leg-val{font-size:32px;font-weight:900;line-height:1;margin-bottom:3px;}
.an-fran-leg-val.matt{color:#2E7DF7;}.an-fran-leg-val.ryan{color:#E63B3B;}
.an-fran-leg-pct{font-size:13px;font-weight:700;color:var(--text-secondary);}
.an-fran-leg-label{font-size:8px;font-weight:700;letter-spacing:1.5px;color:var(--text-label);text-transform:uppercase;margin-top:2px;}
.an-fran-total{text-align:center;font-size:9px;color:var(--text-label);margin-top:14px;}
.stApp .tb-title{color:var(--an-teal)!important;}
.an-hist-bars-wrap{display:flex;align-items:flex-end;justify-content:space-around;height:140px;gap:4px;padding:12px 0 0;}
.an-hist-group{flex:1;display:flex;flex-direction:column;align-items:center;}
.an-hist-pair{display:flex;align-items:flex-end;gap:3px;margin-bottom:4px;}
.an-hist-bar{width:16px;border-radius:3px 3px 0 0;}
.an-hist-bar.matt{background:linear-gradient(0deg,#1C63D5,#2E7DF7);}
.an-hist-bar.ryan{background:linear-gradient(0deg,#C9272A,#E63B3B);}
.an-hist-counts{display:flex;gap:6px;margin-bottom:3px;}
.an-hist-cnt{font-size:8px;font-weight:800;letter-spacing:.5px;}
.an-hist-cnt.matt{color:#2E7DF7;}.an-hist-cnt.ryan{color:#E63B3B;}
.an-hist-lbl{font-size:8px;font-weight:700;letter-spacing:.5px;color:var(--text-label);text-align:center;margin-top:2px;}
.an-hist-legend{display:flex;gap:16px;justify-content:center;margin-top:14px;}
.an-hist-leg{display:flex;align-items:center;gap:5px;font-size:9px;font-weight:700;letter-spacing:1px;color:var(--text-secondary);}
.an-hist-dot{width:8px;height:8px;border-radius:2px;flex-shrink:0;}
.an-hist-dot.matt{background:#2E7DF7;}.an-hist-dot.ryan{background:#E63B3B;}
.an-tier-grp{margin-bottom:14px;}
.an-tier-grp-name{font-size:9px;font-weight:800;letter-spacing:2px;color:var(--text-secondary);text-transform:uppercase;margin-bottom:7px;}
.an-tier-bar-row{display:flex;align-items:center;gap:8px;margin-bottom:4px;}
.an-tier-owner{font-size:9px;font-weight:800;letter-spacing:1.5px;width:36px;flex-shrink:0;text-transform:uppercase;}
.an-tier-owner.matt{color:#2E7DF7;}.an-tier-owner.ryan{color:#E63B3B;}
.an-tier-track{flex:1;background:var(--bg-panel);border-radius:4px;height:10px;overflow:hidden;}
.an-tier-fill{height:100%;border-radius:4px;}
.an-tier-fill.matt{background:linear-gradient(90deg,#1C63D5,#2E7DF7);}
.an-tier-fill.ryan{background:linear-gradient(90deg,#C9272A,#E63B3B);}
.an-tier-count{font-size:12px;font-weight:800;width:28px;text-align:right;flex-shrink:0;}
.an-tier-count.matt{color:#2E7DF7;}.an-tier-count.ryan{color:#E63B3B;}
.an-tier-note{font-size:8px;color:var(--text-label);margin-top:10px;}
.an-comp-row{margin-bottom:18px;}
.an-comp-owner{font-size:9px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;}
.an-comp-owner.matt{color:#2E7DF7;}.an-comp-owner.ryan{color:#E63B3B;}
.an-comp-bar{display:flex;height:34px;border-radius:8px;overflow:hidden;}
.an-comp-seg{display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;color:rgba(255,255,255,.9);overflow:hidden;min-width:0;white-space:nowrap;}
.an-comp-legend{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:16px;}
.an-comp-leg{text-align:center;}
.an-comp-leg-swatch{height:6px;border-radius:2px;margin-bottom:4px;}
.an-comp-leg-lbl{font-size:7px;font-weight:700;letter-spacing:.5px;color:var(--text-label);text-transform:uppercase;line-height:1.3;}
.an-heat-table{width:100%;}
.an-heat-hdr-row{display:flex;align-items:center;gap:8px;padding-bottom:8px;border-bottom:1px solid var(--border);margin-bottom:6px;}
.an-heat-hdr-pos{width:90px;flex-shrink:0;font-size:9px;font-weight:800;letter-spacing:2px;color:var(--text-label);text-transform:uppercase;}
.an-heat-hdr-col{flex:1;text-align:center;font-size:10px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;}
.an-heat-hdr-col.matt{color:#2E7DF7;}.an-heat-hdr-col.ryan{color:#E63B3B;}.an-heat-hdr-col.league{color:var(--an-teal);}
.an-heat-row{display:flex;align-items:center;gap:8px;margin-bottom:5px;}
.an-heat-pos-lbl{width:90px;flex-shrink:0;font-size:11px;font-weight:800;letter-spacing:.5px;color:var(--text-secondary);}
.an-heat-cell{flex:1;height:36px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;}
.an-flex-row{display:flex;gap:16px;align-items:stretch;margin-bottom:16px;}
.an-flex-row .an-panel{display:flex;flex-direction:column;}
.an-r4-dist{flex:1.1;justify-content:space-between;}
.an-r4-tier{flex:1;}
.an-r5-comp{flex:1;justify-content:space-between;}
.an-r5-heat{flex:1.4;}
.an-heat-fullwidth .an-heat-cell{font-size:15px;height:40px;}
.an-heat-fullwidth .an-heat-hdr-col{font-size:11px;}
</style>""", unsafe_allow_html=True)

# ── Guard ──────────────────────────────────────────────────────────────────────
if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ───────────────────────────────────────────────────────────────────────
df      = load_players()
ms_df   = load_man_status()
ls      = compute_league_stats(df)
matt_st = compute_owner_stats(df, "Matt")
ryan_st = compute_owner_stats(df, "Ryan")
ms_sum  = compute_ms_summary(ms_df)

scored_count    = int(df["OVERALL SCORE"].notna().sum())
franchise_total = ls["franchise_total"]
ryan_edge       = ryan_st["avg_score"] - matt_st["avg_score"]

# Per-position avg scores (12 groups)
pos_avgs: dict[str, dict] = {}
for grp, positions in POSITION_GROUPS.items():
    grp_df = df[df["POSITION"].isin(positions)]
    m_sc   = grp_df[grp_df["OWNER"] == "Matt"].dropna(subset=["OVERALL SCORE"])
    r_sc   = grp_df[grp_df["OWNER"] == "Ryan"].dropna(subset=["OVERALL SCORE"])
    n_each = len(grp_df[grp_df["OWNER"] == "Matt"])
    pos_avgs[grp] = {
        "matt": float(m_sc["OVERALL SCORE"].mean()) if len(m_sc) else 0.0,
        "ryan": float(r_sc["OVERALL SCORE"].mean()) if len(r_sc) else 0.0,
        "n":    n_each,
    }
    league_sc = grp_df.dropna(subset=["OVERALL SCORE"])
    pos_avgs[grp]["league_avg"] = float(league_sc["OVERALL SCORE"].mean()) if len(league_sc) else 0.0

pos_max = max(max(v["matt"], v["ryan"]) for v in pos_avgs.values()) or 1.0

# Award badge counts per owner
_AWARD_DEFS = [
    ("MVP",     "MVP"),
    ("OPOY",    "OPOY"),
    ("DPOY",    "DPOY"),
    ("OROY",    "OROY"),
    ("DROY",    "DROY"),
    ("ALL_PRO", "ALL-PRO"),
    ("SB Win",  "SB WIN"),
    ("SB_MVP",  "SB MVP"),
]
badge_rows_data = [
    (lbl, int(df[df["OWNER"] == "Matt"][col].fillna(0).sum()),
          int(df[df["OWNER"] == "Ryan"][col].fillna(0).sum()))
    for col, lbl in _AWARD_DEFS
]

# KI-011: extract SB Win / SB MVP counts for live story string
_sb_row   = {lbl: (m, r) for lbl, m, r in badge_rows_data}
_matt_sb  = _sb_row.get("SB WIN",  (0, 0))[0]
_ryan_sb  = _sb_row.get("SB WIN",  (0, 0))[1]
_matt_sbm = _sb_row.get("SB MVP",  (0, 0))[0]
_ryan_sbm = _sb_row.get("SB MVP",  (0, 0))[1]
_sb_leader = "Matt" if _matt_sb >= _ryan_sb else "Ryan"

# Bar normalisation (per metric, relative to the higher owner)
avg_max       = max(matt_st["avg_score"], ryan_st["avg_score"])
fran_max      = max(matt_st["franchise"], ryan_st["franchise"])
bust_max      = max(matt_st["busts"], ryan_st["busts"]) or 1

matt_avg_w    = matt_st["avg_score"]  / avg_max  * 100
ryan_avg_w    = ryan_st["avg_score"]  / avg_max  * 100
matt_fran_w   = matt_st["franchise"]  / fran_max * 100
ryan_fran_w   = ryan_st["franchise"]  / fran_max * 100
matt_bust_w   = matt_st["busts"]      / bust_max * 100
ryan_bust_w   = ryan_st["busts"]      / bust_max * 100

# Franchise balance percentages
matt_fran_pct = matt_st["franchise"] / franchise_total * 100
ryan_fran_pct = ryan_st["franchise"] / franchise_total * 100

# KI-012: live franchise ratio for story string
_fran_ratio  = (ryan_st["franchise"] / matt_st["franchise"]) if matt_st["franchise"] > 0 else 0.0
_fran_leader = "Ryan" if ryan_st["franchise"] > matt_st["franchise"] else "Matt"
_fran_trailer = "Matt" if _fran_leader == "Ryan" else "Ryan"

# Man Status leader display
if ms_sum["leader"] == "Ryan":
    ms_leader_text = "Ryan leads"
    ms_leader_cls  = "an-val-ryan"
    ms_record      = f"{ms_sum['ryan_wins']}–{ms_sum['matt_wins']}–{ms_sum['ties']}"
elif ms_sum["leader"] == "Matt":
    ms_leader_text = "Matt leads"
    ms_leader_cls  = "an-val-matt"
    ms_record      = f"{ms_sum['matt_wins']}–{ms_sum['ryan_wins']}–{ms_sum['ties']}"
else:
    ms_leader_text = "All Square"
    ms_leader_cls  = "an-val-neutral"
    ms_record      = f"{ms_sum['matt_wins']}–{ms_sum['ryan_wins']}–{ms_sum['ties']}"

ms_total = ms_sum["matt_wins"] + ms_sum["ryan_wins"] + ms_sum["ties"] + ms_sum["pending"]

# =============================================================================
# PHASE 2 DATA — Panels 8–11
# =============================================================================

# Panel 8 — Score distribution (5 buckets over scored players)
_SCORE_BUCKETS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 200)]
_BUCKET_LABELS = ["0–20", "20–40", "40–60", "60–80", "80–100"]
_scored_df = df.dropna(subset=["OVERALL SCORE"])
score_dist: list[dict] = []
for (_lo, _hi), _lbl in zip(_SCORE_BUCKETS, _BUCKET_LABELS):
    _b = _scored_df[(_scored_df["OVERALL SCORE"] >= _lo) & (_scored_df["OVERALL SCORE"] < _hi)]
    score_dist.append({
        "label": _lbl,
        "matt":  int(len(_b[_b["OWNER"] == "Matt"])),
        "ryan":  int(len(_b[_b["OWNER"] == "Ryan"])),
    })
dist_max = max(max(b["matt"], b["ryan"]) for b in score_dist) or 1

# Panels 9 + 10 — shared tier counts (scored-only, 5 canonical tiers)
_TIERS_P2 = ["Franchise", "High-End Starter", "Starter", "Contributor", "Bust"]
_TIER_COLORS = {
    "Franchise":        "#F3BC2E",
    "High-End Starter": "#3ED598",
    "Starter":          "#18C2A8",
    "Contributor":      "#56B7FF",
    "Bust":             "#FF6B6B",
}
tier_counts: dict[str, dict] = {}
for _tier in _TIERS_P2:
    _tf = _scored_df[_scored_df["CAREER_TIER"] == _tier]
    tier_counts[_tier] = {
        "matt": int(len(_tf[_tf["OWNER"] == "Matt"])),
        "ryan": int(len(_tf[_tf["OWNER"] == "Ryan"])),
    }
matt_tier_total = sum(tier_counts[t]["matt"] for t in _TIERS_P2)
ryan_tier_total = sum(tier_counts[t]["ryan"] for t in _TIERS_P2)

# Panel 11 — heatmap intensity helpers (global min/max across all 36 cells)
_heat_vals_all = [
    pos_avgs[g][k] for g in pos_avgs
    for k in ("matt", "ryan", "league_avg")
    if pos_avgs[g].get(k, 0.0) > 0
]
_heat_min = min(_heat_vals_all) if _heat_vals_all else 0.0
_heat_max = max(_heat_vals_all) if _heat_vals_all else 1.0

def _heat_alpha(v: float) -> float:
    if _heat_max == _heat_min or v == 0: return 0.0
    return max(0.0, min(0.85, (v - _heat_min) / (_heat_max - _heat_min) * 0.85))

_BG_RGB = (13, 26, 42)   # #0D1A2A — bg-panel
_TL_RGB = (24, 194, 168) # #18C2A8 — an-teal

def _blend_color(t: float) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        int(_BG_RGB[0] + (_TL_RGB[0] - _BG_RGB[0]) * t),
        int(_BG_RGB[1] + (_TL_RGB[1] - _BG_RGB[1]) * t),
        int(_BG_RGB[2] + (_TL_RGB[2] - _BG_RGB[2]) * t),
    )

# =============================================================================
# PAGE HEADER
# =============================================================================
st.markdown(
    page_header(
        "📈 ANALYTICS",
        f"{ls['total_players']} Players · {ls['draft_classes']} Draft Classes · Live Database",
    ),
    unsafe_allow_html=True,
)

# =============================================================================
# ROW 1 — League Snapshot | Owner Comparison | Man Status
# =============================================================================
r1c1, r1c2, r1c3 = st.columns(3)

with r1c1:
    st.markdown(f"""
<div class="an-panel">
<div class="an-label">LEAGUE SNAPSHOT</div>
<div class="an-snap-hero">{ls['total_players']}</div>
<div class="an-snap-hero-sub">Primary Players &middot; {ls['year_range']}</div>
<div class="an-snap-grid">
<div class="an-snap-tile"><div class="an-snap-val">{ls['draft_classes']}</div><div class="an-snap-sub">Draft Classes</div></div>
<div class="an-snap-tile"><div class="an-snap-val an-val-gold">{ls['franchise_total']}</div><div class="an-snap-sub">Franchise</div></div>
<div class="an-snap-tile"><div class="an-snap-val an-val-teal">{ls['avg_score']:.2f}</div><div class="an-snap-sub">League Avg</div></div>
<div class="an-snap-tile"><div class="an-snap-val an-val-matt">{matt_st['avg_score']:.2f}</div><div class="an-snap-sub">Matt Avg</div></div>
<div class="an-snap-tile"><div class="an-snap-val an-val-ryan">{ryan_st['avg_score']:.2f}</div><div class="an-snap-sub">Ryan Avg</div></div>
<div class="an-snap-tile"><div class="an-snap-val an-val-ryan">+{ryan_edge:.1f}</div><div class="an-snap-sub">Ryan Edge</div></div>
</div>
<div class="an-snap-foot">{scored_count} of {ls['total_players']} scored &middot; {ls['total_players'] - scored_count} TBD (2025&ndash;26 classes)</div>
</div>""", unsafe_allow_html=True)

with r1c2:
    st.markdown(f"""
<div class="an-panel">
<div class="an-label">OWNER COMPARISON</div>
<div class="an-cmp-section">
<div class="an-cmp-metric">AVG SCORE</div>
<div class="an-cmp-bar-row">
<span class="an-cmp-name matt">MATT</span>
<div class="an-cmp-track"><div class="an-cmp-fill matt" style="width:{matt_avg_w:.1f}%"></div></div>
<span class="an-cmp-val matt">{matt_st['avg_score']:.2f}</span>
</div>
<div class="an-cmp-bar-row">
<span class="an-cmp-name ryan">RYAN</span>
<div class="an-cmp-track"><div class="an-cmp-fill ryan" style="width:{ryan_avg_w:.1f}%"></div></div>
<span class="an-cmp-val ryan">{ryan_st['avg_score']:.2f}</span>
</div>
</div>
<div class="an-cmp-section">
<div class="an-cmp-metric">FRANCHISE PLAYERS</div>
<div class="an-cmp-bar-row">
<span class="an-cmp-name matt">MATT</span>
<div class="an-cmp-track"><div class="an-cmp-fill matt" style="width:{matt_fran_w:.1f}%"></div></div>
<span class="an-cmp-val matt">{matt_st['franchise']}</span>
</div>
<div class="an-cmp-bar-row">
<span class="an-cmp-name ryan">RYAN</span>
<div class="an-cmp-track"><div class="an-cmp-fill ryan" style="width:{ryan_fran_w:.1f}%"></div></div>
<span class="an-cmp-val ryan">{ryan_st['franchise']}</span>
</div>
</div>
<div class="an-cmp-section">
<div class="an-cmp-metric">BUST COUNT</div>
<div class="an-cmp-bar-row">
<span class="an-cmp-name matt">MATT</span>
<div class="an-cmp-track"><div class="an-cmp-fill matt" style="width:{matt_bust_w:.1f}%"></div></div>
<span class="an-cmp-val matt">{matt_st['busts']}</span>
</div>
<div class="an-cmp-bar-row">
<span class="an-cmp-name ryan">RYAN</span>
<div class="an-cmp-track"><div class="an-cmp-fill ryan" style="width:{ryan_bust_w:.1f}%"></div></div>
<span class="an-cmp-val ryan">{ryan_st['busts']}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

with r1c3:
    st.markdown(f"""
<div class="an-panel">
<div class="an-label">MAN STATUS &middot; SERIES RECORD</div>
<div class="an-ms-total">{ms_total} MATCHUPS PLAYED</div>
<div class="an-ms-grid">
<div class="an-ms-tile">
<div class="an-ms-val ryan">{ms_sum['ryan_wins']}</div>
<div class="an-ms-tile-label">Ryan Wins</div>
</div>
<div class="an-ms-tile">
<div class="an-ms-val matt">{ms_sum['matt_wins']}</div>
<div class="an-ms-tile-label">Matt Wins</div>
</div>
<div class="an-ms-tile">
<div class="an-ms-val tie">{ms_sum['ties']}</div>
<div class="an-ms-tile-label">Draws</div>
</div>
<div class="an-ms-tile">
<div class="an-ms-val pending">{ms_sum['pending']}</div>
<div class="an-ms-tile-label">Pending</div>
</div>
</div>
<div class="an-ms-leader"><span class="{ms_leader_cls}">{ms_leader_text}</span> &middot; {ms_record}</div>
</div>""", unsafe_allow_html=True)

# =============================================================================
# ROW 2 — Position Distribution | Badge Distribution
# =============================================================================
r2c1, r2c2 = st.columns([1.4, 1])

with r2c1:
    pos_rows_html = ""
    for grp, avgs in pos_avgs.items():
        m_w = f"{avgs['matt'] / pos_max * 100:.1f}"
        r_w = f"{avgs['ryan'] / pos_max * 100:.1f}"
        m_v = f"{avgs['matt']:.1f}"
        r_v = f"{avgs['ryan']:.1f}"
        n   = avgs["n"]
        pos_rows_html += (
            f'<div class="an-pos-row">'
            f'<div class="an-pos-name">{grp}</div>'
            f'<div class="an-pos-bars">'
            f'<div class="an-pos-bar-line">'
            f'<div class="an-pos-bar-track">'
            f'<div class="an-pos-bar-fill matt" style="width:{m_w}%"></div>'
            f'</div>'
            f'<span class="an-pos-val matt">{m_v}</span>'
            f'</div>'
            f'<div class="an-pos-bar-line">'
            f'<div class="an-pos-bar-track">'
            f'<div class="an-pos-bar-fill ryan" style="width:{r_w}%"></div>'
            f'</div>'
            f'<span class="an-pos-val ryan">{r_v}</span>'
            f'</div>'
            f'</div>'
            f'<span class="an-pos-n">n={n} ea</span>'
            f'</div>'
        )
    st.markdown(f"""
<div class="an-panel">
<div class="an-label">POSITION AVG SCORE &middot; MATT vs RYAN</div>
<div class="an-pos-hdr">
<span class="an-pos-hdr-matt">MATT</span>
<span class="an-pos-hdr-ryan">RYAN</span>
<span class="an-pos-hdr-n">N/OWNER</span>
</div>
{pos_rows_html}
</div>""", unsafe_allow_html=True)

with r2c2:
    badge_html = ""
    for label, m, r in badge_rows_data:
        m_cls = "matt" if m > 0 else "zero"
        r_cls = "ryan" if r > 0 else "zero"
        badge_html += (
            f'<div class="an-badge-row">'
            f'<div class="an-badge-name">{label}</div>'
            f'<div class="an-badge-val {m_cls}">{m}</div>'
            f'<div class="an-badge-val {r_cls}">{r}</div>'
            f'</div>'
        )
    st.markdown(f"""
<div class="an-panel">
<div class="an-label">BADGE DISTRIBUTION &middot; 8 AWARD TYPES</div>
<div class="an-badge-hdr-row">
<div class="an-badge-hdr-name">AWARD</div>
<div class="an-badge-hdr-col matt">MATT</div>
<div class="an-badge-hdr-col ryan">RYAN</div>
</div>
{badge_html}
<div class="an-badge-story">Ryan sweeps individual accolades &mdash; MVP, all D/O awards.<br>{_sb_leader} leads SB Wins {_matt_sb}&ndash;{_ryan_sb}. SB MVP split {_matt_sbm}&ndash;{_ryan_sbm}.</div>
</div>""", unsafe_allow_html=True)

# =============================================================================
# ROW 3 — Average Score Analysis | Franchise Balance
# =============================================================================
r3c1, r3c2 = st.columns([1, 1.2])

with r3c1:
    st.markdown(f"""
<div class="an-panel">
<div class="an-label">AVERAGE SCORE ANALYSIS</div>
<div class="an-kpi-hero">
<div class="an-kpi-hero-val">{ls['avg_score']:.2f}</div>
<div class="an-kpi-hero-label">League Average Score</div>
</div>
<div class="an-kpi-minis">
<div class="an-kpi-mini">
<div class="an-kpi-mini-val an-val-matt">{matt_st['avg_score']:.2f}</div>
<div class="an-kpi-mini-label">Matt Avg</div>
</div>
<div class="an-kpi-mini">
<div class="an-kpi-mini-val an-val-ryan">{ryan_st['avg_score']:.2f}</div>
<div class="an-kpi-mini-label">Ryan Avg</div>
</div>
<div class="an-kpi-mini">
<div class="an-kpi-mini-val an-val-ryan">+{ryan_edge:.1f}</div>
<div class="an-kpi-mini-label">Ryan Edge</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

with r3c2:
    st.markdown(f"""
<div class="an-panel">
<div class="an-label">FRANCHISE BALANCE &middot; {franchise_total} TOTAL</div>
<div class="an-fran-strip">
<div class="an-fran-seg matt" style="width:{matt_fran_pct:.1f}%">{matt_fran_pct:.0f}%</div>
<div class="an-fran-seg ryan" style="width:{ryan_fran_pct:.1f}%">{ryan_fran_pct:.0f}%</div>
</div>
<div class="an-fran-legend">
<div class="an-fran-leg">
<div class="an-fran-leg-val matt">{matt_st['franchise']}</div>
<div class="an-fran-leg-pct">{matt_fran_pct:.0f}%</div>
<div class="an-fran-leg-label">Matt</div>
</div>
<div class="an-fran-leg">
<div class="an-fran-leg-val" style="color:var(--text-label);">{franchise_total}</div>
<div class="an-fran-leg-label">Total</div>
</div>
<div class="an-fran-leg">
<div class="an-fran-leg-val ryan">{ryan_st['franchise']}</div>
<div class="an-fran-leg-pct">{ryan_fran_pct:.0f}%</div>
<div class="an-fran-leg-label">Ryan</div>
</div>
</div>
<div class="an-fran-total">{_fran_leader} leads franchise production {_fran_ratio:.1f}&times; over {_fran_trailer} &middot; {ls['year_range']}</div>
</div>""", unsafe_allow_html=True)

# =============================================================================
# ROW 4 — Score Distribution | Tier Composition  (equal-height flex pair)
# =============================================================================

# Left: Score Distribution
_hist_html = '<div class="an-hist-bars-wrap">'
for _bd in score_dist:
    _mh = f"{int(_bd['matt'] / dist_max * 120)}px"
    _rh = f"{int(_bd['ryan'] / dist_max * 120)}px"
    _mc = _bd["matt"]
    _rc = _bd["ryan"]
    _hist_html += (
        f'<div class="an-hist-group">'
        f'<div class="an-hist-counts">'
        f'<span class="an-hist-cnt matt">{_mc}</span>'
        f'<span class="an-hist-cnt ryan">{_rc}</span>'
        f'</div>'
        f'<div class="an-hist-pair">'
        f'<div class="an-hist-bar matt" style="height:{_mh}"></div>'
        f'<div class="an-hist-bar ryan" style="height:{_rh}"></div>'
        f'</div>'
        f'<div class="an-hist-lbl">{_bd["label"]}</div>'
        f'</div>'
    )
_hist_html += (
    '</div>'
    '<div class="an-hist-legend">'
    '<div class="an-hist-leg"><div class="an-hist-dot matt"></div>Matt</div>'
    '<div class="an-hist-leg"><div class="an-hist-dot ryan"></div>Ryan</div>'
    '</div>'
)
_r4_dist = (
    f'<div class="an-panel an-r4-dist">'
    f'<div class="an-label">SCORE DISTRIBUTION &middot; {scored_count} SCORED PLAYERS</div>'
    f'{_hist_html}'
    f'</div>'
)

# Right: Tier Composition
_comp_html = ""
for _owner, _total, _cls in [("Matt", matt_tier_total, "matt"), ("Ryan", ryan_tier_total, "ryan")]:
    _segs = ""
    for _t in _TIERS_P2:
        _cnt  = tier_counts[_t][_owner.lower()]
        _pct  = _cnt / _total * 100 if _total else 0
        _col  = _TIER_COLORS[_t]
        _lbl  = f"{_pct:.0f}%" if _pct >= 10 else ""
        _segs += f'<div class="an-comp-seg" style="width:{_pct:.1f}%;background:{_col};">{_lbl}</div>'
    _comp_html += (
        f'<div class="an-comp-row">'
        f'<div class="an-comp-owner {_cls}">{_owner.upper()} &middot; {_total} scored</div>'
        f'<div class="an-comp-bar">{_segs}</div>'
        f'</div>'
    )
_leg_html = '<div class="an-comp-legend">'
for _t in _TIERS_P2:
    _col   = _TIER_COLORS[_t]
    _short = _t.split(" ")[0]
    _leg_html += (
        f'<div class="an-comp-leg">'
        f'<div class="an-comp-leg-swatch" style="background:{_col}"></div>'
        f'<div class="an-comp-leg-lbl">{_short}</div>'
        f'</div>'
    )
_leg_html += '</div>'
_r4_comp = (
    f'<div class="an-panel an-r5-comp">'
    f'<div class="an-label">TIER COMPOSITION &middot; ROSTER BREAKDOWN</div>'
    f'{_comp_html}'
    f'{_leg_html}'
    f'</div>'
)

st.markdown(
    f'<div class="an-flex-row">{_r4_dist}{_r4_comp}</div>',
    unsafe_allow_html=True,
)

# =============================================================================
# ROW 5 — Franchise Tier Breakdown  (full width)
# =============================================================================
_tier_max = max(max(tier_counts[t]["matt"], tier_counts[t]["ryan"]) for t in _TIERS_P2) or 1
_tier_html = ""
for _t in _TIERS_P2:
    _tm = tier_counts[_t]["matt"]
    _tr = tier_counts[_t]["ryan"]
    _tmw = f"{_tm / _tier_max * 100:.1f}"
    _trw = f"{_tr / _tier_max * 100:.1f}"
    _tier_html += (
        f'<div class="an-tier-grp">'
        f'<div class="an-tier-grp-name">{_t}</div>'
        f'<div class="an-tier-bar-row">'
        f'<span class="an-tier-owner matt">MATT</span>'
        f'<div class="an-tier-track"><div class="an-tier-fill matt" style="width:{_tmw}%"></div></div>'
        f'<span class="an-tier-count matt">{_tm}</span>'
        f'</div>'
        f'<div class="an-tier-bar-row">'
        f'<span class="an-tier-owner ryan">RYAN</span>'
        f'<div class="an-tier-track"><div class="an-tier-fill ryan" style="width:{_trw}%"></div></div>'
        f'<span class="an-tier-count ryan">{_tr}</span>'
        f'</div>'
        f'</div>'
    )
_p9_base = matt_tier_total + ryan_tier_total
st.markdown(
    f'<div class="an-panel">'
    f'<div class="an-label">FRANCHISE TIER BREAKDOWN</div>'
    f'{_tier_html}'
    f'<div class="an-tier-note">Base: {_p9_base} scored-and-tiered players</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# =============================================================================
# ROW 6 — Position Heatmap  (full width)
# =============================================================================
_heat_rows = ""
for _grp, _avgs in pos_avgs.items():
    _row = f'<div class="an-heat-row"><div class="an-heat-pos-lbl">{_grp}</div>'
    for _key in ("matt", "ryan", "league_avg"):
        _v    = _avgs.get(_key, 0.0)
        _t    = _heat_alpha(_v)
        _txt  = "#ffffff" if _t > 0.4 else "#A8B5C6"
        _disp = f"{_v:.1f}" if _v > 0 else "&mdash;"
        _row += (
            f'<div class="an-heat-cell"'
            f' style="background:{_blend_color(_t)};color:{_txt};">'
            f'{_disp}</div>'
        )
    _row += '</div>'
    _heat_rows += _row
st.markdown(
    f'<div class="an-panel an-heat-fullwidth">'
    f'<div class="an-label">POSITION SCORE HEATMAP &middot; 12 GROUPS</div>'
    f'<div class="an-heat-table">'
    f'<div class="an-heat-hdr-row">'
    f'<div class="an-heat-hdr-pos">POSITION</div>'
    f'<div class="an-heat-hdr-col matt">MATT</div>'
    f'<div class="an-heat-hdr-col ryan">RYAN</div>'
    f'<div class="an-heat-hdr-col league">LEAGUE</div>'
    f'</div>'
    f'{_heat_rows}'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)
