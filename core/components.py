"""
core/components.py

Reusable HTML component library for Trail & Bish Dynasty.

Every public function returns an HTML string.  Render with:

    st.markdown(component_fn(...), unsafe_allow_html=True)

Design rules
------------
• No default Streamlit widgets — always custom HTML.
• No inline ``style=`` except for dynamic values (e.g. bar widths from data).
• All static CSS lives in ``assets/theme.css``.
• Owner colors are immutable: Matt = #2E7DF7 (blue), Ryan = #E63B3B (red).
• Add a new component here before adding page-specific HTML to a page file.
• If two pages share a visual pattern it belongs here, not in either page.
"""

from __future__ import annotations

import html as _html
import math as _math

from core.utils import is_score_pending, safe_int, fmt_score


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe_score(score) -> int:
    """Return an int in [0, 100] for bar-width calculations.  Pending / invalid scores become 0."""
    if is_score_pending(score):
        return 0
    return max(0, min(100, safe_int(score)))


def _fmt_score(score) -> str:
    """Thin wrapper around ``fmt_score`` for internal component use.
    Delegates to ``core.utils.fmt_score`` with '0' as the pending fallback."""
    return fmt_score(score, pending_str="0")


def _compact(s: str) -> str:
    """Strip leading whitespace from every line — prevents CommonMark 4-space code-block rule."""
    return "\n".join(line.lstrip() for line in s.strip().splitlines())


# Award column → (display label, CSS class)
_AWARD_MAP: list[tuple[str, str, str]] = [
    ("MVP",     "MVP",    "tb-award-mvp"),
    ("OPOY",    "OPOY",   "tb-award-honor"),
    ("DPOY",    "DPOY",   "tb-award-honor"),
    ("OROY",    "ROY",    "tb-award-roy"),
    ("DROY",    "ROY",    "tb-award-roy"),
    ("ALL_PRO", "AP",     "tb-award-allpro"),
    ("SB Win",  "SB",     "tb-award-sb"),
    ("SB_MVP",  "SB MVP", "tb-award-mvp"),
]


def _award_count(val) -> int:
    """Return a positive int count for a valid award value, else 0."""
    try:
        f = float(val)
        return int(f) if _math.isfinite(f) and f > 0 else 0
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Atoms — smallest building blocks
# ---------------------------------------------------------------------------

def owner_chip(owner: str) -> str:
    """Inline Matt / Ryan colored ownership pill."""
    cls = "tb-chip-matt" if owner == "Matt" else "tb-chip-ryan"
    return f'<span class="tb-chip {cls}">{owner}</span>'


def tier_badge(tier: str) -> str:
    """Career tier classification badge (Legend → Bust).

    Six tiers derived from OVERALL SCORE — see score_to_tier() in stats.py.
    """
    _cls = {
        "Legend":           "tb-tier-legend",
        "Franchise":        "tb-tier-franchise",
        "High-End Starter": "tb-tier-elite",
        "Starter":          "tb-tier-starter",
        "Contributor":      "tb-tier-contrib",
        "Bust":             "tb-tier-bust",
    }
    return f'<span class="tb-tier-badge {_cls.get(tier, "tb-tier-contrib")}">{tier}</span>'


def hof_badge() -> str:
    """Hall of Fame inductee badge.

    Displayed alongside the tier badge when a player's HOF column is True.
    HOF is a hand-set flag in the workbook — independent of score/tier.
    """
    return '<span class="tb-hof-badge">HOF</span>'


def position_chip(position: str) -> str:
    """Dark position label chip."""
    return f'<span class="tb-pos-chip">{position}</span>'


def score_pending_badge() -> str:
    """
    Placeholder for draft picks with no career score yet (2025–26 classes).

    A score of 0 is a real score (Bust tier); this badge is for genuinely
    absent data, not for poor performers.
    """
    return '<span class="tb-score-pending">TBD</span>'


def award_badges(row: dict) -> str:
    """
    Render a compact row of award badge spans for a player.

    Parameters
    ----------
    row:
        A dict from ``pandas.Series.to_dict()``.  Keys must include the
        award column names from the ``players`` sheet.
    """
    badges = []
    for col, label, cls in _AWARD_MAP:
        count = _award_count(row.get(col))
        if count:
            suffix = f"<sup>×{count}</sup>" if count > 1 else ""
            badges.append(
                f'<span class="tb-award-badge {cls}">{label}{suffix}</span>'
            )
    if not badges:
        return '<span class="tb-no-awards">—</span>'
    return '<span class="tb-awards-wrap">' + "".join(badges) + "</span>"


