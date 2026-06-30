"""
core/stats.py

Single computation layer for all aggregated statistics.

Every page that needs league or owner stats imports from here.
This guarantees:
  • Consistent numbers across every page simultaneously
  • A single place to fix or extend any stat definition
  • Zero duplicated derivation logic in page files

Design rule: functions here are pure (DataFrame in → dict out).
No Streamlit imports. No side effects.
"""

from __future__ import annotations

import pandas as pd

from core.utils import is_score_pending


# ---------------------------------------------------------------------------
# Shared constants — tier system
# ---------------------------------------------------------------------------

# Six score-derived tiers.  Every player's CAREER_TIER is computed from their
# OVERALL SCORE using these cutoffs — no per-player hand-overrides, ever.
# The boundaries are locked (D032).  Only inputs (scores) change going forward.
TIER_CUTOFFS: list[tuple[float, str]] = [
    (95.0, "Legend"),
    (80.0, "Franchise"),
    (68.0, "High-End Starter"),
    (54.0, "Starter"),
    (40.0, "Contributor"),
    (0.0,  "Bust"),
]

# Tiers treated as "top-tier franchise-quality" players for aggregate counts.
# Legend + Franchise = every player who scored 80+.
FRANCHISE_TIERS: frozenset[str] = frozenset({"Legend", "Franchise"})


def score_to_tier(score: float) -> str:
    """
    Map an OVERALL SCORE to its canonical tier name.

    This is the single definition of tier boundaries.  CAREER_TIER is
    derived from OVERALL SCORE in load_players() — the workbook column
    is overwritten on every load.  No per-player overrides exist.

    Parameters
    ----------
    score:
        OVERALL SCORE value.  Must be a finite float; NaN / pending
        players should be handled by the caller before calling this.

    Returns
    -------
    One of: 'Legend' | 'Franchise' | 'High-End Starter' |
            'Starter' | 'Contributor' | 'Bust'
    """
    for cutoff, name in TIER_CUTOFFS:
        if score >= cutoff:
            return name
    return "Bust"


# ---------------------------------------------------------------------------
# Shared constants — position groups
# ---------------------------------------------------------------------------

# Canonical position-group mapping.  Mirrors the actual POSITION values in
# the `players` sheet.  Pages that need an "All" option add it locally.
POSITION_GROUPS: dict[str, list[str]] = {
    "QB":      ["QB"],
    "RB":      ["RB"],
    "WR":      ["WR"],
    "TE":      ["TE"],
    "OL":      ["OL", "OT", "OG", "C"],
    "EDGE/DE": ["EDGE", "DE"],
    "DT":      ["DT"],
    "LB":      ["LB", "ILB", "OLB"],
    "CB":      ["CB"],
    "SS":      ["SS"],
    "FS":      ["FS"],
    "S":       ["S"],
}

# Minimum number of scored players required for an average to be displayed
# without a sample-size caveat.  Below this threshold, the UI must show (n=X)
# alongside the average so viewers know the stat is small-sample.
# Decision: defined here (stats layer), never computed ad hoc in page files.
MIN_RANKED_SAMPLE: int = 5


# ---------------------------------------------------------------------------
# League-wide stats
# ---------------------------------------------------------------------------

def compute_league_stats(df: pd.DataFrame) -> dict:
    """
    Compute all league-wide aggregate statistics from the players DataFrame.

    Returns a flat dict of typed, safe values — no NaN, no None.
    Pages should destructure only the keys they need; the dict is intentionally
    broad so future pages rarely need to touch this module for basic stats.

    Parameters
    ----------
    df:
        Raw players DataFrame from ``load_players()``.
    """
    scored    = df.dropna(subset=["OVERALL SCORE"])
    year_avg  = df.groupby("YEAR")["OVERALL SCORE"].mean()
    best_year = int(year_avg.idxmax())

    return {
        # Counts
        "total_players":   int(len(df)),
        "draft_classes":   int(df["YEAR"].nunique()),
        "positions":       int(df["POSITION"].nunique()),
        "franchise_total": int(df["CAREER_TIER"].isin(FRANCHISE_TIERS).sum()),
        "bust_total":      int((df["CAREER_TIER"] == "Bust").sum()),
        # Scoring
        "avg_score":       float(scored["OVERALL SCORE"].mean()),
        "high_score":      int(scored["OVERALL SCORE"].max()),
        "low_score":       int(scored["OVERALL SCORE"].min()),
        "avg_round":       float(df["ROUND"].mean()),
        # Draft class
        "best_year":       best_year,
        "best_year_avg":   float(year_avg[best_year]),
        "year_range":      f"{int(df['YEAR'].min())}–{int(df['YEAR'].max())}",
    }


