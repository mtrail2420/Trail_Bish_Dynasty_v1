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

from core.utils import is_score_pending, UDFA_ROUND, format_round, FIRST_YEAR, fmt_score


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

def _owner_aggregate(sub_df: pd.DataFrame) -> dict:
    """
    Core owner-level aggregate primitive over whatever roster slice is
    passed in -- the whole dynasty, one owner's picks, one owner's picks
    through a given year, etc. Shared foundation for compute_owner_stats()
    (whole-dynasty-to-date slice) and compute_cumulative_power() (an
    expanding year-by-year slice).

    These two answer conceptually different questions -- "what are this
    owner's aggregate stats" vs. "how has cumulative power changed over
    time" -- and deliberately remain separate functions rather than one
    depending on the other's output, per the consolidation decision in
    project chat: they happen to agree at the latest data point today,
    but that's a consequence of both being correct, not a reason to
    couple two conceptually distinct questions together. What they
    actually share is the underlying arithmetic, which lives here once.

    Returns {total, scored_count, avg_score, franchise, busts, high_score}.
    `total` counts every row passed in (scored or not); `scored_count` and
    `avg_score`/`high_score` only consider rows with a real OVERALL SCORE.
    """
    scored = sub_df.dropna(subset=["OVERALL SCORE"])
    return {
        "total":        int(len(sub_df)),
        "scored_count": int(len(scored)),
        "avg_score":    float(scored["OVERALL SCORE"].mean()) if len(scored) else 0.0,
        "franchise":    int(sub_df["CAREER_TIER"].isin(FRANCHISE_TIERS).sum()),
        "busts":        int((sub_df["CAREER_TIER"] == "Bust").sum()),
        "high_score":   int(scored["OVERALL SCORE"].max()) if len(scored) else 0,
    }


def compute_owner_stats(df: pd.DataFrame, owner: str) -> dict:
    """
    Compute per-owner statistics (whole dynasty, to date).

    Parameters
    ----------
    df:    Raw players DataFrame from ``load_players()``.
    owner: ``"Matt"`` or ``"Ryan"``.
    """
    odf = df[df["OWNER"] == owner]
    agg = _owner_aggregate(odf)
    return {
        "owner":      owner,
        "total":      agg["total"],
        "avg_score":  agg["avg_score"],
        "franchise":  agg["franchise"],
        "busts":      agg["busts"],
        "high_score": agg["high_score"],
    }


# ---------------------------------------------------------------------------
# Dynasty DNA / Draft Efficiency — shared drafting-identity engine
# ---------------------------------------------------------------------------
#
# Built as ONE feature, not two separate ones (see the roadmap discussion
# in project chat, and docs/DECISIONS.md if this gets a D-number). Dynasty
# DNA and Draft Efficiency were originally proposed as separate ideas, but
# they compute the same underlying thing: round/position/era performance,
# grouped by owner. Any future feature needing that breakdown (Power Index,
# "Why Is Ryan Winning", Era Analysis, Position Dynasty Analysis) should
# call compute_draft_dna() rather than recomputing its own version — that's
# the whole point of building it once here instead of four times across
# four pages.

DRAFT_ERAS: list[tuple[str, int, int]] = [
    ("2007–2011", 2007, 2011),
    ("2012–2016", 2012, 2016),
    ("2017–2021", 2017, 2021),
    ("2022–2026", 2022, 2026),
]
"""Four 5-year eras spanning the dynasty's full draft history so far.
Revisit during the annual update once 2027 data exists -- either extend
the last era or add a fifth, whichever reads best once there's enough
data in it to be meaningful. Deliberately not auto-computed from
CURRENT_YEAR: era boundaries are a judgment call, not a formula."""

# Tiers counted as a "hit" for late-round-hit-rate purposes: Starter or
# better. Contributor and Bust are not hits -- they made the roster, but
# a late-round "hit" story needs the player actually panning out.
_HIT_TIERS: frozenset[str] = frozenset(
    {"Legend", "Franchise", "High-End Starter", "Starter"}
)