# ---------------------------------------------------------------------------
# Page-level structural components
# ---------------------------------------------------------------------------

def page_header(title: str, subtitle: str | None = None) -> str:
    """ESPN-style hero title block at the top of each page."""
    sub = f'<div class="tb-subtitle">{subtitle}</div>' if subtitle else ""
    return _compact(f"""
    <div class="tb-header">
        <div class="tb-header-left">
            <div class="tb-title">{title}</div>
            {sub}
        </div>
    </div>
    """)


def section_header(title: str, subtitle: str | None = None) -> str:
    """Accent-line section divider with optional descriptor."""
    sub = f'<span class="tb-section-sub">{subtitle}</span>' if subtitle else ""
    return _compact(f"""
    <div class="tb-section-header">
        <span class="tb-section-title">{title}</span>
        {sub}
    </div>
    """)


# ---------------------------------------------------------------------------
# Stat cards
# ---------------------------------------------------------------------------

def stat_card(
    label: str,
    value: str,
    subtitle: str | None = None,
    color: str = "blue",
) -> str:
    """Glow metric card.  ``color`` ∈ {blue, red, green, gold}."""
    sub = f'<div class="tb-card-subtitle">{subtitle}</div>' if subtitle else ""
    return _compact(f"""
    <div class="tb-card tb-{color}">
        <div class="tb-card-title">{label}</div>
        <div class="tb-card-value">{value}</div>
        {sub}
    </div>
    """)


def mini_stat(label: str, value: str) -> str:
    """Compact stat cell — used inside the rivalry banner."""
    return _compact(f"""
    <div class="tb-mini-stat">
        <div class="tb-mini-stat-value">{value}</div>
        <div class="tb-mini-stat-label">{label}</div>
    </div>
    """)


# ---------------------------------------------------------------------------
# Rivalry banner
# ---------------------------------------------------------------------------

def rivalry_banner(matt_df, ryan_df) -> str:
    """Full-width Matt vs Ryan head-to-head comparison panel."""

    def _side(df, name: str, side_cls: str) -> str:
        owner_cls = side_cls.replace("tb-rb-", "tb-")
        return f"""
        <div class="tb-rb-side {side_cls}">
            <div class="tb-rb-owner-name {owner_cls}">{name.upper()}</div>
            <div class="tb-rb-stats">
                {mini_stat("Players",   str(len(df)))}
                {mini_stat("Avg Score", f"{df['OVERALL SCORE'].mean():.1f}")}
                {mini_stat("Franchise", str(int((df['CAREER_TIER'] == 'Franchise').sum())))}
                {mini_stat("Busts",     str(int((df['CAREER_TIER'] == 'Bust').sum())))}
            </div>
        </div>
        """

    matt_avg   = float(matt_df["OVERALL SCORE"].mean())
    ryan_avg   = float(ryan_df["OVERALL SCORE"].mean())
    leader     = "Matt" if matt_avg >= ryan_avg else "Ryan"
    leader_cls = "tb-matt" if leader == "Matt" else "tb-ryan"

    return _compact(f"""
    <div class="tb-rivalry-banner">
        {_side(matt_df, "Matt", "tb-rb-matt")}
        <div class="tb-rb-center">
            <div class="tb-rb-vs">VS</div>
            <div class="tb-rb-leader {leader_cls}">{leader} leads</div>
        </div>
        {_side(ryan_df, "Ryan", "tb-rb-ryan")}
    </div>
    """)


# ---------------------------------------------------------------------------
# Compact player list  (GOAT Race / Dashboard ranked lists)
# ---------------------------------------------------------------------------

def player_row(
    rank: int,
    name: str,
    owner: str,
    position: str,
    year: int,
    score: float,
    tier: str,
    featured: bool = False,
) -> str:
    """Compact ranked player row with inline score bar.  Used for GOAT Race etc."""
    pending  = is_score_pending(score)
    s        = _safe_score(score)
    bar_cls  = "tb-bar-matt" if owner == "Matt" else "tb-bar-ryan"
    feat_cls = " rk-lead-featured" if featured else ""

    bar_html      = "" if pending else f"""
        <div class="tb-pr-score-wrap">
            <div class="tb-pr-bar-track">
                <div class="tb-pr-bar {bar_cls}" style="width:{s}%"></div>
            </div>
        </div>"""
    score_display = score_pending_badge() if pending else _fmt_score(score)

    return _compact(f"""
    <div class="tb-player-row{feat_cls}">
        <div class="tb-pr-rank">#{rank}</div>
        <div class="tb-pr-info">
            <div class="tb-pr-name">{_html.escape(str(name))}</div>
            <div class="tb-pr-meta">
                {owner_chip(owner)}&nbsp;
                {position_chip(position)}&nbsp;
                <span class="tb-pr-year">{year}</span>
            </div>
        </div>
        {bar_html}
        <div class="tb-pr-score-num">{score_display}</div>
        <div class="tb-pr-tier">{tier_badge(tier)}</div>
    </div>
    """)