# ---------------------------------------------------------------------------
# Per-owner stats
# ---------------------------------------------------------------------------

def compute_owner_stats(df: pd.DataFrame, owner: str) -> dict:
    """
    Compute per-owner statistics.

    Parameters
    ----------
    df:    Raw players DataFrame from ``load_players()``.
    owner: ``"Matt"`` or ``"Ryan"``.
    """
    odf    = df[df["OWNER"] == owner]
    scored = odf.dropna(subset=["OVERALL SCORE"])

    return {
        "owner":      owner,
        "total":      int(len(odf)),
        "avg_score":  float(scored["OVERALL SCORE"].mean()) if len(scored) else 0.0,
        "franchise":  int(odf["CAREER_TIER"].isin(FRANCHISE_TIERS).sum()),
        "busts":      int((odf["CAREER_TIER"] == "Bust").sum()),
        "high_score": int(scored["OVERALL SCORE"].max()) if len(scored) else 0,
    }


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def score_leader(
    matt_stats: dict,
    ryan_stats: dict,
) -> tuple[str, float]:
    """Return ``(leader_name, avg_score_delta)``."""
    delta  = abs(matt_stats["avg_score"] - ryan_stats["avg_score"])
    leader = "Matt" if matt_stats["avg_score"] >= ryan_stats["avg_score"] else "Ryan"
    return leader, delta


# ---------------------------------------------------------------------------
# Ranking helpers  (used by Rankings page — derives from players, not the sheet)
# ---------------------------------------------------------------------------

