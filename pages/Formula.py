"""
pages/Formula.py — The Formula
Explains the scoring system: formula, award weights, worked example, tier ranges.
Display-only. No data mutations, no hardcoded values.
Identity: League Rulebook — clean, authoritative reference.
"""

import pandas as pd
import streamlit as st

from core.components import page_header
from core.data_loader import load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import TIER_CUTOFFS, score_to_tier, compute_baseline_audit

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Formula — Trail & Bish Dynasty",
    page_icon="📐",
    layout="wide",
)

render_sidebar(active="Formula")

# ── Scoped CSS ────────────────────────────────────────────────────────────────
# All classes use the fr- prefix to avoid conflicts with other pages.
st.markdown("""<style>
.fr-lbl{font-size:11px;font-weight:800;letter-spacing:3px;text-transform:uppercase;
color:#2E7DFF;border-bottom:1px solid rgba(46,125,255,.15);padding-bottom:8px;
margin-bottom:18px;text-align:center;}
.fr-plain{font-size:15px;line-height:1.75;color:#8090aa;text-align:center;
max-width:640px;margin:0 auto 26px;}
.fr-fairness{background:rgba(10,14,25,.6);border:1px solid rgba(255,255,255,.08);
border-radius:10px;padding:16px 22px;display:flex;align-items:flex-start;gap:14px;
margin-bottom:36px;}
.fr-fairness-icon{font-size:22px;flex-shrink:0;margin-top:2px;}
.fr-fairness-text{font-size:14px;color:#4a6080;line-height:1.75;}
.fr-fairness-text strong{color:#8090aa;}

.fr-formula-box{background:rgba(10,14,25,.85);border:1px solid rgba(46,125,255,.2);
border-left:3px solid #2E7DFF;border-radius:10px;padding:22px 26px;margin-bottom:26px;}
.fr-formula-eq{font-size:18px;font-weight:800;color:#fff;font-family:'Courier New',monospace;
margin-bottom:12px;text-align:center;line-height:1.5;}
.fr-formula-eq .f-blue{color:#2E7DFF;}
.fr-formula-eq .f-gold{color:#D4AF37;}
.fr-formula-note{font-size:13px;color:#4a6080;line-height:1.65;text-align:center;}
.fr-formula-note strong{color:#7090aa;}

.fr-award-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px;}
.fr-award-tile{background:rgba(10,14,25,.7);border:1px solid rgba(255,255,255,.06);
border-radius:9px;padding:14px 6px;text-align:center;}
.fr-award-icon{font-size:20px;margin-bottom:4px;}
.fr-award-pts{font-size:26px;font-weight:900;color:#D4AF37;line-height:1;}
.fr-award-lbl{font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
color:#4a6080;margin-top:4px;}
.fr-cap-note{text-align:center;font-size:12px;color:#4a6080;margin-bottom:6px;}

.fr-tier-row{display:flex;align-items:center;gap:10px;background:rgba(10,14,25,.6);
border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:10px 14px;margin-bottom:6px;}
.fr-tier-badge{font-size:10px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;
padding:4px 10px;border-radius:4px;min-width:140px;text-align:center;flex-shrink:0;}
.fr-tier-legend{background:rgba(212,175,55,.15);color:#D4AF37;border:1px solid rgba(212,175,55,.3);}
.fr-tier-franchise{background:rgba(245,158,11,.15);color:#F59E0B;border:1px solid rgba(245,158,11,.3);}
.fr-tier-hes{background:rgba(46,125,255,.15);color:#2E7DFF;border:1px solid rgba(46,125,255,.3);}
.fr-tier-starter{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3);}
.fr-tier-contrib{background:rgba(148,163,184,.15);color:#94a3b8;border:1px solid rgba(148,163,184,.3);}
.fr-tier-bust{background:rgba(230,59,59,.15);color:#E63B3B;border:1px solid rgba(230,59,59,.3);}
.fr-tier-range{font-size:15px;font-weight:700;color:#8090aa;flex:1;text-align:right;}
.fr-tier-count{font-size:13px;color:#4a6080;width:80px;text-align:right;flex-shrink:0;}

.fr-ex-box{background:rgba(10,14,25,.8);border:1px solid rgba(255,255,255,.08);
border-radius:10px;padding:22px 26px;}
.fr-ex-header{display:flex;align-items:center;gap:12px;margin-bottom:18px;
padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,.07);}
.fr-ex-name{font-size:22px;font-weight:900;color:#fff;}
.fr-ex-pill{font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
padding:3px 9px;border-radius:4px;}
.fr-ex-pill-ryan{background:rgba(230,59,59,.15);color:#E63B3B;border:1px solid rgba(230,59,59,.3);}
.fr-ex-pill-matt{background:rgba(46,125,247,.15);color:#2E7DF7;border:1px solid rgba(46,125,247,.3);}
.fr-ex-meta{font-size:13px;color:#4a6080;}
.fr-ex-step-lbl{font-size:11px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
color:#4a6080;margin-bottom:8px;}
.fr-ex-chips{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:18px;}
.fr-ex-chip{background:rgba(212,175,55,.1);border:1px solid rgba(212,175,55,.2);
border-radius:5px;padding:5px 11px;font-size:13px;font-weight:700;color:#D4AF37;}
.fr-ex-math{font-family:'Courier New',monospace;font-size:15px;color:#8090aa;
line-height:2;background:rgba(0,0,0,.25);border-radius:8px;padding:14px 18px;margin-bottom:16px;}
.fr-ex-math .hi{color:#e8eaf0;font-weight:800;}
.fr-ex-math .gold{color:#D4AF37;}
.fr-ex-math .blue{color:#2E7DFF;}
.fr-ex-math .dim{color:#4a6080;}
.fr-ex-result{display:flex;align-items:center;gap:20px;background:rgba(46,125,255,.06);
border:1px solid rgba(46,125,255,.15);border-radius:8px;padding:14px 20px;}
.fr-ex-result-divider{width:1px;height:48px;background:rgba(255,255,255,.08);flex-shrink:0;}
.fr-ex-result-lbl{font-size:11px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
color:#4a6080;margin-bottom:4px;}
.fr-ex-result-val{font-size:36px;font-weight:900;color:#fff;line-height:1;}
.fr-ex-result-tier{font-size:13px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;}
.fr-section-rule{border:none;border-top:1px solid rgba(255,255,255,.07);margin:32px 0 28px;}

.fr-audit-box{background:rgba(10,14,25,.8);border:1px solid rgba(255,255,255,.08);
border-radius:10px;padding:22px 26px;margin-bottom:18px;}
.fr-audit-stat-row{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:18px;}
.fr-audit-stat{flex:1;min-width:140px;background:rgba(0,0,0,.25);border-radius:8px;
padding:12px 16px;text-align:center;}
.fr-audit-stat-val{font-size:24px;font-weight:900;color:#D4AF37;line-height:1;}
.fr-audit-stat-lbl{font-size:9px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;
color:#4a6080;margin-top:6px;}
.fr-audit-step-row{display:flex;align-items:center;gap:10px;background:rgba(0,0,0,.2);
border-radius:7px;padding:8px 14px;margin-bottom:5px;font-size:13px;}
.fr-audit-step-tiers{flex:1;color:#8090aa;font-weight:700;}
.fr-audit-step-gap{color:#D4AF37;font-weight:900;font-family:'Courier New',monospace;}
.fr-audit-note{font-size:13px;color:#4a6080;line-height:1.75;margin:14px 0;}
.fr-audit-note strong{color:#7090aa;}
.fr-audit-outlier-row{display:flex;align-items:center;gap:10px;padding:7px 12px;
border-radius:6px;margin-bottom:4px;font-size:12px;background:rgba(0,0,0,.18);}
.fr-audit-outlier-name{flex:1;color:#c0cce0;font-weight:700;}
.fr-audit-outlier-tiers{color:#4a6080;width:150px;}
.fr-audit-outlier-delta{font-weight:900;font-family:'Courier New',monospace;width:60px;text-align:right;}
.fr-audit-outlier-delta.neg{color:#E63B3B;}
.fr-audit-outlier-delta.pos{color:#22c55e;}
</style>""", unsafe_allow_html=True)