def player_table(rows_html: str) -> str:
    """Wrapper container for a list of ``player_row()`` items."""
    return f'<div class="tb-player-table">{rows_html}</div>'


# ---------------------------------------------------------------------------
# Callout / highlight card
# ---------------------------------------------------------------------------

def callout(label: str, value: str, detail: str, color: str = "blue") -> str:
    """Highlight card with a colored left accent border.  ``color`` ∈ {blue, red, green, gold}."""
    return _compact(f"""
    <div class="tb-callout tb-{color}">
        <div class="tb-callout-label">{label}</div>
        <div class="tb-callout-value">{value}</div>
        <div class="tb-callout-detail">{detail}</div>
    </div>
    """)


# ---------------------------------------------------------------------------
# Elite player cards — Players page signature feature
# ---------------------------------------------------------------------------

def elite_player_card(
    rank: int,
    name: str,
    owner: str,
    position: str,
    year: int,
    round_: int,
    score: float,
    tier: str,
    awards_html: str,
) -> str:
    """Premium card for top-10 players.  ESPN / Ultimate Team aesthetic."""
    owner_cls  = "tb-elite-matt" if owner == "Matt" else "tb-elite-ryan"
    rd         = f"Rd {round_}" if round_ else ""
    pending    = is_score_pending(score)
    score_disp = score_pending_badge() if pending else _fmt_score(score)

    return _compact(f"""
    <div class="tb-elite-card {owner_cls}">
        <div class="tb-elite-rank">#{rank}</div>
        <div class="tb-elite-score">{score_disp}</div>
        <div class="tb-elite-name">{_html.escape(str(name))}</div>
        <div class="tb-elite-meta">
            {position_chip(position)}
            {owner_chip(owner)}
        </div>
        <div class="tb-elite-draft">{year} · {rd}</div>
        <div class="tb-elite-tier-wrap">{tier_badge(tier)}</div>
        <div class="tb-elite-awards">{awards_html}</div>
    </div>
    """)


# ---------------------------------------------------------------------------
# Player detail card — Players page spotlight
# ---------------------------------------------------------------------------

def player_detail_card(
    name: str,
    owner: str,
    position: str,
    year: int,
    round_: int,
    score: float,
    tier: str,
    awards_html: str,
    notes: str = "",
    production: str = "",
    longevity: str = "",
    champ_impact: str = "",
) -> str:
    """Full-width player profile card shown in the Player Spotlight section."""
    owner_cls  = "tb-detail-matt" if owner == "Matt" else "tb-detail-ryan"
    safe_name  = _html.escape(str(name))
    safe_notes = _html.escape(str(notes)) if notes and str(notes) != "nan" else ""
    rd_str     = f"Round {round_}" if round_ else "—"
    pending    = is_score_pending(score)
    score_disp = score_pending_badge() if pending else _fmt_score(score)
    score_cls  = "" if pending else ("tb-matt" if owner == "Matt" else "tb-ryan")

    stat_rows = [("Draft Class", str(year)), ("Draft Round", rd_str), ("Overall Score", score_disp)]
    for val, lbl in [(production, "Production"), (longevity, "Longevity"), (champ_impact, "Champ Impact")]:
        if val and str(val) not in ("nan", ""):
            stat_rows.append((_html.escape(str(val)), lbl))

    stats_html = "".join(
        f'<div class="tb-detail-stat">'
        f'<div class="tb-detail-stat-val">{v}</div>'
        f'<div class="tb-detail-stat-label">{l}</div>'
        f'</div>'
        for v, l in stat_rows
    )

    notes_block = f'<div class="tb-detail-notes">{safe_notes}</div>' if safe_notes else ""

    return _compact(f"""
    <div class="tb-player-detail {owner_cls}">
        <div class="tb-detail-header">
            <div class="tb-detail-left">
                <div class="tb-detail-name">{safe_name}</div>
                <div class="tb-detail-meta">
                    {owner_chip(owner)}&nbsp;
                    {position_chip(position)}&nbsp;
                    {tier_badge(tier)}
                </div>
                <div class="tb-detail-awards-row">{awards_html}</div>
            </div>
            <div class="tb-detail-score {score_cls}">{score_disp}</div>
        </div>
        <div class="tb-detail-stats">{stats_html}</div>
        {notes_block}
    </div>
    """)


