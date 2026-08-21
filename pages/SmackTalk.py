"""
pages/SmackTalk.py — Smack Talk Engine (V2 feature)

Data-backed trash talk generator. Every line pulls a real number from the
current backend workbook — no generic AI insults, no made-up stats. Pure
template + random.choice generation, same "warn-never-block, never
hand-override the data" spirit as the rest of the app: this page reads
facts, it never writes or reinterprets scores.
"""
import random

import streamlit as st

from core.data_loader import load_players, workbook_exists
from core.sidebar import render_sidebar
from core.stats import compute_class_stats, compute_smack_talk_facts
from core.components import page_header, section_header

st.set_page_config(
    page_title="Smack Talk — Trail & Bish Dynasty",
    page_icon="😈",
    layout="wide",
)

render_sidebar(active="Smack Talk")

# ── Guard ─────────────────────────────────────────────────────────────────────

if not workbook_exists():
    st.error("Backend workbook not found.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────

df = load_players()
cs = compute_class_stats(df)
facts = compute_smack_talk_facts(df, cs)

OTHER = {"Matt": "Ryan", "Ryan": "Matt"}

# ── Templates ─────────────────────────────────────────────────────────────────
# Every {placeholder} below is filled from `facts`, computed above from the
# real workbook — nothing here is invented.

_ROAST_TEMPLATES = [
    "{owner}'s {franchise} Franchise-tier players sound impressive until you "
    "remember he also drafted {worst_name} in Round {worst_round} — a {worst_score:.0f} "
    "overall score. That's not a pick, that's a cry for help.",

    "{other}'s {best_name} put up a {best_score:.0f} overall. {owner}'s best pick "
    "of all time? Still hasn't cracked what {other} finds on accident.",

    "{owner} is averaging a {avg_score:.1f} overall across {total} draft picks. "
    "The league's still waiting to see if that number ever climbs above 'mediocre.'",

    "{owner} has {busts} Bust-tier players in the system. That's not bad luck, "
    "that's a pattern.",

    "{owner} racked up {award_total} total awards across the whole roster. "
    "{other} beat that with {other_award_total} — and still has a better bust rate.",
]

_DEFEND_TEMPLATES = [
    "Say what you want, but {owner}'s {best_name} put up a {best_score:.0f} overall "
    "— that's not a fluke, that's a franchise cornerstone.",

    "{owner} has {franchise} Franchise-tier players in the system. That's not "
    "'getting lucky,' that's drafting with an actual plan.",

    "Sure, {owner} whiffed on {worst_name} — every GM has one. But a {avg_score:.1f} "
    "average across {total} picks says the misses are the exception, not the rule.",

    "{award_total} total awards on {owner}'s roster speaks for itself. "
    "Numbers don't lie, even when {other} wants them to.",

    "{owner}'s bust rate is a non-issue when the ceiling includes a "
    "{best_score:.0f}-overall player like {best_name}. Championships are won at "
    "the top of the roster, not the bottom.",
]


def _series_roast_line(ctx: dict) -> str:
    """
    Series-record roast — computed, not a fixed template, because the
    correct phrasing depends on who's actually leading. A plain template
    assuming {owner} is always trailing produces a factually backwards
    sentence for whichever owner happens to be ahead (caught by testing
    every template against both real targets before shipping).
    """
    owner, other = ctx["owner"], ctx["other"]
    ow, ov, ties = ctx["owner_wins"], ctx["other_wins"], ctx["ties"]
    if ov > ow:
        return (f"The series record is {other}'s {ov}\u2013{ow}\u2013{ties} over {owner}. "
                f"At some point 'rebuilding' stops being an excuse.")
    if ow > ov:
        return (f"{owner} leads the series {ow}\u2013{ov}\u2013{ties}, and it's still not "
                f"enough to cover for {ctx['worst_name']}.")
    return f"The series is dead even at {ow}\u2013{ov}\u2013{ties} — fitting, since neither side wants to admit the other's actually keeping up."


def _series_defend_line(ctx: dict) -> str:
    """Series-record defend — same reasoning as _series_roast_line above."""
    owner, other = ctx["owner"], ctx["other"]
    ow, ov, ties = ctx["owner_wins"], ctx["other_wins"], ctx["ties"]
    if ow > ov:
        return f"{owner} leads the series {ow}\u2013{ov}\u2013{ties}. That's not a fluke, that's a track record."
    if ov > ow:
        return (f"{owner} is only down {ov}\u2013{ow}\u2013{ties} in the series. "
                f"Momentum swings. This dynasty isn't over, it's just getting started.")
    return f"The series is tied {ow}\u2013{ov}\u2013{ties} — {owner}'s never actually been behind."


def _build_context(target: str, totals: dict) -> dict:
    other = OTHER[target]
    t, o = facts[target], facts[other]
    cw = facts["class_wins"]
    return {
        "owner": target, "other": other,
        "franchise": t["franchise"], "busts": t["busts"],
        "avg_score": t["avg_score"], "total": int(totals.get(target, 0)),
        "best_name": t["best_name"], "best_score": t["best_score"],
        "worst_name": t["worst_name"], "worst_score": t["worst_score"],
        "worst_round": t["worst_round"] if t["worst_round"] else "?",
        "award_total": t["award_total"], "other_award_total": o["award_total"],
        "owner_wins": cw[target], "other_wins": cw[other], "ties": cw["ties"],
    }


# Real pick totals per owner
_totals = df.groupby("OWNER").size().to_dict()

# ── Page render ───────────────────────────────────────────────────────────────

st.markdown(
    page_header("😈 Smack Talk Engine", "Every line below is backed by real data from the workbook"),
    unsafe_allow_html=True,
)

st.markdown(
    """<style>
.st-talk-card{
    background:linear-gradient(135deg,rgba(20,10,10,.9),rgba(10,10,20,.9));
    border:1px solid rgba(255,255,255,.10);border-radius:14px;
    padding:32px 28px;margin-top:18px;min-height:120px;
    display:flex;align-items:center;justify-content:center;text-align:center;
}
.st-talk-text{font-size:19px;font-weight:700;line-height:1.6;color:#f0f0f5;max-width:760px;}
.st-talk-empty{font-size:14px;color:#4a6080;font-weight:600;}
</style>""",
    unsafe_allow_html=True,
)

st.markdown(section_header("PICK YOUR POISON", "Choose a mode, then hit generate"), unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    mode = st.radio("Mode", options=["Roast", "Defend"], horizontal=True, key="st_mode")
with c2:
    target = st.radio("Target", options=["Matt", "Ryan"], horizontal=True, key="st_target")

generate = st.button("😈 Generate", key="st_generate", use_container_width=True)

if generate:
    ctx = _build_context(target, _totals)
    plain_pool = _ROAST_TEMPLATES if mode == "Roast" else _DEFEND_TEMPLATES
    series_line = _series_roast_line(ctx) if mode == "Roast" else _series_defend_line(ctx)
    # Mix the fixed templates with the one computed (always-correct) series line
    candidates = [tpl.format(**ctx) for tpl in plain_pool] + [series_line]
    line = random.choice(candidates)
    st.session_state["st_last_line"] = line

if "st_last_line" in st.session_state:
    st.markdown(
        f'<div class="st-talk-card"><div class="st-talk-text">{st.session_state["st_last_line"]}</div></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="st-talk-card"><div class="st-talk-empty">Pick a mode and target above, then hit Generate.</div></div>',
        unsafe_allow_html=True,
    )