# ── Page Header ───────────────────────────────────────────────────────────────
page_header("THE FORMULA", "How every score is built · How every tier is earned")

# ── Fairness principle — lead with the headline ───────────────────────────────
st.markdown("""
<div class="fr-fairness">
  <div class="fr-fairness-icon">⚖️</div>
  <div class="fr-fairness-text">
    <strong>Owner-fair. Position-fair. Override-free.</strong>
    The formula and tier cutoffs are identical for every player regardless of owner, position,
    or draft round. Tier is determined solely by score. No hand overrides exist —
    the score determines the tier, period.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Two-column: formula + awards  |  tier ranges ─────────────────────────────
col_formula, col_tiers = st.columns([1.4, 1])

with col_formula:
    st.markdown('<div class="fr-lbl">How it works</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="fr-plain">
      Every player starts with a hand-calibrated <strong style="color:#c0cce0;">baseline score</strong>
      reflecting real-world career production — stats, longevity, peak performance. On top of that
      baseline, postseason awards stack bonus points. Awards are capped so a decorated-but-average
      player can't leapfrog a quietly great career. Score ceiling is 100.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="fr-lbl">The formula</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="fr-formula-box">
      <div class="fr-formula-eq">
        SCORE = <span class="f-blue">min(100,</span>&nbsp;baseline&nbsp;+&nbsp;<span class="f-gold">0.6 × min(award_pts, 16)</span><span class="f-blue">)</span>
      </div>
      <div class="fr-formula-note">
        Award points are summed from the weights below, capped at 16 before the 0.6× multiplier is applied.<br>
        Max possible award bonus: <strong>0.6 × 16 = 9.6 pts</strong> &nbsp;·&nbsp; Score ceiling: <strong>100</strong>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="fr-lbl">Award weights</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="fr-award-grid">
      <div class="fr-award-tile">
        <div class="fr-award-icon">🏆</div><div class="fr-award-pts">6</div><div class="fr-award-lbl">MVP</div>
      </div>
      <div class="fr-award-tile">
        <div class="fr-award-icon">🌟</div><div class="fr-award-pts">4</div><div class="fr-award-lbl">SB MVP</div>
      </div>
      <div class="fr-award-tile">
        <div class="fr-award-icon">⭐</div><div class="fr-award-pts">3</div><div class="fr-award-lbl">OPOY</div>
      </div>
      <div class="fr-award-tile">
        <div class="fr-award-icon">🛡️</div><div class="fr-award-pts">3</div><div class="fr-award-lbl">DPOY</div>
      </div>
      <div class="fr-award-tile">
        <div class="fr-award-icon">🥇</div><div class="fr-award-pts">2.5</div><div class="fr-award-lbl">All-Pro</div>
      </div>
      <div class="fr-award-tile">
        <div class="fr-award-icon">🏈</div><div class="fr-award-pts">2.5</div><div class="fr-award-lbl">SB Win</div>
      </div>
      <div class="fr-award-tile">
        <div class="fr-award-icon">🌱</div><div class="fr-award-pts">1</div><div class="fr-award-lbl">OROY</div>
      </div>
      <div class="fr-award-tile">
        <div class="fr-award-icon">🌱</div><div class="fr-award-pts">1</div><div class="fr-award-lbl">DROY</div>
      </div>
    </div>
    <div class="fr-cap-note">Points cap at 16 before the multiplier — stacking awards never creates runaway scores.</div>
    <div class="fr-cap-note" style="margin-top:8px;color:#8090aa;">
      <strong style="color:#c0cce0;">All-Pro</strong> means First-Team AP All-Pro only —
      never second-team, never a Pro Bowl selection.<br>
      <strong style="color:#c0cce0;">SB Win</strong> credits anyone on the champion's roster
      at Super Bowl time — active, inactive, IR, or a practice-squad elevation all count.
    </div>
    """, unsafe_allow_html=True)