# ---------------------------------------------------------------------------
# Full roster table — Players page
# ---------------------------------------------------------------------------

def roster_table_header() -> str:
    """Fixed column header row for the full roster table."""
    return _compact("""
    <div class="tb-roster-header">
        <div class="tb-rc-rank">#</div>
        <div class="tb-rc-name">PLAYER</div>
        <div class="tb-rc-owner">OWNER</div>
        <div class="tb-rc-pos">POS</div>
        <div class="tb-rc-year">YEAR</div>
        <div class="tb-rc-round">RD</div>
        <div class="tb-rc-score">SCORE</div>
        <div class="tb-rc-tier">TIER</div>
        <div class="tb-rc-awards">AWARDS</div>
    </div>
    """)


def class_dive_row(
    rank: int,
    name: str,
    owner: str,
    position: str,
    round_: int,
    score: float,
    tier: str,
    awards_html: str,
) -> str:
    """
    Compact player row for the War Room Class Deep Dive table.

    Omits the draft year column (redundant when viewing one class) and uses
    a narrower layout than the full ``player_roster_row``.

    Reuses ``.tb-class-dive-row`` grid defined in theme.css.
    """
    safe   = _html.escape(str(name))
    rd_str = f"Rd {round_}" if round_ else "—"

    if is_score_pending(score):
        score_disp = score_pending_badge()
        score_cls  = ""
    else:
        score_disp = _fmt_score(score)
        score_cls  = "tb-matt" if owner == "Matt" else "tb-ryan"

    return _compact(f"""
    <div class="tb-class-dive-row">
        <div class="tb-cd-rank">{rank}</div>
        <div class="tb-cd-name">{safe}</div>
        <div>{owner_chip(owner)}</div>
        <div>{position_chip(position)}</div>
        <div style="color:#5A7494;font-size:12px;font-weight:600;">{rd_str}</div>
        <div class="tb-cd-score {score_cls}">{score_disp}</div>
        <div>{tier_badge(tier)}</div>
        <div>{awards_html}</div>
    </div>
    """)


def player_roster_row(
    rank: int,
    name: str,
    owner: str,
    position: str,
    year: int,
    round_: int,
    score: float,
    tier: str,
    awards_html: str,
) -> str:
    """
    Full-width roster table row.

    Distinct from ``player_row()`` (compact ranked list).
    This variant adds round, award badges, and a score bar with a pending state.
    """
    safe   = _html.escape(str(name))
    rd_str = f"Rd {round_}" if round_ else "—"

    if is_score_pending(score):
        score_inner = score_pending_badge()
    else:
        s       = _safe_score(score)
        bar_cls = "tb-bar-matt" if owner == "Matt" else "tb-bar-ryan"
        score_inner = (
            f'<span class="tb-rc-score-num">{_fmt_score(score)}</span>'
            f'<div class="tb-pr-bar-track tb-rc-bar">'
            f'<div class="tb-pr-bar {bar_cls}" style="width:{s}%"></div>'
            f'</div>'
        )

    return _compact(f"""
    <div class="tb-roster-row">
        <div class="tb-rc-rank">{rank}</div>
        <div class="tb-rc-name"><span class="tb-rc-player-name">{safe}</span></div>
        <div class="tb-rc-owner">{owner_chip(owner)}</div>
        <div class="tb-rc-pos">{position_chip(position)}</div>
        <div class="tb-rc-year">{year}</div>
        <div class="tb-rc-round">{rd_str}</div>
        <div class="tb-rc-score"><div class="tb-rc-score-inner">{score_inner}</div></div>
        <div class="tb-rc-tier">{tier_badge(tier)}</div>
        <div class="tb-rc-awards">{awards_html}</div>
    </div>
    """)


# ---------------------------------------------------------------------------
# Rivalry atoms — reusable across War Room · Man Status · Analytics
# ---------------------------------------------------------------------------

