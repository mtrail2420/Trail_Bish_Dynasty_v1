"""
core/utils.py

Pure utility functions with no Streamlit or workbook dependencies.

These are safe to import from any module without circular import risk.
All functions are side-effect free and stateless.
"""

from __future__ import annotations

import math

# ── League year constants (centralized D-XXX) ──────────────────────────────
# The single source of truth for "what year is it" across the app. Bump
# CURRENT_YEAR (and nothing else) during the annual update — every page
# that shows the current/pending draft class reads from here instead of
# a hardcoded literal, so next year's refresh is a one-line change.
FIRST_YEAR: int = 2007
CURRENT_YEAR: int = 2026
YEAR_RANGE: str = f"{FIRST_YEAR}–{CURRENT_YEAR}"
CURRENT_CLASS: int = CURRENT_YEAR  # the pending/not-yet-scored draft class


def safe_int(val, default: int = 0) -> int:
    """Convert *val* to int, returning *default* for NaN / None / non-numeric."""
    try:
        f = float(val)
        return int(f) if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


UDFA_ROUND: int = 8
"""Sentinel value stored in the ROUND column for undrafted free agents.

The real NFL draft only has 7 rounds, so 8 can never collide with a real
pick. It's deliberately >= 4 so UDFA players are eligible for "late-round
steal" comparisons across the app (an undrafted player who becomes a
stud is the ultimate value story) while `format_round()` below ensures
it is never displayed as the literal, nonexistent "Round 8" — it always
renders as "UDFA".
"""


def format_round(round_val, spelled_out: bool = False) -> str:
    """Format a ROUND value for display: 'Rd 3' / 'Round 3', 'UDFA', or '—'.

    Use *spelled_out* for surfaces that write out "Round" in full
    (player_detail_card, legacy_spotlight_card); leave it False for the
    abbreviated "Rd" form used in compact rows and comparison chips.
    """
    r = safe_int(round_val, default=0)
    if r == UDFA_ROUND:
        return "UDFA"
    if r >= 1:
        return f"Round {r}" if spelled_out else f"Rd {r}"
    return "—"


def safe_str(val) -> str:
    """Convert *val* to str, returning ``""`` for NaN / None / the literal strings."""
    s = str(val)
    return "" if s in ("nan", "None", "") else s


def fmt_score(score, pending_str: str = "—") -> str:
    """Format an OVERALL SCORE for display.

    Returns one decimal place, trailing '.0' stripped:
      95.8 → '95.8' · 100.0 → '100' · 91.0 → '91'

    Returns *pending_str* when the score is absent/invalid (NaN, None, etc.).
    Use for any surface that shows OVERALL SCORE as a number.
    """
    try:
        f = float(score)
    except (TypeError, ValueError):
        return pending_str
    if not math.isfinite(f):
        return pending_str
    v = max(0.0, min(100.0, f))
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def is_score_pending(score) -> bool:
    """
    Return ``True`` when a score is absent.

    Used for 2025–26 draft picks whose careers have not yet produced a score.
    A score of 0 is valid (Bust tier); only NaN / None / non-numeric qualify
    as pending.
    """
    try:
        return not math.isfinite(float(score))
    except (TypeError, ValueError):
        return True