def compute_draft_dna(df: pd.DataFrame, owner: str) -> dict:
    """
    Compute one owner's "drafting identity": strongest/weakest position,
    best/worst round, best/worst era, late-round hit rate, franchise
    conversion rate, and bust rate.

    This is the shared analytical engine for Dynasty DNA / Draft
    Efficiency. Buckets with fewer than MIN_RANKED_SAMPLE scored players
    are excluded from best/worst selection (but still appear in the raw
    breakdown dicts) so a single lucky or unlucky pick can't crown an
    entire round or era.

    Parameters
    ----------
    df:    Raw players DataFrame from ``load_players()``.
    owner: "Matt" or "Ryan".

    Returns
    -------
    dict with keys:
      total, position, round, era  (raw breakdowns: label -> {avg, n})
      best_position, worst_position, best_round, worst_round,
      best_era, worst_era          (each {name, avg, n}, or None)
      late_round_hit_rate          (0-100, % of Round 4+/UDFA picks
                                     that reached Starter tier or better)
      first_round_avg, late_round_avg
      franchise_conversion_rate, bust_rate   (0-100)
    """
    odf    = df[df["OWNER"] == owner]
    scored = odf.dropna(subset=["OVERALL SCORE"])
    total  = int(len(odf))

    def _bucket_stats(sub_df: pd.DataFrame) -> dict:
        return {
            "avg": float(sub_df["OVERALL SCORE"].mean()) if len(sub_df) else 0.0,
            "n":   int(len(sub_df)),
        }

    def _best_worst(buckets: dict[str, dict]) -> tuple[dict | None, dict | None]:
        eligible = {k: v for k, v in buckets.items() if v["n"] >= MIN_RANKED_SAMPLE}
        if not eligible:
            return None, None
        best_k  = max(eligible, key=lambda k: eligible[k]["avg"])
        worst_k = min(eligible, key=lambda k: eligible[k]["avg"])
        return (
            {"name": best_k,  **eligible[best_k]},
            {"name": worst_k, **eligible[worst_k]},
        )

    # ── Position breakdown ──────────────────────────────────────────
    position: dict[str, dict] = {
        grp: _bucket_stats(scored[scored["POSITION"].isin(positions)])
        for grp, positions in POSITION_GROUPS.items()
    }
    best_position, worst_position = _best_worst(position)

    # ── Round breakdown (1-7, UDFA) ──────────────────────────────────
    round_: dict[str, dict] = {}
    for r in list(range(1, 8)) + [UDFA_ROUND]:
        r_sc = scored[scored["ROUND"] == r]
        if len(r_sc) == 0 and r != UDFA_ROUND:
            continue  # skip real rounds with zero picks; always compute UDFA
        round_[format_round(r)] = _bucket_stats(r_sc)

    # Best round may legitimately be UDFA -- an undrafted player who
    # becomes a stud is exactly the story this stat should tell. Worst
    # round deliberately excludes UDFA: undrafted players averaging lower
    # than drafted ones is the expected baseline, not a drafting weakness,
    # so it would show up as "Worst Round: UDFA" almost every time
    # regardless of how well an owner actually drafts -- noise, not signal.
    best_round, _ = _best_worst(round_)
    _, worst_round = _best_worst({k: v for k, v in round_.items() if k != "UDFA"})

    # ── Era breakdown ────────────────────────────────────────────────
    era: dict[str, dict] = {
        label: _bucket_stats(scored[(scored["YEAR"] >= start) & (scored["YEAR"] <= end)])
        for label, start, end in DRAFT_ERAS
    }
    best_era, worst_era = _best_worst(era)

    # ── Late-round hit rate: Round 4+ (incl. UDFA) reaching Starter+ ──
    late_scored = scored[scored["ROUND"] >= 4]
    late_hits   = int(late_scored["CAREER_TIER"].isin(_HIT_TIERS).sum())
    late_round_hit_rate = (late_hits / len(late_scored) * 100) if len(late_scored) else 0.0

    # ── First-round vs late-round average, for risk-profile framing ──
    first_scored    = scored[scored["ROUND"] <= 2]
    first_round_avg = float(first_scored["OVERALL SCORE"].mean()) if len(first_scored) else 0.0
    late_round_avg  = float(late_scored["OVERALL SCORE"].mean()) if len(late_scored) else 0.0

    franchise_conversion_rate = (
        float(odf["CAREER_TIER"].isin(FRANCHISE_TIERS).sum()) / total * 100
    ) if total else 0.0
    bust_rate = (
        float((odf["CAREER_TIER"] == "Bust").sum()) / total * 100
    ) if total else 0.0

    return {
        "owner": owner,
        "total": total,
        "position": position,
        "round": round_,
        "era": era,
        "best_position": best_position,
        "worst_position": worst_position,
        "best_round": best_round,
        "worst_round": worst_round,
        "best_era": best_era,
        "worst_era": worst_era,
        "late_round_hit_rate": late_round_hit_rate,
        "first_round_avg": first_round_avg,
        "late_round_avg": late_round_avg,
        "franchise_conversion_rate": franchise_conversion_rate,
        "bust_rate": bust_rate,
    }


# ---------------------------------------------------------------------------
# Dynasty Power Index + "Why Is Ryan Winning?" — owner-level explanation
# ---------------------------------------------------------------------------
#
# Built as ONE feature, per explicit direction: Power Index is never shown
# without its explanation. This does NOT introduce a new source of truth --
# every input below comes from compute_owner_stats() and compute_draft_dna(),
# which are themselves built on canonical OVERALL SCORE / CAREER_TIER
# fields. No individual player is re-scored; this is purely an owner-level
# aggregate of numbers that already exist.

POWER_INDEX_WEIGHTS: dict[str, float] = {
    "avg_score":      0.5,
    "franchise_rate": 0.3,
    "hit_rate":       0.2,
}
"""Weights for compute_power_index(). Sum to exactly 1.0, enforced by the
assert immediately below so this can never silently drift out of balance.
Each weight applies to an input that is already 0-100-scaled (avg_score
per the locked player-scoring formula; franchise_rate and hit_rate are
already percentages), so the weighted sum is itself directly on a 0-100
scale with no separate normalization step. Deliberately excludes bust
rate as a fourth factor -- it's already implicit in avg_score (a bust
drags the average down), so scoring it twice would double-count the
same signal under two different names."""

assert abs(sum(POWER_INDEX_WEIGHTS.values()) - 1.0) < 1e-9, (
    "POWER_INDEX_WEIGHTS must sum to 1.0"
)

_POWER_INDEX_LABELS: dict[str, str] = {
    "avg_score":      "Average Player Quality",
    "franchise_rate": "Franchise-Tier Depth",
    "hit_rate":       "Late-Round Hit Rate",
}