def winner_badge(winner: str, label: str = "") -> str:
    """
    Compact badge indicating who won a class, season, or matchup.

    Parameters
    ----------
    winner: ``"Matt"`` | ``"Ryan"`` | ``"Tie"``
    label:  Override the display text.  Defaults to ``"Matt Wins"``, etc.
    """
    if winner == "Matt":
        cls  = "tb-winner-matt"
        text = label or "Matt Wins"
    elif winner == "Ryan":
        cls  = "tb-winner-ryan"
        text = label or "Ryan Wins"
    else:
        cls  = "tb-winner-tie"
        text = label or "Tied"
    return f'<span class="tb-winner-badge {cls}">{text}</span>'


def grade_badge(grade: str) -> str:
    """
    Letter grade badge (S / A / B / C / D / —) for a draft class or pick.

    Grade thresholds are defined in ``core.stats.class_grade()`` — this
    function only renders; it does not compute grades.
    """
    _cls = {
        "S": "tb-grade-S",
        "A": "tb-grade-A",
        "B": "tb-grade-B",
        "C": "tb-grade-C",
        "D": "tb-grade-D",
    }
    return f'<span class="tb-grade-badge {_cls.get(grade, "tb-grade--")}">{grade}</span>'


def rivalry_stat_row(
    label: str,
    matt_val: str,
    ryan_val: str,
    winner: str = "",
) -> str:
    """
    One labeled Matt-vs-Ryan comparison row for a ``comparison_panel``.

    Parameters
    ----------
    label:    Stat name shown in the center column.
    matt_val: Pre-formatted Matt value (caller controls number format).
    ryan_val: Pre-formatted Ryan value.
    winner:   ``"Matt"`` | ``"Ryan"`` | ``""`` — highlights winner's value.
    """
    matt_cls = "tb-cr-matt-win" if winner == "Matt" else ""
    ryan_cls = "tb-cr-ryan-win" if winner == "Ryan" else ""
    return _compact(f"""
    <div class="tb-comparison-row">
        <div class="tb-cr-matt {matt_cls}">{matt_val}</div>
        <div class="tb-cr-label">{label}</div>
        <div class="tb-cr-ryan {ryan_cls}">{ryan_val}</div>
    </div>
    """)


def comparison_panel(title: str, rows_html: str) -> str:
    """
    Labeled container for a stack of ``rivalry_stat_row()`` entries.

    Reusable on any page that needs side-by-side Matt / Ryan stat comparison.
    """
    return _compact(f"""
    <div class="tb-comparison-panel">
        <div class="tb-comparison-title">{title}</div>
        {rows_html}
    </div>
    """)


# ---------------------------------------------------------------------------
# Draft class card — War Room signature feature
# ---------------------------------------------------------------------------

def draft_class_card(
    year: int,
    total_picks: int,
    winner: str,
    matt: dict,
    ryan: dict,
) -> str:
    """
    Draft class report card — shows both owners' performance for one year.

    Parameters
    ----------
    year:        Draft year (e.g. 2015).
    total_picks: Total picks in the class across both owners.
    winner:      ``"Matt"`` | ``"Ryan"`` | ``"Tie"`` — who won the class.
    matt:        Dict with keys: total, scored, avg_score, franchise, busts, grade.
    ryan:        Same structure as ``matt``.
    """
    def _side(stats: dict, owner: str, side_cls: str) -> str:  # noqa: E306
        won     = winner == owner
        avg_raw = stats.get("avg_score", 0.0)
        avg_str = f"{avg_raw:.1f}" if stats.get("scored", 0) else "—"
        val_cls = ("tb-matt" if owner == "Matt" else "tb-ryan") if won else ""

        return f"""
        <div class="tb-class-side {side_cls}">
            <div class="tb-class-owner-label">{owner.upper()}</div>
            <div class="tb-class-body">
                <div class="tb-cs-row">
                    <span class="tb-cs-label">Picks</span>
                    <span class="tb-cs-value">{stats.get('total', 0)}</span>
                </div>
                <div class="tb-cs-row">
                    <span class="tb-cs-label">Avg Score</span>
                    <span class="tb-cs-value {val_cls}">{avg_str}</span>
                </div>
                <div class="tb-cs-row">
                    <span class="tb-cs-label">Franchise</span>
                    <span class="tb-cs-value">{stats.get('franchise', 0)}</span>
                </div>
                <div class="tb-cs-row">
                    <span class="tb-cs-label">Busts</span>
                    <span class="tb-cs-value">{stats.get('busts', 0)}</span>
                </div>
            </div>
            <div class="tb-class-grade-wrap">{grade_badge(stats.get('grade', '—'))}</div>
        </div>
        """

    return _compact(f"""
    <div class="tb-class-card">
        <div class="tb-class-header">
            <span class="tb-class-year">{year}</span>
            <span class="tb-class-total">{total_picks} picks</span>
            {winner_badge(winner)}
        </div>
        <div class="tb-class-sides">
            {_side(matt, "Matt", "tb-class-side-matt")}
            {_side(ryan, "Ryan", "tb-class-side-ryan")}
        </div>
    </div>
    """)


