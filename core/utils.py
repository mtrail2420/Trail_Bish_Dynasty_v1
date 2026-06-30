"""
core/utils.py

Pure utility functions with no Streamlit or workbook dependencies.

These are safe to import from any module without circular import risk.
All functions are side-effect free and stateless.
"""

from __future__ import annotations

import math


def safe_int(val, default: int = 0) -> int:
    """Convert *val* to int, returning *default* for NaN / None / non-numeric."""
    try:
        f = float(val)
        return int(f) if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


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