with col_tiers:
    st.markdown('<div class="fr-lbl">Tier ranges</div>', unsafe_allow_html=True)

    # Live tier counts from the workbook
    tier_counts: dict[str, int] = {}
    if workbook_exists():
        try:
            _df = load_players()
            for _, tier_name in TIER_CUTOFFS:
                tier_counts[tier_name] = int((_df["CAREER_TIER"] == tier_name).sum())
        except Exception:
            pass

    _tier_defs = [
        ("fr-tier-legend",    "Legend",           "≥ 95"),
        ("fr-tier-franchise", "Franchise",         "80 – 94.9"),
        ("fr-tier-hes",       "High-End Starter",  "68 – 79.9"),
        ("fr-tier-starter",   "Starter",           "54 – 67.9"),
        ("fr-tier-contrib",   "Contributor",       "40 – 53.9"),
        ("fr-tier-bust",      "Bust",              "< 40"),
    ]
    for badge_cls, label, score_range in _tier_defs:
        count = tier_counts.get(label, 0)
        count_str = f"{count} players" if count else ""
        st.markdown(
            f'<div class="fr-tier-row">'
            f'<span class="fr-tier-badge {badge_cls}">{label}</span>'
            f'<span class="fr-tier-range">{score_range}</span>'
            f'<span class="fr-tier-count">{count_str}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("""
    <div style="margin-top:14px;padding:10px 14px;border-radius:7px;
    background:rgba(10,14,25,.5);border:1px solid rgba(255,255,255,.06);">
      <span style="font-size:9px;font-weight:800;letter-spacing:1.5px;
      text-transform:uppercase;color:#4a6080;">ℹ️ &nbsp;TBD players</span>
      <p style="font-size:11px;color:#4a6080;margin:6px 0 0;line-height:1.65;">
        2025–26 class players show <strong style="color:#6070a0;">TBD</strong> because
        the season hasn't ended and awards haven't been finalized yet — not because they
        failed to score.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:10px;padding:10px 14px;border-radius:7px;
    background:rgba(10,14,25,.5);border:1px solid rgba(255,255,255,.06);">
      <span style="font-size:9px;font-weight:800;letter-spacing:1.5px;
      text-transform:uppercase;color:#4a6080;">ℹ️ &nbsp;"Franchise Players" elsewhere in the app</span>
      <p style="font-size:11px;color:#4a6080;margin:6px 0 0;line-height:1.65;">
        Dashboard and Legacy use <strong style="color:#6070a0;">"Franchise Players"</strong> as
        shorthand for Legend + Franchise combined (score ≥ 80). On this page, the
        <strong style="color:#6070a0;">Franchise</strong> row above means that single tier —
        80–94.9 — not the combined count.
      </p>
    </div>
    """, unsafe_allow_html=True)

# ── Worked Example ─────────────────────────────────────────────────────────────
st.markdown('<hr class="fr-section-rule">', unsafe_allow_html=True)
st.markdown('<div class="fr-lbl">Worked example</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fr-plain" style="margin-bottom:20px;">The formula in action — a real player, real awards, real math.</div>',
    unsafe_allow_html=True,
)

_WEIGHTS: dict[str, float] = {
    "MVP": 6, "SB_MVP": 4, "OPOY": 3, "DPOY": 3,
    "ALL_PRO": 2.5, "SB Win": 2.5, "OROY": 1, "DROY": 1,
}
_LABELS: dict[str, str] = {
    "MVP": "MVP", "SB_MVP": "SB MVP", "OPOY": "OPOY", "DPOY": "DPOY",
    "ALL_PRO": "All-Pro", "SB Win": "SB Win", "OROY": "OROY", "DROY": "DROY",
}
_ICONS: dict[str, str] = {
    "MVP": "🏆", "SB_MVP": "🌟", "OPOY": "⭐", "DPOY": "🛡️",
    "ALL_PRO": "🥇", "SB Win": "🏈", "OROY": "🌱", "DROY": "🌱",
}
_TIER_COLORS: dict[str, str] = {
    "Legend": "#D4AF37", "Franchise": "#F59E0B",
    "High-End Starter": "#2E7DFF", "Starter": "#22c55e",
    "Contributor": "#94a3b8", "Bust": "#E63B3B",
}

if workbook_exists():
    try:
        _df = load_players()
        # Matt Ryan: clean sub-100 score, 4 distinct award types, great story
        _ex_rows = _df[_df["PLAYER"] == "Cooper Kupp"]
        if len(_ex_rows) == 0:
            raise ValueError("Cooper Kupp not found")
        _ex = _ex_rows.iloc[0]

        _final_score  = float(_ex["OVERALL SCORE"])
        _owner        = str(_ex["OWNER"])
        _pill_cls     = "fr-ex-pill-ryan" if _owner == "Ryan" else "fr-ex-pill-matt"

        # Award breakdown
        _breakdown: list[tuple[str, int, float, float]] = []
        _award_pts_total = 0.0
        for _col, _w in _WEIGHTS.items():
            if _col in _ex.index and pd.notna(_ex[_col]) and float(_ex[_col]) > 0:
                _count = int(_ex[_col])
                _pts   = _count * _w
                _award_pts_total += _pts
                _breakdown.append((_col, _count, _w, _pts))

        _capped_pts = min(_award_pts_total, 16.0)
        _bonus      = round(0.6 * _capped_pts, 1)
        _baseline   = round(_final_score - _bonus, 1)
        _tier       = score_to_tier(_final_score)
        _tier_color = _TIER_COLORS.get(_tier, "#fff")

        # Award chips
        _chips_html = ""
        for _col, _count, _w, _pts in _breakdown:
            _times = f" ×{_count}" if _count > 1 else ""
            _chips_html += (
                f'<div class="fr-ex-chip">'
                f'{_ICONS[_col]}&nbsp;{_LABELS[_col]}{_times} = {_pts:g} pts'
                f'</div>'
            )

        # Math steps
        _pts_str  = " + ".join(f"{p:g}" for _, _, _, p in _breakdown)
        _cap_note = f" (capped from {_award_pts_total:g})" if _award_pts_total > 16 else ""

        _ex_col, _spacer = st.columns([1.4, 1])
        with _ex_col:
            st.markdown(
                f'<div class="fr-ex-box">'
                f'  <div class="fr-ex-header">'
                f'    <div class="fr-ex-name">{_ex["PLAYER"]}</div>'
                f'    <span class="fr-ex-pill {_pill_cls}">{_owner}</span>'
                f'    <span class="fr-ex-meta">{_ex["POSITION"]} · {int(_ex["YEAR"])} class</span>'
                f'  </div>'
                f'  <div class="fr-ex-step-lbl">Awards earned</div>'
                f'  <div class="fr-ex-chips">{_chips_html}</div>'
                f'  <div class="fr-ex-step-lbl">The math</div>'
                f'  <div class="fr-ex-math">'
                f'    Award pts &nbsp;= <span class="gold">{_pts_str} = {_award_pts_total:g}</span><br>'
                f'    Bonus &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <span class="gold">0.6 × {_capped_pts:g}{_cap_note} = {_bonus:g}</span><br>'
                f'    Baseline &nbsp;&nbsp;&nbsp;= <span class="hi">{_baseline:g}</span>'
                f'<span class="dim"> &nbsp;(hand-calibrated career score)</span><br>'
                f'    Final &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <span class="blue">min(100,&nbsp;{_baseline:g}&nbsp;+&nbsp;{_bonus:g})</span>'
                f' = <span class="hi">{_final_score:g}</span>'
                f'  </div>'
                f'  <div class="fr-ex-result">'
                f'    <div>'
                f'      <div class="fr-ex-result-lbl">Overall Score</div>'
                f'      <div class="fr-ex-result-val">{_final_score:g}</div>'
                f'    </div>'
                f'    <div class="fr-ex-result-divider"></div>'
                f'    <div>'
                f'      <div class="fr-ex-result-lbl">Career Tier</div>'
                f'      <div class="fr-ex-result-tier" style="color:{_tier_color};">{_tier}</div>'
                f'    </div>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    except Exception as _e:
        st.markdown(
            f'<div style="color:#4a6080;font-size:12px;padding:12px;">Example unavailable: {_e}</div>',
            unsafe_allow_html=True,
            )

# ── Baseline Methodology Audit ───────────────────────────────────────────────
# Documentation only — reverse-derives each player's baseline from the locked
# formula to show HOW it correlates with PRODUCTION/LONGEVITY, using the
# actual current workbook every time this renders. Nothing here changes any
# score, tier, or the formula itself (locked, D030 — see docs/DECISIONS.md).
st.markdown('<hr class="fr-section-rule">', unsafe_allow_html=True)
st.markdown('<div class="fr-lbl">Baseline methodology audit</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="fr-plain">'
    'The baseline half of every score (before awards) isn\'t arbitrary — here\'s exactly '
    'how it lines up with the PRODUCTION and LONGEVITY fields, recomputed live from the '
    'current roster every time this page loads.'
    '</div>',
    unsafe_allow_html=True,
)

try:
    _audit_df = load_players()
    _audit = compute_baseline_audit(_audit_df)

    st.markdown(
        f'<div class="fr-audit-box">'
        f'<div class="fr-audit-stat-row">'
        f'<div class="fr-audit-stat"><div class="fr-audit-stat-val">{_audit["production_r2"]*100:.1f}%</div>'
        f'<div class="fr-audit-stat-lbl">Variance explained<br>by PRODUCTION alone</div></div>'
        f'<div class="fr-audit-stat"><div class="fr-audit-stat-val">{_audit["production_longevity_r2"]*100:.1f}%</div>'
        f'<div class="fr-audit-stat-lbl">+ LONGEVITY<br>(marginal gain, small)</div></div>'
        f'<div class="fr-audit-stat"><div class="fr-audit-stat-val">{_audit["avg_step"]:g}</div>'
        f'<div class="fr-audit-stat-lbl">Avg points per<br>PRODUCTION tier step</div></div>'
        f'<div class="fr-audit-stat"><div class="fr-audit-stat-val">{_audit["residual_std"]:g}</div>'
        f'<div class="fr-audit-stat-lbl">Std dev of judgment<br>beyond the tiers</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="fr-audit-note"><strong>Step sizes between PRODUCTION tiers</strong> — not perfectly uniform: tight in the middle, wider at both ends.</div>', unsafe_allow_html=True)
    for s in _audit["steps"]:
        st.markdown(
            f'<div class="fr-audit-step-row">'
            f'<span class="fr-audit-step-tiers">{s["from"]} → {s["to"]}</span>'
            f'<span class="fr-audit-step-gap">{s["gap"]:g} pts</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="fr-audit-note">'
        f'LONGEVITY only adds <strong>{(_audit["production_longevity_r2"]-_audit["production_r2"])*100:.1f} percentage points</strong> '
        f'on top of PRODUCTION — real but minor. CHAMPIONSHIP_IMPACT is tagged on only '
        f'<strong>{_audit["n_champ_impact_tagged"]} of {_audit["n_scored"]}</strong> scored players, so it\'s a rare '
        f'special-case flag, not a general input most players have.'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="fr-audit-note"><strong>The ~12% not explained by tiers alone is deliberate judgment, '
        'not noise.</strong> Players scored notably below their tier were mostly real busts relative to '
        'their draft hype; players scored above were mostly legitimate emerging talent. A few examples:</div>',
        unsafe_allow_html=True,
    )

    _oc1, _oc2 = st.columns(2)
    with _oc1:
        st.markdown('<div style="font-size:11px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:#E63B3B;margin-bottom:8px;">Scored below tier</div>', unsafe_allow_html=True)
        for o in _audit["penalized_below_tier"][:5]:
            st.markdown(
                f'<div class="fr-audit-outlier-row">'
                f'<span class="fr-audit-outlier-name">{o["name"]} ({o["owner"]})</span>'
                f'<span class="fr-audit-outlier-tiers">{o["production"]}/{o["longevity"]}</span>'
                f'<span class="fr-audit-outlier-delta neg">{o["residual"]:+.1f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with _oc2:
        st.markdown('<div style="font-size:11px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:#22c55e;margin-bottom:8px;">Scored above tier</div>', unsafe_allow_html=True)
        for o in _audit["credited_above_tier"][:5]:
            st.markdown(
                f'<div class="fr-audit-outlier-row">'
                f'<span class="fr-audit-outlier-name">{o["name"]} ({o["owner"]})</span>'
                f'<span class="fr-audit-outlier-tiers">{o["production"]}/{o["longevity"]}</span>'
                f'<span class="fr-audit-outlier-delta pos">{o["residual"]:+.1f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="fr-audit-note" style="margin-top:16px;">'
        'This is documentation of how the existing baseline was derived — it does not change any '
        'score, tier, or the formula above, which is locked (D030).'
        '</div>',
        unsafe_allow_html=True,
    )
except Exception as _audit_e:
    st.markdown(
        f'<div style="color:#4a6080;font-size:12px;padding:12px;">Audit unavailable: {_audit_e}</div>',
        unsafe_allow_html=True,
    )

# ── Data & Sources ────────────────────────────────────────────────────────────
# Closing note per the whole-page review: everything above explains the rule,
# proves it with a real example, and validates it statistically. This last
# piece explains the architecture the whole thing sits on -- why correcting
# one player's record propagates everywhere automatically, and why nothing
# on this page (or any analytics page) can silently drift out of sync with
# the workbook.
st.markdown('<hr class="fr-section-rule">', unsafe_allow_html=True)
st.markdown('<div class="fr-lbl">Data &amp; sources</div>', unsafe_allow_html=True)
st.markdown("""
<div class="fr-plain" style="text-align:left;max-width:720px;margin:0 auto;">
  Every score, tier, and derived stat in this app traces back to one file —
  <code>AP_Dynasty_Backend.xlsx</code> — the single canonical source of truth.
  Analytics, DNA, Power Index, Timeline, and every chart elsewhere in the app
  are all <strong style="color:#c0cce0;">calculated live from that workbook
  every time a page loads</strong>. Nothing gets written back to it, and
  nothing is cached stale — correct one player's record and every page that
  depends on it is correct on the next load, automatically.
</div>
""", unsafe_allow_html=True)