# ---------------------------------------------------------------------------
# Legacy Center — museum-identity components
# Reused by Man Status and future analytics pages.
# ---------------------------------------------------------------------------

def legacy_leaderboard_row(rank: int, name: str, owner: str, score: float) -> str:
    """Gold-register leaderboard row for the Legacy Center GOAT Race."""
    s = _safe_score(score)
    bar_cls = "tb-lc-bar-matt" if owner == "Matt" else "tb-lc-bar-ryan"
    return f"""
<div class="tb-lc-leader-row">
  <div class="tb-lc-leader-rank">{rank}</div>
  <div class="tb-lc-leader-info">
    <div class="tb-lc-leader-name">{_html.escape(str(name))}</div>
    <div class="tb-lc-leader-meta">{owner_chip(owner)}</div>
  </div>
  <div class="tb-lc-leader-bar-wrap">
    <div class="tb-lc-leader-bar {bar_cls}" style="width:{s}%"></div>
  </div>
  <div class="tb-lc-leader-score">{_fmt_score(score)}</div>
</div>"""


def exhibit_card(icon: str, title: str, subtitle: str, is_available: bool = True, anchor: str = "") -> str:
    """Museum exhibit navigation card — icon · title · subtitle · enter affordance."""
    avail_cls = "" if is_available else " tb-exhibit-unavailable"
    btn_text  = "VIEW EXHIBIT →" if is_available else "COMING SOON"
    badge     = "" if is_available else '<div class="tb-exhibit-badge">ENTRIES PENDING</div>'
    card = f"""
<div class="tb-exhibit-card{avail_cls}">
  <div class="tb-exhibit-icon">{icon}</div>
  <div class="tb-exhibit-title">{title}</div>
  <div class="tb-exhibit-sub">{subtitle}</div>
  {badge}
  <div class="tb-exhibit-btn">{btn_text}</div>
</div>"""
    if anchor:
        return f'<a href="#{anchor}" class="tb-exhibit-anchor">{card}</a>'
    return card


def award_count_tile(icon: str, count: int, label: str) -> str:
    """Trophy icon + dynasty-wide award total tile for the awards grid."""
    return f"""
<div class="tb-award-tile">
  <div class="tb-award-icon">{icon}</div>
  <div class="tb-award-count">{count}</div>
  <div class="tb-award-label">{label}</div>
</div>"""


def timeline_node(year: int, label: str, winner: str, is_milestone: bool = False) -> str:
    """Dynasty Timeline horizontal node — dot colored by class winner."""
    owner_cls = {
        "Matt":    "tb-timeline-matt",
        "Ryan":    "tb-timeline-ryan",
        "Tie":     "tb-timeline-tie",
    }.get(winner, "tb-timeline-pending")
    milestone_cls = " tb-timeline-milestone" if is_milestone else ""
    return f"""
<div class="tb-timeline-node {owner_cls}{milestone_cls}">
  <div class="tb-timeline-dot"></div>
  <div class="tb-timeline-year">{year}</div>
  <div class="tb-timeline-label">{_html.escape(str(label))}</div>
</div>"""


def legacy_spotlight_card(
    name: str,
    owner: str,
    position: str,
    year: int,
    round_: int,
    score,
    tier: str,
    facts: list,
    awards_html: str,
) -> str:
    """Ceremonial featured-player card for the Legacy Spotlight section."""
    pending    = is_score_pending(score)
    score_disp = score_pending_badge() if pending else _fmt_score(score)
    rd_str     = f"Round {safe_int(round_)}" if round_ else "—"
    facts_html = "".join(
        f'<div class="tb-spotlight-fact">★ {_html.escape(str(f))}</div>' for f in facts
    )
    awards_block = (
        f'<div class="tb-spotlight-awards">{awards_html}</div>' if awards_html else ""
    )
    return f"""
<div class="tb-lc-spotlight">
  <div class="tb-spotlight-header">LEGACY SPOTLIGHT</div>
  <div class="tb-spotlight-sub">DYNASTY'S GREATEST PLAYER</div>
  <div class="tb-spotlight-name">{_html.escape(str(name))}</div>
  <div class="tb-spotlight-meta">{owner_chip(owner)}&nbsp;{position_chip(position)}</div>
  <div class="tb-spotlight-score-row">
    <span class="tb-spotlight-score-label">Score</span>
    <span class="tb-spotlight-score-val">{score_disp}</span>
    &nbsp;{tier_badge(tier)}
  </div>
  <div class="tb-spotlight-draft">{year} · {rd_str}</div>
  {facts_html}
  {awards_block}
</div>"""


