"""
pages/WildcardBoys.py — Wildcard Boys
Displays speculative late picks graded by Cooked Meter (0=pristine, 100=cooked).
WC Score = 100 − Cooked Meter, computed live.
Too Early picks are shown but excluded from scoreboard averages.
Pending (blank OUTCOME) picks = 2026 class, not drafted yet.

Identity: Late-Night Gambling Den.  Every swing on the table.
"""

import html as _html

import pandas as pd
import streamlit as st

from core.data_loader import load_wildcard, workbook_exists
from core.sidebar import render_sidebar
from core.components import page_header

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wildcard Boys — Trail & Bish Dynasty",
    page_icon="🔥",
    layout="wide",
)

render_sidebar(active="Wildcard Boys")

# ── Scoped CSS (wc- prefix) ────────────────────────────────────────────────────
st.markdown("""<style>
/* ── Hero ──────────────────────────────────────────────────────────────────── */
.wc-hero{text-align:center;padding:8px 0 28px;margin-bottom:4px;}
.wc-hero-icon{font-size:32px;margin-bottom:10px;}
.wc-hero-title{font-size:30px;font-weight:900;letter-spacing:5px;
text-transform:uppercase;color:#fff;margin:0 0 8px;}
.wc-hero-sub{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#4a6080;}

/* ── Explainer ─────────────────────────────────────────────────────────────── */
.wc-explainer{background:rgba(10,14,25,.7);border:1px solid rgba(255,255,255,.07);
border-left:3px solid #D4AF37;border-radius:8px;padding:13px 18px;
margin-bottom:26px;font-size:12px;color:#8090aa;line-height:1.7;}
.wc-explainer strong{color:#D4AF37;}

/* ── Scoreboard ────────────────────────────────────────────────────────────── */
.wc-scoreboard{display:grid;grid-template-columns:1fr auto 1fr;gap:16px;
align-items:center;background:rgba(10,14,25,.8);border:1px solid rgba(255,255,255,.08);
border-radius:12px;padding:22px 28px;margin-bottom:26px;}
.wc-sb-owner{text-align:center;}
.wc-sb-name{font-size:11px;font-weight:800;letter-spacing:2.5px;
text-transform:uppercase;margin-bottom:8px;}
.wc-sb-name.matt{color:#2E7DF7;}
.wc-sb-name.ryan{color:#E63B3B;}
.wc-sb-avg{font-size:40px;font-weight:900;color:#fff;line-height:1;}
.wc-sb-sub{font-size:10px;color:#4a6080;margin-top:5px;letter-spacing:1px;
text-transform:uppercase;}
.wc-sb-crown{font-size:22px;margin-top:5px;}
.wc-sb-vs{font-size:12px;color:#1e2535;font-weight:900;text-align:center;
letter-spacing:1px;}
.wc-sb-leader-lbl{font-size:9px;font-weight:800;letter-spacing:1.5px;
text-transform:uppercase;margin-top:4px;}
.wc-sb-leader-lbl.matt{color:#2E7DF7;}
.wc-sb-leader-lbl.ryan{color:#E63B3B;}

/* ── Legend ────────────────────────────────────────────────────────────────── */
.wc-legend{display:flex;flex-wrap:wrap;gap:7px;justify-content:center;
margin-bottom:28px;}
.wc-legend-chip{font-size:9px;font-weight:700;letter-spacing:1px;
text-transform:uppercase;padding:4px 11px;border-radius:12px;}

/* ── Section label ─────────────────────────────────────────────────────────── */
.wc-section-lbl{font-size:9px;font-weight:800;letter-spacing:3px;
text-transform:uppercase;color:#D4AF37;border-bottom:1px solid rgba(255,255,255,.06);
padding-bottom:8px;margin:24px 0 12px;}

/* ── Pick row ──────────────────────────────────────────────────────────────── */
.wc-pick-row{display:grid;grid-template-columns:58px 1fr 160px 110px;
align-items:center;gap:14px;background:rgba(10,14,25,.75);
border:1px solid rgba(255,255,255,.06);border-radius:8px;
padding:11px 16px;margin-bottom:6px;transition:border-color .15s;}
.wc-pick-row:hover{border-color:rgba(255,255,255,.12);}
.wc-pick-row.pending{opacity:.5;}

.wc-pick-cat{font-size:10px;font-weight:800;color:#4a6080;letter-spacing:1px;
text-transform:uppercase;}
.wc-pick-main{display:flex;align-items:flex-start;gap:10px;}
.wc-owner-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:4px;}
.wc-owner-dot.matt{background:#2E7DF7;}
.wc-owner-dot.ryan{background:#E63B3B;}
.wc-pick-name{font-size:14px;font-weight:700;color:#e8eaf0;}
.wc-pick-pos{font-size:10px;color:#4a6080;margin-left:5px;}
.wc-pick-notes{font-size:10px;color:#4a6080;display:block;margin-top:2px;
line-height:1.4;}
.wc-pick-pending-tag{font-size:10px;color:#3a4450;font-style:italic;
display:block;margin-top:2px;}

.wc-meter-wrap{display:flex;flex-direction:column;gap:4px;}
.wc-meter-label{font-size:9px;font-weight:700;letter-spacing:.5px;
text-transform:uppercase;}
.wc-meter-bar-bg{height:5px;border-radius:3px;background:rgba(255,255,255,.06);
overflow:hidden;}
.wc-meter-bar-fill{height:100%;border-radius:3px;}
.wc-meter-sub{font-size:9px;color:#3a4450;margin-top:1px;}

/* ── Outcome badges ─────────────────────────────────────────────────────────── */
.wc-badge{font-size:9px;font-weight:800;letter-spacing:.5px;text-transform:uppercase;
padding:5px 11px;border-radius:6px;text-align:center;white-space:nowrap;}
.wc-elite  {background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3);}
.wc-strong {background:rgba(74,222,128,.15);color:#4ade80;border:1px solid rgba(74,222,128,.3);}
.wc-solid  {background:rgba(163,230,53,.15);color:#a3e635;border:1px solid rgba(163,230,53,.3);}
.wc-mixed  {background:rgba(234,179,8,.15);color:#eab308;border:1px solid rgba(234,179,8,.3);}
.wc-under  {background:rgba(249,115,22,.15);color:#f97316;border:1px solid rgba(249,115,22,.3);}
.wc-cooked {background:rgba(230,59,59,.15);color:#E63B3B;border:1px solid rgba(230,59,59,.3);}
.wc-early  {background:rgba(74,96,128,.15);color:#8090aa;border:1px solid rgba(74,96,128,.3);}
.wc-pending{background:rgba(42,48,64,.15);color:#5a6470;border:1px dashed rgba(74,96,128,.25);}

/* ── Empty / error states ─────────────────────────────────────────────────── */
.wc-empty{padding:16px;font-size:12px;color:#4a6080;text-align:center;}
</style>""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────────
if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────
df_raw = load_wildcard()

# Real picks only (has a PLAYER and a YEAR)
df = df_raw[df_raw["PLAYER"].notna() & df_raw["YEAR"].notna()].copy()

# Normalise outcome string
df["OUTCOME"] = df["OUTCOME"].where(df["OUTCOME"].notna(), other=None)

# Compute WC Score live
df["WC_SCORE_LIVE"] = 100.0 - df["COOKED_METER"]

# Scoreboard: exclude Too Early AND blank OUTCOME
_scored = df[
    df["OUTCOME"].notna() &
    (df["OUTCOME"].str.strip().str.lower() != "too early")
].copy()

# Per-owner scoreboard stats
def _sb_stats(owner: str) -> dict:
    o = _scored[_scored["OWNER"] == owner]
    return {
        "picks": len(o),
        "avg":   round(o["WC_SCORE_LIVE"].mean(), 1) if len(o) else 0.0,
        "total": int(o["WC_SCORE_LIVE"].sum()),
    }

matt_sb = _sb_stats("Matt")
ryan_sb = _sb_stats("Ryan")
leader  = "Matt" if matt_sb["avg"] >= ryan_sb["avg"] else "Ryan"

# ── Outcome → style maps ───────────────────────────────────────────────────────
_OUTCOME_NORM = {
    "elite hit":    ("Elite Hit",    "wc-elite",  "#22c55e"),
    "strong hit":   ("Strong Hit",   "wc-strong", "#4ade80"),
    "solid value":  ("Solid Value",  "wc-solid",  "#a3e635"),
    "mixed result": ("Mixed Result", "wc-mixed",  "#eab308"),
    "underwhelming":("Underwhelming","wc-under",  "#f97316"),
    "cooked":       ("Cooked",       "wc-cooked", "#E63B3B"),
    "too early":    ("Too Early",    "wc-early",  "#4a6080"),
}

def _outcome_info(outcome: str | None):
    """Return (display_label, badge_css_class, bar_color)."""
    if outcome is None:
        return ("Pending", "wc-pending", "#3a4450")
    key = outcome.strip().lower()
    return _OUTCOME_NORM.get(key, (outcome, "wc-pending", "#3a4450"))

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="wc-hero">
  <div class="wc-hero-icon">🔥</div>
  <div class="wc-hero-title">Wildcard Boys</div>
  <div class="wc-hero-sub">The Cooked Meter · How every late swing aged</div>
</div>
""", unsafe_allow_html=True)