def compute_power_index(df: pd.DataFrame) -> dict:
    """
    Owner-level Dynasty Power Index: a single transparent 0-100 number per
    owner answering "how strong is each dynasty right now", plus a full,
    additive breakdown of exactly what's driving the gap between them.

    Formula (weights in POWER_INDEX_WEIGHTS, sum to 1.0):
        power_index = 0.5 * avg_score
                    + 0.3 * franchise_conversion_rate
                    + 0.2 * late_round_hit_rate
    A direct weighted blend of three already-0-100 numbers -- no hidden
    normalization, no magic number.

    The gap between Ryan's and Matt's index is decomposed into each
    component's exact contribution. Because the index is a linear
    combination, those contributions are GUARANTEED to sum to the total
    gap -- enforced by an assert here rather than just asserted in
    prose, so "Why Is Ryan Winning" is arithmetic that visibly adds up,
    not a vibe.

    Parameters
    ----------
    df: Raw players DataFrame from ``load_players()``.

    Returns
    -------
    dict with keys:
      matt, ryan       -- each {avg_score, franchise_rate, hit_rate,
                           power_index}
      leader, gap       -- who's ahead and by how many Power Index points
                           (gap is always >= 0; see `leader` for direction)
      components        -- list of {label, matt_value, ryan_value, weight,
                           contribution, leader}, one per weighted factor,
                           sorted by |contribution| descending (biggest
                           driver of the gap first)
      sharpest_position  -- supplementary context, NOT part of the
                           weighted math: the single position group with
                           the largest score gap between the owners
                           (both sides must meet MIN_RANKED_SAMPLE), or
                           None if nothing qualifies.
    """
    matt_stats = compute_owner_stats(df, "Matt")
    ryan_stats = compute_owner_stats(df, "Ryan")
    matt_dna   = compute_draft_dna(df, "Matt")
    ryan_dna   = compute_draft_dna(df, "Ryan")

    def _owner_inputs(stats: dict, dna: dict) -> dict:
        avg_score      = stats["avg_score"]
        franchise_rate = dna["franchise_conversion_rate"]
        hit_rate       = dna["late_round_hit_rate"]
        power_index = (
            POWER_INDEX_WEIGHTS["avg_score"] * avg_score
            + POWER_INDEX_WEIGHTS["franchise_rate"] * franchise_rate
            + POWER_INDEX_WEIGHTS["hit_rate"] * hit_rate
        )
        return {
            "avg_score": avg_score, "franchise_rate": franchise_rate,
            "hit_rate": hit_rate, "power_index": power_index,
        }

    matt = _owner_inputs(matt_stats, matt_dna)
    ryan = _owner_inputs(ryan_stats, ryan_dna)

    raw_gap = ryan["power_index"] - matt["power_index"]  # positive = Ryan ahead
    leader  = "Ryan" if raw_gap > 0 else "Matt" if raw_gap < 0 else "Tie"

    components = []
    for key, weight in POWER_INDEX_WEIGHTS.items():
        m_val, r_val = matt[key], ryan[key]
        contribution = weight * (r_val - m_val)  # positive = favors Ryan
        components.append({
            "label": _POWER_INDEX_LABELS[key],
            "matt_value": m_val, "ryan_value": r_val, "weight": weight,
            "contribution": contribution,
            "leader": "Ryan" if contribution > 0 else "Matt" if contribution < 0 else "Tie",
        })
    components.sort(key=lambda c: abs(c["contribution"]), reverse=True)

    # The whole point of this feature: verify the breakdown actually
    # explains the number, don't just assert it in a docstring.
    assert abs(sum(c["contribution"] for c in components) - raw_gap) < 1e-6, (
        "Power Index component contributions do not sum to the total gap"
    )

    # ── Sharpest positional edge (supplementary color, not scored) ────
    sharpest_position = None
    shared_positions = set(matt_dna["position"]) & set(ryan_dna["position"])
    eligible = [
        (pos, ryan_dna["position"][pos]["avg"] - matt_dna["position"][pos]["avg"])
        for pos in shared_positions
        if matt_dna["position"][pos]["n"] >= MIN_RANKED_SAMPLE
        and ryan_dna["position"][pos]["n"] >= MIN_RANKED_SAMPLE
    ]
    if eligible:
        pos, diff = max(eligible, key=lambda x: abs(x[1]))
        sharpest_position = {
            "position": pos, "diff": diff,
            "leader": "Ryan" if diff > 0 else "Matt" if diff < 0 else "Tie",
            "matt_avg": matt_dna["position"][pos]["avg"],
            "ryan_avg": ryan_dna["position"][pos]["avg"],
        }

    return {
        "matt": matt, "ryan": ryan, "leader": leader, "gap": abs(raw_gap),
        "components": components, "sharpest_position": sharpest_position,
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


# ---------------------------------------------------------------------------
# Draft Class Retrospectives — narrative summary per class (V2 feature)
# ---------------------------------------------------------------------------

def class_retrospective(year_df: pd.DataFrame) -> dict:
    """
    Compute the narrative retrospective for one draft class: best pick,
    biggest miss, best late-round steal, and a one-line summary sentence.

    ``year_df`` should already be filtered to a single YEAR (as War Room's
    Class Deep Dive already does). Pure presentation logic — does not
    change or reinterpret OVERALL SCORE or CAREER_TIER in any way.
    """
    scored = year_df.dropna(subset=["OVERALL SCORE"])
    if scored.empty:
        return {
            "best_pick": None, "biggest_miss": None, "steal": None,
            "summary": "This class hasn't been scored yet — check back once it develops.",
        }

    def _row(r) -> dict:
        return {
            "name":   str(r["PLAYER"]),
            "owner":  str(r["OWNER"]),
            "score":  float(r["OVERALL SCORE"]),
            "round":  int(r["ROUND"]) if pd.notna(r["ROUND"]) else None,
            "tier":   str(r["CAREER_TIER"]),
        }

    best_pick_row = scored.loc[scored["OVERALL SCORE"].idxmax()]
    best_pick = _row(best_pick_row)

    # Biggest miss: worst score among Round 1-2 picks only (a "miss" needs
    # draft capital spent on it — a bad Round 7 pick isn't a miss, it's
    # expected variance).
    early = scored[scored["ROUND"] <= 2]
    biggest_miss = _row(early.loc[early["OVERALL SCORE"].idxmin()]) if not early.empty else None

    # Steal: best score among Round 4+ picks (mirrors the Dashboard's
    # "Best Late-Round Picks" definition, scoped to this one class).
    late = scored[scored["ROUND"] >= 4]
    steal = _row(late.loc[late["OVERALL SCORE"].idxmax()]) if not late.empty else None

    m_avg = scored[scored["OWNER"] == "Matt"]["OVERALL SCORE"].mean()
    r_avg = scored[scored["OWNER"] == "Ryan"]["OVERALL SCORE"].mean()
    m_avg = 0.0 if pd.isna(m_avg) else float(m_avg)
    r_avg = 0.0 if pd.isna(r_avg) else float(r_avg)

    if m_avg > r_avg:
        winner_sentence = f"Matt won this class, averaging {m_avg:.1f} to Ryan's {r_avg:.1f}."
    elif r_avg > m_avg:
        winner_sentence = f"Ryan won this class, averaging {r_avg:.1f} to Matt's {m_avg:.1f}."
    else:
        winner_sentence = f"This class was a dead heat — both owners averaged {m_avg:.1f}."

    headline = f"{best_pick['name']} ({best_pick['owner']}) was the class's best player at {best_pick['score']:.1f}."
    if steal and steal["name"] != best_pick["name"]:
        if steal["round"] == UDFA_ROUND:
            headline += f" {steal['owner']}'s undrafted signing of {steal['name']} was the steal of the class."
        else:
            headline += f" {steal['owner']}'s Round {steal['round']} pick of {steal['name']} was the steal of the class."
    if biggest_miss:
        headline += f" {biggest_miss['owner']}'s Round {biggest_miss['round']} selection of {biggest_miss['name']} never lived up to the pick."

    return {
        "best_pick": best_pick,
        "biggest_miss": biggest_miss,
        "steal": steal,
        "summary": f"{winner_sentence} {headline}",
    }


# ---------------------------------------------------------------------------
# Power Rankings History — Matt vs Ryan avg score by year (V2 feature)
# ---------------------------------------------------------------------------

def compute_power_history(class_df: pd.DataFrame) -> list[dict]:
    """
    Year-by-year Matt vs Ryan average score, for the rivalry-over-time
    trend view. Takes the already-computed class_df from
    ``compute_class_stats`` — no re-derivation of scores.

    Returns one dict per year: {year, matt_avg, ryan_avg, leader}.
    Years with no scored picks yet (future/pending classes) are excluded.
    """
    rows = []
    for year in sorted(class_df["YEAR"].unique()):
        year_rows = class_df[class_df["YEAR"] == year]
        m = year_rows[year_rows["OWNER"] == "Matt"]
        r = year_rows[year_rows["OWNER"] == "Ryan"]
        m_scored = int(m["scored"].iloc[0]) if not m.empty else 0
        r_scored = int(r["scored"].iloc[0]) if not r.empty else 0
        if m_scored == 0 and r_scored == 0:
            continue
        m_avg = float(m["avg_score"].iloc[0]) if not m.empty else 0.0
        r_avg = float(r["avg_score"].iloc[0]) if not r.empty else 0.0
        leader = "Matt" if m_avg > r_avg else "Ryan" if r_avg > m_avg else "Tie"
        rows.append({
            "year": int(year), "matt_avg": m_avg, "ryan_avg": r_avg, "leader": leader,
        })
    return rows


# ---------------------------------------------------------------------------
# Dynasty Timeline — curated milestone narrative (Legacy Center, V2 feature)
# ---------------------------------------------------------------------------
#
# Every milestone below has an explicit, disambiguated definition, decided
# up front rather than left as a vague label -- "power swing" in particular
# can mean several different things, so each one below states exactly which
# it means and why. All of it is deterministic and derived from canonical
# workbook fields; nothing here is a new score, a new data source, or an
# AI-generated judgment call.
#
# Two distinct notions of "who's ahead" are used on purpose, and must not
# be confused with each other:
#   - compute_power_history() (above) is PER-CLASS: for one single draft
#     year, who did better in that class alone. Used here only for
#     "Biggest Draft-Class Swing".
#   - compute_cumulative_power() (below) is CUMULATIVE / RUNNING: as of
#     the end of year Y, averaging every scored pick either owner has
#     made from FIRST_YEAR through Y. This is "the dynasty standing at
#     that point in time" and is what every other milestone below means
#     by "power", "lead", "swing", or "comeback".

def compute_cumulative_power(df: pd.DataFrame) -> list[dict]:
    """
    Cumulative Matt-vs-Ryan standing, expanding year over year: "as of the
    end of year Y, what does each owner's body of work look like so far."

    This is distinct from compute_power_history(), which reports each
    class in isolation. This function answers "who was ahead in the
    dynasty as a whole at this point in history" -- the running average
    across every scored pick made up to and including that year.

    Returns one dict per year that has at least one cumulative scored
    pick for either owner: {year, matt_avg, ryan_avg, leader, gap,
    matt_n, ryan_n}. Years before either owner has a single scored pick
    are omitted (there is no "standing" yet to report).
    """
    rows: list[dict] = []
    for year in sorted(df["YEAR"].unique()):
        upto = df[df["YEAR"] <= year]
        m = _owner_aggregate(upto[upto["OWNER"] == "Matt"])
        r = _owner_aggregate(upto[upto["OWNER"] == "Ryan"])
        if m["scored_count"] == 0 and r["scored_count"] == 0:
            continue
        m_avg, r_avg = m["avg_score"], r["avg_score"]
        leader = "Matt" if m_avg > r_avg else "Ryan" if r_avg > m_avg else "Tie"
        rows.append({
            "year": int(year), "matt_avg": m_avg, "ryan_avg": r_avg,
            "leader": leader, "gap": abs(m_avg - r_avg),
            "matt_n": m["scored_count"], "ryan_n": r["scored_count"],
        })
    return rows


def compute_dynasty_timeline(df: pd.DataFrame) -> list[dict]:
    """
    Build the curated Dynasty Timeline: a small, deterministic set of
    milestone events, each with a title, the triggering year, a one-line
    "why it matters", a supporting metric, and an owner for color-coding.

    Milestone definitions (each deliberately disambiguated):
      - Dynasty Begins: FIRST_YEAR, static.
      - First Franchise-Level Player: earliest YEAR among players whose
        CAREER_TIER is Franchise or Legend. Ties broken by highest score.
      - First Legend-Level Player: same, restricted to CAREER_TIER ==
        "Legend" specifically.
      - First Championship-Impact Player: earliest YEAR among players
        with SB Win > 0. Ties broken by highest score.
      - First Major Power Swing: the first year (via
        compute_cumulative_power) where the cumulative leader differs
        from the prior year's leader, AND both owners already have at
        least MIN_RANKED_SAMPLE cumulative scored picks -- the same
        small-sample threshold used everywhere else in this module, so
        an early flip on 1-2 picks each doesn't get reported as
        "major". This is a YEAR-OVER-YEAR LEADER CHANGE, not a class
        win/loss and not a magnitude threshold.
      - Biggest Draft-Class Swing: the single YEAR (via
        compute_power_history, PER-CLASS) with the largest score gap
        between Matt's and Ryan's picks in that one class alone --
        deliberately NOT the cumulative dynasty-wide gap.
      - Largest Owner Lead: the YEAR (via compute_cumulative_power) with
        the largest CUMULATIVE gap in dynasty history to date, among
        years where both owners have at least MIN_RANKED_SAMPLE
        cumulative scored picks -- same reasoning as the power-swing
        gate above.
      - Biggest Comeback: compares the cumulative gap at its historical
        peak to the cumulative gap in the most recent scored year --
        the amount the trailing owner (from that peak) has since closed,
        floored at 0 if the gap has only grown. Only reported if it's
        > 0 and the peak year isn't the most recent year (there must be
        something to have "come back" from).
      - Current Dynasty State: the most recent entry from
        compute_cumulative_power -- today's actual standing.

    Returns a chronologically-sorted list of milestone dicts:
      {year, title, event, why, metric, owner}
    ``owner`` is "Matt", "Ryan", or "Dynasty" (for owner-neutral facts),
    used purely for color-coding in the UI.
    """
    milestones: list[dict] = []
    scored = df.dropna(subset=["OVERALL SCORE"])
    cum    = compute_cumulative_power(df)
    per_class = compute_power_history(compute_class_stats(df))

    # ── Dynasty Begins ────────────────────────────────────────────────
    milestones.append({
        "year": FIRST_YEAR, "title": "The Beginning",
        "event": "Trail & Bish Dynasty begins.",
        "why": "Every player, every class, every rivalry number that follows starts here.",
        "metric": f"{int((df['YEAR'] == FIRST_YEAR).sum())} players drafted in the inaugural class",
        "owner": "Dynasty",
    })

    # ── First Franchise-Level Player ────────────────────────────────
    fr = scored[scored["CAREER_TIER"].isin(FRANCHISE_TIERS)].sort_values(
        ["YEAR", "OVERALL SCORE"], ascending=[True, False]
    )
    if not fr.empty:
        top = fr.iloc[0]
        milestones.append({
            "year": int(top["YEAR"]), "title": "First Franchise-Level Player",
            "event": f"{top['PLAYER']} ({top['OWNER']}) becomes the dynasty's first Franchise-tier player.",
            "why": "The first sign either owner could hit at an elite level, not just find a starter.",
            "metric": f"Score {fmt_score(top['OVERALL SCORE'])} · {top['CAREER_TIER']}",
            "owner": str(top["OWNER"]),
        })

    # ── First Legend-Level Player ────────────────────────────────────
    lg = scored[scored["CAREER_TIER"] == "Legend"].sort_values(
        ["YEAR", "OVERALL SCORE"], ascending=[True, False]
    )
    if not lg.empty:
        top = lg.iloc[0]
        milestones.append({
            "year": int(top["YEAR"]), "title": "First Legend-Level Player",
            "event": f"{top['PLAYER']} ({top['OWNER']}) becomes the dynasty's first Legend.",
            "why": "The ceiling of the entire scoring system, reached for the first time.",
            "metric": f"Score {fmt_score(top['OVERALL SCORE'])}",
            "owner": str(top["OWNER"]),
        })

    # ── First Championship-Impact Player ─────────────────────────────
    if "SB Win" in df.columns:
        sb = scored[scored["SB Win"].fillna(0) > 0].sort_values(
            ["YEAR", "OVERALL SCORE"], ascending=[True, False]
        )
        if not sb.empty:
            top = sb.iloc[0]
            rings = int(top["SB Win"])
            milestones.append({
                "year": int(top["YEAR"]), "title": "First Championship-Impact Player",
                "event": f"{top['PLAYER']} ({top['OWNER']}) becomes the dynasty's first Super Bowl champion.",
                "why": "The moment the dynasty stopped being just about scores and started touching real championships.",
                "metric": f"{rings} ring{'s' if rings != 1 else ''}",
                "owner": str(top["OWNER"]),
            })

    # ── First Major Power Swing (cumulative leader flips, non-trivial sample) ──
    prev_leader = None
    for row in cum:
        if prev_leader is not None and row["leader"] != prev_leader and row["leader"] != "Tie":
            if row["matt_n"] >= MIN_RANKED_SAMPLE and row["ryan_n"] >= MIN_RANKED_SAMPLE:
                milestones.append({
                    "year": row["year"], "title": "First Major Power Shift",
                    "event": f"{row['leader']} takes the all-time dynasty lead for the first time.",
                    "why": "The balance of power changes hands for the first time with a real sample behind it.",
                    "metric": f"+{row['gap']:.1f} avg score edge as of {row['year']}",
                    "owner": row["leader"],
                })
                break
        if row["matt_n"] >= MIN_RANKED_SAMPLE and row["ryan_n"] >= MIN_RANKED_SAMPLE:
            prev_leader = row["leader"]

    # ── Biggest Draft-Class Swing (single class, not cumulative) ────
    if per_class:
        biggest_class = max(per_class, key=lambda r: abs(r["matt_avg"] - r["ryan_avg"]))
        gap = abs(biggest_class["matt_avg"] - biggest_class["ryan_avg"])
        if gap > 0:
            milestones.append({
                "year": biggest_class["year"], "title": "Biggest Draft-Class Swing",
                "event": f"{biggest_class['leader']} dominates the {biggest_class['year']} class outright.",
                "why": "The single most lopsided class in dynasty history, judged on that class alone.",
                "metric": f"+{gap:.1f} avg score gap in one class",
                "owner": biggest_class["leader"],
            })

    # ── Largest Owner Lead (cumulative, sample-gated) ────────────────
    # Same MIN_RANKED_SAMPLE gate as the power-swing check above -- an
    # early year with 1-2 picks each can produce a huge but meaningless
    # gap. Only years where both owners have a real sample are eligible.
    eligible_cum = [
        r for r in cum if r["matt_n"] >= MIN_RANKED_SAMPLE and r["ryan_n"] >= MIN_RANKED_SAMPLE
    ]
    if eligible_cum:
        peak = max(eligible_cum, key=lambda r: r["gap"])
        if peak["gap"] > 0:
            milestones.append({
                "year": peak["year"], "title": "Largest Owner Lead",
                "event": f"{peak['leader']} opens the widest cumulative lead in dynasty history.",
                "why": "The single furthest apart the two owners have ever been, dynasty-wide.",
                "metric": f"+{peak['gap']:.1f} avg score, {peak['leader']} {peak['matt_avg' if peak['leader']=='Matt' else 'ryan_avg']:.1f}",
                "owner": peak["leader"],
            })

        # ── Biggest Comeback (peak gap vs. most recent gap) ──────────
        latest = cum[-1]
        if peak["year"] != latest["year"]:
            closed = peak["gap"] - latest["gap"]
            if closed > 0:
                trailing_owner = "Ryan" if peak["leader"] == "Matt" else "Matt"
                milestones.append({
                    "year": latest["year"], "title": "Biggest Comeback",
                    "event": f"{trailing_owner} claws back {closed:.1f} points of the {peak['year']} deficit.",
                    "why": (
                        f"{trailing_owner} has taken the lead back"
                        if latest["leader"] == trailing_owner
                        else f"{trailing_owner} has cut into what was once a +{peak['gap']:.1f} deficit"
                    ),
                    "metric": f"Gap: +{peak['gap']:.1f} ({peak['year']}) → +{latest['gap']:.1f} (now)",
                    "owner": trailing_owner,
                })

        # ── Current Dynasty State ─────────────────────────────────────
        # Deliberately NOT sample-gated -- this reports reality as it
        # stands today, not "the most extreme historical moment", so
        # there's no small-sample risk to guard against here.
        milestones.append({
            "year": latest["year"], "title": "Current Dynasty State",
            "event": f"{latest['leader']} leads the all-time dynasty average, as of the {latest['year']} class.",
            "why": "Where things actually stand today.",
            "metric": f"Matt {latest['matt_avg']:.1f} · Ryan {latest['ryan_avg']:.1f}",
            "owner": latest["leader"],
        })

    milestones.sort(key=lambda m: m["year"])
    return milestones


# ---------------------------------------------------------------------------
# Dynasty Awards — single-champion badges, dynasty-wide (V2 feature)
# ---------------------------------------------------------------------------

def compute_dynasty_awards(df: pd.DataFrame) -> dict:
    """
    Four dynasty-wide single-champion awards, computed straight from
    existing columns. Presentation-only — none of these feed back into
    OVERALL SCORE or CAREER_TIER.
    """
    scored = df.dropna(subset=["OVERALL SCORE"])
    award_cols = ["MVP", "OPOY", "DPOY", "OROY", "DROY", "ALL_PRO", "SB Win", "SB_MVP"]
    present_cols = [c for c in award_cols if c in scored.columns]

    def _pick(sub_df: pd.DataFrame, by: str, ascending: bool) -> dict | None:
        if sub_df.empty:
            return None
        row = sub_df.sort_values(by, ascending=ascending).iloc[0]
        return {
            "name":  str(row["PLAYER"]),
            "owner": str(row["OWNER"]),
            "value": row[by],
            "round": int(row["ROUND"]) if pd.notna(row["ROUND"]) else None,
        }

    # Biggest Steal: best score among Round 4+ picks, dynasty-wide.
    late = scored[scored["ROUND"] >= 4]
    steal = _pick(late, "OVERALL SCORE", ascending=False)

    # Biggest Bust: worst score among Round 1-2 picks, dynasty-wide.
    early = scored[scored["ROUND"] <= 2]
    bust = None
    if not early.empty:
        row = early.sort_values("OVERALL SCORE", ascending=True).iloc[0]
        bust = {
            "name": str(row["PLAYER"]), "owner": str(row["OWNER"]),
            "value": float(row["OVERALL SCORE"]), "round": int(row["ROUND"]) if pd.notna(row["ROUND"]) else None,
        }

    # Most Decorated: highest total award count.
    decorated = None
    if present_cols:
        tmp = scored.copy()
        tmp["_award_total"] = tmp[present_cols].fillna(0).sum(axis=1)
        if tmp["_award_total"].max() > 0:
            row = tmp.sort_values("_award_total", ascending=False).iloc[0]
            decorated = {
                "name": str(row["PLAYER"]), "owner": str(row["OWNER"]),
                "value": int(row["_award_total"]), "round": None,
            }

    # Most Durable: LONGEVITY is a categorical field (Elite/High/Moderate/Low/
    # Minimal), not a number of years — sorting it alphabetically is meaningless
    # (tested against live data and caught this before shipping). Instead: among
    # players in the top "Elite" longevity tier, take the highest OVERALL SCORE.
    durable = None
    if "LONGEVITY" in scored.columns:
        elite_longevity = scored[scored["LONGEVITY"] == "Elite"]
        if not elite_longevity.empty:
            row = elite_longevity.sort_values("OVERALL SCORE", ascending=False).iloc[0]
            durable = {
                "name": str(row["PLAYER"]), "owner": str(row["OWNER"]),
                "value": "Elite", "round": None,
            }

    return {"steal": steal, "bust": bust, "decorated": decorated, "durable": durable}


# ---------------------------------------------------------------------------
# Smack Talk Engine — fact pack (V2 feature)
# ---------------------------------------------------------------------------

def compute_smack_talk_facts(df: pd.DataFrame, class_df: pd.DataFrame) -> dict:
    """
    Gather the real numbers the Smack Talk Engine needs, per owner.
    Pure fact-gathering — no sentence generation, no randomness, so it
    stays consistent with this file's "pure functions" rule. The page
    layer turns these facts into actual trash talk text.
    """
    facts: dict = {}
    record = compute_series_record(class_df)
    rushmore = compute_mount_rushmore(df)
    _award_cols = ["MVP", "OPOY", "DPOY", "OROY", "DROY", "ALL_PRO", "SB Win", "SB_MVP"]

    for owner in ["Matt", "Ryan"]:
        odf = df[df["OWNER"] == owner]
        scored = odf.dropna(subset=["OVERALL SCORE"])
        best = rushmore[owner][0] if rushmore[owner] else None
        worst = (
            scored.sort_values("OVERALL SCORE", ascending=True).iloc[0].to_dict()
            if len(scored) else None
        )
        present_cols = [c for c in _award_cols if c in odf.columns]
        award_total = int(odf[present_cols].fillna(0).sum().sum()) if present_cols else 0

        facts[owner] = {
            "avg_score":  float(scored["OVERALL SCORE"].mean()) if len(scored) else 0.0,
            "franchise":  int(odf["CAREER_TIER"].isin(FRANCHISE_TIERS).sum()),
            "busts":      int((odf["CAREER_TIER"] == "Bust").sum()),
            "best_name":  best["PLAYER"] if best else "nobody worth mentioning",
            "best_score": float(best["OVERALL SCORE"]) if best else 0.0,
            "worst_name": worst["PLAYER"] if worst else "nobody worth mentioning",
            "worst_score": float(worst["OVERALL SCORE"]) if worst else 0.0,
            "worst_round": int(worst["ROUND"]) if worst and pd.notna(worst["ROUND"]) else None,
            "award_total": award_total,
        }

    facts["class_wins"] = {"Matt": record["matt_wins"], "Ryan": record["ryan_wins"], "ties": record["ties"]}
    return facts


# ---------------------------------------------------------------------------
# Baseline methodology audit — how OVERALL SCORE's baseline was actually
# derived (documentation, not a scoring change). See docs/DECISIONS.md D030
# for why the formula itself is locked and never touched by this analysis.
# ---------------------------------------------------------------------------

_AWARD_WEIGHTS: dict[str, float] = {
    "MVP": 6, "SB_MVP": 4, "OPOY": 3, "DPOY": 3,
    "ALL_PRO": 2.5, "SB Win": 2.5, "OROY": 1, "DROY": 1,
}
_TIER_ORDINAL: dict[str, int] = {"Elite": 4, "High": 3, "Moderate": 2, "Low": 1, "Minimal": 0}


def _implied_baseline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reverse the locked D030 formula to recover each scored player's baseline:
    baseline = OVERALL SCORE - 0.6 * min(award_points, 16).
    Read-only derivation for documentation purposes — never written back to
    the workbook, never used to recompute OVERALL SCORE or CAREER_TIER.
    """
    scored = df.dropna(subset=["OVERALL SCORE"]).copy()
    for c in _AWARD_WEIGHTS:
        if c in scored.columns:
            scored[c] = scored[c].fillna(0).astype(float)
        else:
            scored[c] = 0.0
    scored["award_pts_raw"] = sum(scored[c] * w for c, w in _AWARD_WEIGHTS.items())
    scored["award_pts_capped"] = scored["award_pts_raw"].clip(upper=16)
    scored["implied_baseline"] = scored["OVERALL SCORE"] - 0.6 * scored["award_pts_capped"]
    return scored


def _r2_linreg(X_cols: list, y: "pd.Series") -> tuple[float, list[float]]:
    """Plain numpy least-squares linear regression — avoids adding sklearn
    as a dependency for one R² computation on a free-tier Streamlit app."""
    import numpy as np
    X = np.column_stack([X_cols[i] for i in range(len(X_cols))] + [np.ones(len(y))])
    coef, *_ = np.linalg.lstsq(X, y.values, rcond=None)
    pred = X @ coef
    ss_res = float(((y.values - pred) ** 2).sum())
    ss_tot = float(((y.values - y.values.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return r2, list(coef), pred


def compute_baseline_audit(df: pd.DataFrame) -> dict:
    """
    Live audit of how the baseline component of OVERALL SCORE relates to
    the PRODUCTION / LONGEVITY / CHAMPIONSHIP_IMPACT tier fields.

    Documentation only — recomputes nothing that feeds back into the app's
    actual scores. Every number here is derived fresh from the current
    workbook each time this runs, so it can't go stale relative to the data.
    """
    scored = _implied_baseline(df)
    scored["prod_ord"] = scored["PRODUCTION"].map(_TIER_ORDINAL)
    scored["long_ord"] = scored["LONGEVITY"].map(_TIER_ORDINAL)

    # Step sizes: mean implied baseline per PRODUCTION tier, in tier order
    tier_order = ["Elite", "High", "Moderate", "Low", "Minimal"]
    prod_means = scored.groupby("PRODUCTION")["implied_baseline"].mean()
    steps = []
    for i in range(len(tier_order) - 1):
        hi, lo = tier_order[i], tier_order[i + 1]
        if hi in prod_means.index and lo in prod_means.index:
            steps.append({
                "from": hi, "to": lo,
                "gap": round(float(prod_means[hi] - prod_means[lo]), 1),
            })

    sub = scored.dropna(subset=["prod_ord", "long_ord", "implied_baseline"])
    r2_prod, _, _ = _r2_linreg([sub["prod_ord"].values], sub["implied_baseline"])
    r2_both, coef_both, pred_both = _r2_linreg(
        [sub["prod_ord"].values, sub["long_ord"].values], sub["implied_baseline"]
    )

    sub = sub.copy()
    sub["predicted"] = pred_both
    sub["residual"] = sub["implied_baseline"] - sub["predicted"]

    def _outlier_rows(rows) -> list[dict]:
        return [
            {
                "name": str(r["PLAYER"]), "owner": str(r["OWNER"]),
                "production": str(r["PRODUCTION"]), "longevity": str(r["LONGEVITY"]),
                "baseline": round(float(r["implied_baseline"]), 1),
                "predicted": round(float(r["predicted"]), 1),
                "residual": round(float(r["residual"]), 1),
            }
            for _, r in rows.iterrows()
        ]

    return {
        "n_scored": int(len(scored)),
        "n_with_awards": int((scored["award_pts_raw"] > 0).sum()),
        "n_champ_impact_tagged": int(scored["CHAMPIONSHIP_IMPACT"].notna().sum()),
        "production_r2": round(r2_prod, 4),
        "production_longevity_r2": round(r2_both, 4),
        "avg_step": round(sum(s["gap"] for s in steps) / len(steps), 1) if steps else 0.0,
        "steps": steps,
        "residual_std": round(float(sub["residual"].std()), 2),
        "penalized_below_tier": _outlier_rows(sub.nsmallest(6, "residual")),
        "credited_above_tier": _outlier_rows(sub.nlargest(6, "residual")),
    }