def rank_players(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return the players DataFrame sorted by OVERALL SCORE descending, with a
    RANK column prepended.

    Pending (NaN-score) players are appended at the end, unranked (RANK = 0).

    Decision D005: Rankings derived from players sheet, not the AP Rankings
    sheet, which is a non-tabular human-readable reporting layout.
    """
    scored  = df.dropna(subset=["OVERALL SCORE"]).sort_values(
        "OVERALL SCORE", ascending=False
    ).reset_index(drop=True)
    pending = df[df["OVERALL SCORE"].apply(is_score_pending)].copy()

    scored["RANK"]  = scored.index + 1
    pending["RANK"] = 0

    return pd.concat([scored, pending], ignore_index=True)


def rank_players_by_position(
    df: pd.DataFrame,
    position: str | list[str],
) -> pd.DataFrame:
    """
    Return scored + ranked players for a position or position group.

    Parameters
    ----------
    df:
        Raw players DataFrame.
    position:
        A single POSITION value (``"QB"``) or a list of values that form a
        group (e.g. ``["OL", "OT", "OG", "C"]`` for the OL group).
        Pass values from ``POSITION_GROUPS`` directly.
    """
    if isinstance(position, list):
        pos_df = df[df["POSITION"].isin(position)]
    else:
        pos_df = df[df["POSITION"] == position]
    return rank_players(pos_df)


# ---------------------------------------------------------------------------
# Draft War Room — class-level stats
# ---------------------------------------------------------------------------

def class_grade(avg_score: float) -> str:
    """
    Return a letter grade (S / A / B / C / D) for a draft class.

    Thresholds are calibrated against actual data:
      best class avg = 76.25 (2008), league avg = 57.11.

    Decision: business rule lives here (not in components) so any page
    consuming grades uses the same definition.
    """
    if avg_score >= 68: return "S"
    if avg_score >= 60: return "A"
    if avg_score >= 52: return "B"
    if avg_score >= 44: return "C"
    return "D"


def compute_class_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-(year, owner) statistics for the Draft War Room page.

    Returns a DataFrame with one row per (YEAR, OWNER) pair and columns:
      YEAR, OWNER, total, scored, avg_score, franchise, busts, grade.

    Pending players (NaN OVERALL SCORE) are counted in ``total`` but
    excluded from ``scored``, ``avg_score``, and ``grade``.
    """
    rows = []
    for year in sorted(df["YEAR"].unique()):
        year_df = df[df["YEAR"] == year]
        for owner in ["Matt", "Ryan"]:
            owner_df = year_df[year_df["OWNER"] == owner]
            scored   = owner_df.dropna(subset=["OVERALL SCORE"])
            avg      = float(scored["OVERALL SCORE"].mean()) if len(scored) else 0.0
            rows.append({
                "YEAR":      int(year),
                "OWNER":     owner,
                "total":     int(len(owner_df)),
                "scored":    int(len(scored)),
                "avg_score": avg,
                "franchise": int(owner_df["CAREER_TIER"].isin(FRANCHISE_TIERS).sum()),
                "busts":     int((owner_df["CAREER_TIER"] == "Bust").sum()),
                "grade":     class_grade(avg) if len(scored) else "—",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Legacy Center — computed exhibit data (all derive from players sheet)
# ---------------------------------------------------------------------------

_AWARD_COLS: list[str] = ["MVP", "OPOY", "DPOY", "OROY", "DROY", "ALL_PRO", "SB Win", "SB_MVP"]


def compute_award_totals(df: pd.DataFrame) -> dict[str, int]:
    """Dynasty-wide total instances of each award column across all players."""
    return {col: int(df[col].fillna(0).sum()) for col in _AWARD_COLS if col in df.columns}


def compute_mount_rushmore(df: pd.DataFrame) -> dict[str, list[dict]]:
    """Top 4 scored players per owner — the computed dynasty Mount Rushmore."""
    scored = df.dropna(subset=["OVERALL SCORE"])
    return {
        owner: (
            scored[scored["OWNER"] == owner]
            .sort_values("OVERALL SCORE", ascending=False)
            .head(4)
            .to_dict("records")
        )
        for owner in ["Matt", "Ryan"]
    }


def compute_all_franchise(df: pd.DataFrame) -> dict[str, dict]:
    """Best scored player per position group per owner — the All-Franchise squad."""
    scored = df.dropna(subset=["OVERALL SCORE"])
    result: dict[str, dict] = {}
    for pos_label, pos_values in POSITION_GROUPS.items():
        pos_df = scored[scored["POSITION"].isin(pos_values)]
        entry: dict = {}
        for owner in ["Matt", "Ryan"]:
            owner_pos = pos_df[pos_df["OWNER"] == owner]
            entry[owner] = (
                owner_pos.sort_values("OVERALL SCORE", ascending=False).iloc[0].to_dict()
                if len(owner_pos)
                else None
            )
        result[pos_label] = entry
    return result


def compute_hall_of_fame(df: pd.DataFrame) -> pd.DataFrame:
    """All Legend + Franchise tier players sorted by OVERALL SCORE descending."""
    return (
        df[df["CAREER_TIER"].isin(FRANCHISE_TIERS)]
        .dropna(subset=["OVERALL SCORE"])
        .sort_values("OVERALL SCORE", ascending=False)
        .reset_index(drop=True)
    )


def compute_greatest_classes(df: pd.DataFrame, n: int = 5) -> list[dict]:
    """Top n draft classes ranked by combined (Matt + Ryan) average score."""
    cs = compute_class_stats(df)
    combined = cs.groupby("YEAR")["avg_score"].mean()
    top_years = combined.sort_values(ascending=False).head(n).index.tolist()
    result = []
    for rank, year in enumerate(top_years, 1):
        avg = float(combined[year])
        yr = cs[cs["YEAR"] == year]
        m_avg = float(yr[yr["OWNER"] == "Matt"]["avg_score"].values[0])
        r_avg = float(yr[yr["OWNER"] == "Ryan"]["avg_score"].values[0])
        winner = "Matt" if m_avg > r_avg else "Ryan" if r_avg > m_avg else "Tie"
        result.append({
            "rank": rank, "year": int(year), "combined_avg": avg,
            "grade": class_grade(avg), "matt_avg": m_avg, "ryan_avg": r_avg, "winner": winner,
        })
    return result


def compute_legacy_moments(df: pd.DataFrame) -> list[dict]:
    """Five milestone facts derived algorithmically from live workbook data."""
    moments: list[dict] = []
    scored = df.dropna(subset=["OVERALL SCORE"]).sort_values("OVERALL SCORE", ascending=False)

    top1 = scored.iloc[0]
    moments.append({
        "text": f"{top1['PLAYER']} leads the all-time GOAT Race · Score {int(top1['OVERALL SCORE'])}",
        "owner": str(top1["OWNER"]),
    })

    cs = compute_class_stats(df)
    combined = cs.groupby("YEAR")["avg_score"].mean()
    best_yr = int(combined.idxmax())
    moments.append({
        "text": f"{best_yr} is the greatest draft class in dynasty history · Avg {float(combined.max()):.1f}",
        "owner": "Dynasty",
    })

    matt_avg = float(scored[scored["OWNER"] == "Matt"]["OVERALL SCORE"].mean())
    ryan_avg = float(scored[scored["OWNER"] == "Ryan"]["OVERALL SCORE"].mean())
    lead = "Ryan" if ryan_avg > matt_avg else "Matt"
    moments.append({
        "text": f"{lead} leads the all-time rivalry with a +{abs(ryan_avg - matt_avg):.1f} avg score edge",
        "owner": lead,
    })

    valid_cols = [c for c in _AWARD_COLS if c in df.columns]
    award_sums = df[valid_cols].fillna(0).sum(axis=1)
    idx = int(award_sums.idxmax())
    decorated = df.loc[idx]
    n_awards = int(award_sums[idx])
    if n_awards > 0:
        moments.append({
            "text": f"{decorated['PLAYER']} is the most decorated with {n_awards} career awards",
            "owner": str(decorated["OWNER"]),
        })

    franchise_count = int(df["CAREER_TIER"].isin(FRANCHISE_TIERS).sum())
    moments.append({
        "text": f"Dynasty milestone: {franchise_count} Franchise players across {int(df['YEAR'].nunique())} classes",
        "owner": "Dynasty",
    })

    return moments


# ---------------------------------------------------------------------------
# Man Status — series aggregates (source: man status sheet via load_man_status)
# ---------------------------------------------------------------------------

# Sentinel constants matching the exact WINNER strings in the workbook.
# Verified 2026-06-28: Matt / Ryan / Tie / Pending.  Never branch on raw literals.
_MS_MATT    = "Matt"
_MS_RYAN    = "Ryan"
_MS_TIE     = "Tie"
_MS_PENDING = "Pending"


def ms_winner_state(winner_val: str) -> str:
    """
    Normalise a WINNER cell to one of four canonical states.

    Returns 'Matt' | 'Ryan' | 'Tie' | 'Pending'.
    Any unrecognised value is treated as Pending.
    """
    s = str(winner_val).strip()
    if s == _MS_MATT:    return "Matt"
    if s == _MS_RYAN:    return "Ryan"
    if s == _MS_TIE:     return "Tie"
    return "Pending"


def compute_ms_summary(ms_df: pd.DataFrame) -> dict:
    """
    Compute Man Status series-level aggregates from the 20-row man status sheet.

    All tallies are read from the WINNER column — never recomputed from scores.
    Streak calculations exclude Tie and Pending rows (decisive wins only).

    Returns
    -------
    dict with keys: matt_wins, ryan_wins, ties, pending, leader,
    cur_streak_owner, cur_streak_len, best_streak_owner, best_streak_len,
    biggest_margin, biggest_margin_year, biggest_margin_winner,
    closest_margin, closest_margin_year, closest_margin_winner,
    featured_bout_year (most recent decisive non-tie bout).
    """
    matt_wins = ryan_wins = ties = pending = 0
    for _, row in ms_df.iterrows():
        state = ms_winner_state(str(row["WINNER"]))
        if state == "Matt":   matt_wins += 1
        elif state == "Ryan": ryan_wins += 1
        elif state == "Tie":  ties += 1
        else:                 pending += 1

    leader = (
        "Ryan" if ryan_wins > matt_wins
        else "Matt" if matt_wins > ryan_wins
        else "Tie"
    )

    # Streaks — decisive bouts only (Tie and Pending excluded as non-wins)
    decisive = (
        ms_df[ms_df["WINNER"].isin([_MS_MATT, _MS_RYAN])]
        .sort_values("YEAR")
        .reset_index(drop=True)
    )

    cur_owner = best_owner = ""
    cur_len   = best_len  = 0
    for _, row in decisive.iterrows():
        w = str(row["WINNER"])
        if w == cur_owner:
            cur_len += 1
        else:
            cur_owner = w
            cur_len   = 1
        if cur_len > best_len:
            best_len  = cur_len
            best_owner = cur_owner

    # Margin extremes — decisive bouts only
    margined = decisive[decisive["MARGIN"].notna()].copy()
    margined["MARGIN"] = margined["MARGIN"].astype(float)
    big_row   = margined.loc[margined["MARGIN"].idxmax()] if len(margined) else None
    close_row = margined.loc[margined["MARGIN"].idxmin()] if len(margined) else None

    # Featured bout = highest YEAR among decisive bouts — explicit max, not sort-order dependent
    featured_year = int(decisive["YEAR"].max()) if len(decisive) else 0

    return {
        "matt_wins":            matt_wins,
        "ryan_wins":            ryan_wins,
        "ties":                 ties,
        "pending":              pending,
        "leader":               leader,
        "cur_streak_owner":     cur_owner,
        "cur_streak_len":       cur_len,
        "best_streak_owner":    best_owner,
        "best_streak_len":      best_len,
        "biggest_margin":       round(float(big_row["MARGIN"]), 1)  if big_row   is not None else 0,
        "biggest_margin_year":  int(big_row["YEAR"])        if big_row   is not None else 0,
        "biggest_margin_winner":str(big_row["WINNER"])      if big_row   is not None else "",
        "closest_margin":       round(float(close_row["MARGIN"]), 1)  if close_row is not None else 0,
        "closest_margin_year":  int(close_row["YEAR"])      if close_row is not None else 0,
        "closest_margin_winner":str(close_row["WINNER"])    if close_row is not None else "",
        "featured_bout_year":   featured_year,
    }


def compute_series_record(class_stats: pd.DataFrame) -> dict:
    """
    Compute the all-time Matt vs Ryan series record from class stats.

    A class is won by the owner with the higher ``avg_score`` among scored
    picks.  Classes where neither owner has scored picks yet (2025–26) are
    excluded from the record.

    Returns
    -------
    dict with keys: matt_wins, ryan_wins, ties, total_decided.
    """
    matt_wins = ryan_wins = ties = 0

    for year in class_stats["YEAR"].unique():
        year_data = class_stats[class_stats["YEAR"] == year]
        m = year_data[year_data["OWNER"] == "Matt"]
        r = year_data[year_data["OWNER"] == "Ryan"]

        if len(m) == 0 or len(r) == 0:
            continue

        # Skip classes with no scored picks at all
        if m.iloc[0]["scored"] == 0 and r.iloc[0]["scored"] == 0:
            continue

        m_avg = m.iloc[0]["avg_score"]
        r_avg = r.iloc[0]["avg_score"]

        if m_avg > r_avg:
            matt_wins += 1
        elif r_avg > m_avg:
            ryan_wins += 1
        else:
            ties += 1

    return {
        "matt_wins":     matt_wins,
        "ryan_wins":     ryan_wins,
        "ties":          ties,
        "total_decided": matt_wins + ryan_wins + ties,
    }