# ── Explainer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="wc-explainer">
  <strong>Judgment call, not a formula.</strong>
  Wildcard outcomes are graded by feel — these are speculative late picks,
  not the main draft. Scoring is kept intentionally separate from the dynasty
  formula. <strong>"Too Early"</strong> picks aren't counted in the averages
  until they have a real outcome. <strong>Pending</strong> rows (2026 class)
  haven't been drafted yet.
</div>
""", unsafe_allow_html=True)

# ── Scoreboard ────────────────────────────────────────────────────────────────
_matt_crown = "👑" if leader == "Matt" else ""
_ryan_crown = "👑" if leader == "Ryan" else ""
_matt_lead_html = f'<div class="wc-sb-leader-lbl matt">Leading</div>' if leader == "Matt" else ""
_ryan_lead_html = f'<div class="wc-sb-leader-lbl ryan">Leading</div>' if leader == "Ryan" else ""

st.markdown(f"""
<div class="wc-scoreboard">
  <div class="wc-sb-owner">
    <div class="wc-sb-name matt">Matt</div>
    <div class="wc-sb-avg">{matt_sb["avg"]}</div>
    <div class="wc-sb-sub">{matt_sb["picks"]} scored picks</div>
    <div class="wc-sb-crown">{_matt_crown}</div>
    {_matt_lead_html}
  </div>
  <div class="wc-sb-vs">VS</div>
  <div class="wc-sb-owner">
    <div class="wc-sb-name ryan">Ryan</div>
    <div class="wc-sb-avg">{ryan_sb["avg"]}</div>
    <div class="wc-sb-sub">{ryan_sb["picks"]} scored picks</div>
    <div class="wc-sb-crown">{_ryan_crown}</div>
    {_ryan_lead_html}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Legend ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="wc-legend">
  <span class="wc-legend-chip wc-elite">Elite Hit</span>
  <span class="wc-legend-chip wc-strong">Strong Hit</span>
  <span class="wc-legend-chip wc-solid">Solid Value</span>
  <span class="wc-legend-chip wc-mixed">Mixed Result</span>
  <span class="wc-legend-chip wc-under">Underwhelming</span>
  <span class="wc-legend-chip wc-cooked">Cooked</span>
  <span class="wc-legend-chip wc-early">Too Early</span>
  <span class="wc-legend-chip wc-pending">Pending</span>