# ---------------------------------------------------------------------------
# Man Status — fight-card identity components
# Reusable by Analytics and any future rivalry page.
# ---------------------------------------------------------------------------

def ms_scoreboard_hero(
    matt_wins: int,
    ryan_wins: int,
    ties: int,
    pending: int,
    leader: str,
) -> str:
    """
    Man Status main-event arena hero — the all-time series championship tally.

    Blue corner (Matt) vs Red corner (Ryan), full-width broadcast banner.
    """
    leader_cls  = "tb-ms-leader-matt" if leader == "Matt" else "tb-ms-leader-ryan"
    leader_text = f"{leader.upper()} LEADS THE SERIES"
    return f"""
<div class="tb-ms-arena">
  <div class="tb-ms-arena-blue-glow"></div>
  <div class="tb-ms-arena-red-glow"></div>
  <div class="tb-ms-arena-inner">
    <div class="tb-ms-eyebrow">🥊 &nbsp; THE MAIN EVENT · ALL-TIME SERIES RECORD &nbsp; 🥊</div>
    <div class="tb-ms-title">MAN STATUS</div>
    <div class="tb-ms-tagline">THE ULTIMATE RIVALRY. THE ULTIMATE BATTLE.</div>
    <div class="tb-ms-corners">
      <div class="tb-ms-corner tb-ms-corner-matt">
        <div class="tb-ms-corner-label">BLUE CORNER</div>
        <div class="tb-ms-corner-name">MATT</div>
        <div class="tb-ms-corner-record">{matt_wins}W · {ryan_wins}L · {ties}T</div>
      </div>
      <div class="tb-ms-tally">
        <div class="tb-ms-tally-row">
          <div class="tb-ms-tally-num tb-ms-tally-matt">{matt_wins}</div>
          <div class="tb-ms-tally-sep">–</div>
          <div class="tb-ms-tally-num tb-ms-tally-ryan">{ryan_wins}</div>
        </div>
        <div class="tb-ms-tally-sub">
          <span class="tb-ms-tally-ties">{ties} TIES</span>
          <span class="tb-ms-tally-dot">·</span>
          <span class="tb-ms-tally-pending">{pending} PENDING</span>
        </div>
        <div class="tb-ms-leader-badge {leader_cls}">{leader_text}</div>
      </div>
      <div class="tb-ms-corner tb-ms-corner-ryan">
        <div class="tb-ms-corner-label">RED CORNER</div>
        <div class="tb-ms-corner-name">RYAN</div>
        <div class="tb-ms-corner-record">{ryan_wins}W · {matt_wins}L · {ties}T</div>
      </div>
    </div>
  </div>
</div>"""


def ms_tale_header(
    year: int,
    matt_pick: str,
    matt_pos: str,
    ryan_pick: str,
    ryan_pos: str,
    winner: str,
    margin: int,
) -> str:
    """
    Tale of the Tape two-fighter face-off banner header for the featured bout.
    Sits above a comparison_panel() block.
    """
    if winner in ("Matt", "Ryan"):
        result_line = f"{winner} wins · by {margin}"
    elif winner == "Tie":
        result_line = "Draw · Margin 0"
    else:
        result_line = "Pending · TBD"
    return f"""
<div class="tb-ms-tot-wrap">
  <div class="tb-ms-tot-header">
    <div class="tb-ms-tot-side">
      <div class="tb-ms-tot-fighter tb-ms-tot-fighter-matt">{_html.escape(str(matt_pick))}</div>
      <div class="tb-ms-tot-pos">{owner_chip("Matt")}&nbsp;{_html.escape(str(matt_pos))}</div>
    </div>
    <div class="tb-ms-tot-center">
      <div class="tb-ms-tot-vs">VS</div>
      <div class="tb-ms-tot-year-label">{year}</div>
      <div class="tb-ms-tot-result">{result_line}</div>
    </div>
    <div class="tb-ms-tot-side tb-ms-tot-side-right">
      <div class="tb-ms-tot-fighter tb-ms-tot-fighter-ryan">{_html.escape(str(ryan_pick))}</div>
      <div class="tb-ms-tot-pos">{_html.escape(str(ryan_pos))}&nbsp;{owner_chip("Ryan")}</div>
    </div>
  </div>"""