</div>
""", unsafe_allow_html=True)

# ── Owner filter ──────────────────────────────────────────────────────────────
_filter_owner = st.radio(
    "Filter by owner",
    ["All", "Matt", "Ryan"],
    horizontal=True,
    label_visibility="collapsed",
)

if _filter_owner != "All":
    df = df[df["OWNER"] == _filter_owner].copy()

# ── Year groups (newest first) ─────────────────────────────────────────────────
_years = sorted(df["YEAR"].dropna().unique().astype(int), reverse=True)

def _pick_row_html(row: pd.Series) -> str:
    """Render one pick row as an HTML string."""
    outcome    = row["OUTCOME"] if pd.notna(row["OUTCOME"]) else None
    is_pending = outcome is None
    is_early   = (outcome or "").strip().lower() == "too early"

    display_lbl, badge_cls, bar_color = _outcome_info(outcome)

    owner     = str(row["OWNER"])
    dot_cls   = "matt" if owner == "Matt" else "ryan"
    name      = _html.escape(str(row["PLAYER"]))
    pos       = _html.escape(str(row["POSITION"]) if pd.notna(row["POSITION"]) else "")
    cat       = _html.escape(str(row["CATEGORY"]) if pd.notna(row["CATEGORY"]) else "")
    notes_raw = str(row["NOTES"]) if pd.notna(row["NOTES"]) else ""
    notes     = _html.escape(notes_raw[:80] + ("…" if len(notes_raw) > 80 else ""))

    row_cls = "wc-pick-row pending" if is_pending else "wc-pick-row"

    # Cooked meter column
    if is_pending:
        cm_val = None
        meter_lbl    = '<span class="wc-meter-label" style="color:#3a4450;">TBD</span>'
        meter_bar    = ''
        meter_sub    = ''
    elif is_early:
        cm_val = float(row["COOKED_METER"]) if pd.notna(row["COOKED_METER"]) else 45
        meter_lbl    = f'<span class="wc-meter-label" style="color:#4a6080;">Not counted yet</span>'
        meter_bar    = (f'<div class="wc-meter-bar-bg">'
                        f'<div class="wc-meter-bar-fill" style="width:{cm_val:.0f}%;background:#4a6080;"></div>'
                        f'</div>')
        meter_sub    = ''
    else:
        cm_val = float(row["COOKED_METER"]) if pd.notna(row["COOKED_METER"]) else 50
        wc_score = 100 - cm_val
        meter_lbl    = (f'<span class="wc-meter-label" style="color:{bar_color};">'
                        f'Cooked: {cm_val:.0f}</span>')
        meter_bar    = (f'<div class="wc-meter-bar-bg">'
                        f'<div class="wc-meter-bar-fill" '
                        f'style="width:{cm_val:.0f}%;background:{bar_color};"></div>'
                        f'</div>')
        meter_sub    = f'<div class="wc-meter-sub">WC Score: {wc_score:.0f}</div>'

    # Notes / pending tag
    if is_pending:
        notes_html = f'<span class="wc-pick-pending-tag">not drafted yet</span>'
    elif notes:
        notes_html = f'<span class="wc-pick-notes">{notes}</span>'
    else:
        notes_html = ''

    return (
        f'<div class="{row_cls}">'
        f'  <div class="wc-pick-cat">{cat}</div>'
        f'  <div class="wc-pick-main">'
        f'    <span class="wc-owner-dot {dot_cls}"></span>'
        f'    <div>'
        f'      <span class="wc-pick-name">{name}</span>'
        f'      <span class="wc-pick-pos">{pos}</span>'
        f'      {notes_html}'
        f'    </div>'
        f'  </div>'
        f'  <div class="wc-meter-wrap">{meter_lbl}{meter_bar}{meter_sub}</div>'
        f'  <span class="wc-badge {badge_cls}">{display_lbl}</span>'
        f'</div>'
    )

for _year in _years:
    year_df = df[df["YEAR"] == _year].copy()
    if len(year_df) == 0:
        continue

    # Sort: scored picks best-to-worst (CM asc), then Too Early, then Pending
    def _sort_key(row):
        outcome = row["OUTCOME"]
        if pd.isna(outcome):
            return (2, 100)   # Pending last
        if str(outcome).strip().lower() == "too early":
            return (1, float(row["COOKED_METER"]) if pd.notna(row["COOKED_METER"]) else 99)
        return (0, float(row["COOKED_METER"]) if pd.notna(row["COOKED_METER"]) else 99)

    year_df = year_df.copy()
    year_df["_sort"] = year_df.apply(_sort_key, axis=1)
    year_df = year_df.sort_values("_sort").reset_index(drop=True)

    # Section label suffix
    has_pending = year_df["OUTCOME"].isna().any()
    has_only_pending = year_df["OUTCOME"].notna().sum() == 0
    if has_only_pending:
        suffix = " — Pending"
    elif has_pending:
        suffix = " — In Progress"
    else:
        suffix = ""

    st.markdown(
        f'<div class="wc-section-lbl">{int(_year)} Draft Class{suffix}</div>',
        unsafe_allow_html=True,
    )

    rows_html = "".join(_pick_row_html(row) for _, row in year_df.iterrows())
    st.markdown(rows_html, unsafe_allow_html=True)

if len(df) == 0:
    st.markdown('<div class="wc-empty">No picks found.</div>', unsafe_allow_html=True)