def ms_bout_card(
    year: int,
    matt_pick: str,
    matt_pos: str,
    matt_score,
    matt_resume: str,
    ryan_pick: str,
    ryan_pos: str,
    ryan_score,
    ryan_resume: str,
    winner: str,
    margin,
    matt_notes: str = "",
    ryan_notes: str = "",
) -> str:
    """
    Single Man Status bout card — one year's head-to-head matchup row.

    winner: 'Matt' | 'Ryan' | 'Tie' | 'Pending'
    All text escaping handled internally.
    """
    is_pending = winner == "Pending"
    is_tie     = winner == "Tie"

    state_cls = {
        "Matt":    "tb-ms-bout-matt-win",
        "Ryan":    "tb-ms-bout-ryan-win",
        "Tie":     "tb-ms-bout-tie",
        "Pending": "tb-ms-bout-pending",
    }.get(winner, "tb-ms-bout-pending")

    def _pick_block(name, pos, score, resume, notes, side, is_winner) -> str:
        side_cls = f"tb-ms-pick-{side}"
        win_cls  = " tb-ms-pick-winner" if is_winner else ""
        if is_pending or str(name) == "nan":
            return (
                f'<div class="tb-ms-pick {side_cls}">'
                f'<div class="tb-ms-pick-name tb-ms-pick-tbd">TBD</div>'
                f'</div>'
            )
        score_str  = str(safe_int(score)) if not is_score_pending(score) else "TBD"
        score_cls  = "tb-matt" if side == "matt" else "tb-ryan"
        resume_str = str(resume) if str(resume) not in ("nan", "", "â") else ""
        notes_str  = str(notes)  if str(notes)  not in ("nan", "")      else ""
        resume_html = f'<div class="tb-ms-pick-resume">{_html.escape(resume_str)}</div>' if resume_str else ""
        notes_html  = f'<div class="tb-ms-pick-notes">{_html.escape(notes_str)}</div>'   if notes_str  else ""
        return (
            f'<div class="tb-ms-pick {side_cls}{win_cls}">'
            f'<div class="tb-ms-pick-name">{_html.escape(str(name))}</div>'
            f'<div class="tb-ms-pick-pos">{_html.escape(str(pos))}</div>'
            f'<div class="tb-ms-pick-score {score_cls}">{score_str}</div>'
            f'{resume_html}{notes_html}'
            f'</div>'
        )

    matt_html = _pick_block(matt_pick, matt_pos, matt_score, matt_resume, matt_notes,
                            "matt", winner == "Matt")
    ryan_html = _pick_block(ryan_pick, ryan_pos, ryan_score, ryan_resume, ryan_notes,
                            "ryan", winner == "Ryan")

    margin_str = str(safe_int(margin)) if margin is not None and str(margin) != "nan" else "0"

    if is_pending:
        result_html = (
            '<div class="tb-ms-result tb-ms-result-pending">'
            '<div class="tb-ms-result-upcoming">UPCOMING</div>'
            '<div class="tb-ms-result-tbd">TBD</div>'
            '</div>'
        )
    elif is_tie:
        result_html = (
            '<div class="tb-ms-result tb-ms-result-tie">'
            '<div class="tb-ms-result-draw">DRAW</div>'
            f'<div class="tb-ms-result-margin" style="color:#6A5010">Margin {margin_str}</div>'
            '</div>'
        )
    else:
        w_cls  = "tb-ms-result-matt" if winner == "Matt" else "tb-ms-result-ryan"
        by_cls = "tb-matt"           if winner == "Matt" else "tb-ryan"
        result_html = (
            f'<div class="tb-ms-result {w_cls}">'
            f'<div class="tb-ms-result-winner">{winner.upper()} WINS</div>'
            f'<div class="tb-ms-result-margin {by_cls}">by {margin_str}</div>'
            f'</div>'
        )

    return (
        f'<div class="tb-ms-bout-card {state_cls}">'
        f'<div class="tb-ms-bout-year">{year}</div>'
        f'{matt_html}'
        f'<div class="tb-ms-bout-vs">VS</div>'
        f'{ryan_html}'
        f'{result_html}'
        f'</div>'
    )
