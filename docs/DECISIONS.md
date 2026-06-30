# Engineering Decisions

Decisions recorded here explain the WHY behind significant architectural choices.
Future engineers should consult this before changing any listed behavior.

> **SESSION MEMORY DOES NOT PERSIST.** This `docs/` folder is the project's memory.
> On any fresh Claude Code session, read `docs/PROJECT_STATUS.md` first (app snapshot,
> data pipeline, what's next), then this file (architectural decisions), then
> `docs/KNOWN_ISSUES.md` (open bugs) before making changes. Log every real decision
> here in newest-first order so the next session can reconstruct state without
> relying on chat history.

---

## D034 — Cleanup pass: Legacy Facts layout, Analytics live strings, margin precision (2026-06-30)

**Date:** 2026-06-30
**Status:** Complete

Three targeted fixes. Scoring, tiers, and cutoffs untouched.

**(a) Legacy Facts layout (cosmetic)**
Root cause: `tb-lc-rivalry-box` has no max-width, so the standalone Facts panel
fills the full content column (~860px). `tb-lc-moments-wrap` used
`justify-content: space-between`, spreading five rows across the full height.

Fix: New `.tb-lc-facts-solo-wrap` class (`max-width: 560px; margin: 0 auto`) wraps
the panel in Legacy.py. Two scoped overrides under it reset the moments-wrap to
`flex-start` and tighten row padding from `10px 0` → `6px 0`. The shared
`.tb-lc-rivalry-box` and `.tb-lc-moments-wrap` classes are unchanged — no risk to
the Glance/Facts equal-height row elsewhere on the page.

**Files changed:** `assets/theme.css`, `pages/Legacy.py`.

**(b) KI-011 / KI-012 — Analytics hardcoded strings replaced with live values**
Two strings in `pages/Analytics.py` carried hardcoded snapshot numbers.

KI-011 (Badge Distribution): `"Matt leads SB Wins 24–20. SB MVP split 1–1."` was
hardcoded. Now extracted from `badge_rows_data` (already built on the page).
SB wins leader is also computed, not assumed.

KI-012 (Franchise Balance): `"Ryan leads franchise production 2.2× over Matt"` was
hardcoded. Now computed from `ryan_st['franchise'] / matt_st['franchise']` (already
on the page) with a division-by-zero guard. Leader name is also computed.

Current values happen to match the old hardcoded strings — confirmed correct.

**Files changed:** `pages/Analytics.py`.

**(c) KI-013 — Margin truncation in stats.py**
`int(big_row["MARGIN"])` and `int(close_row["MARGIN"])` truncated decimal margins
(46.5 displayed as 46). Changed to `round(float(...), 1)`. ManStatus.py's existing
`f'+{summary["biggest_margin"]}'` renders floats correctly — no page change needed.

Verified: biggest_margin = 46.5, closest_margin = 8.0.

**Files changed:** `core/stats.py`.

---

## D033 — Legend floor raised from 90 to 95 (2026-06-30)

**Date:** 2026-06-30
**Status:** Active

Legend cutoff moved from 90 → 95 in `TIER_CUTOFFS` in `core/stats.py`. One-line change.

**Why:** At 90, Legend caught Derrick Henry (91.3) and Cam Newton (91.0), who feel
a step below the true immortals. At 95, Legend is exactly six players:
Ramsey (100), Kupp (100), Matt Ryan (99.5), Garrett (97.6), Watt (95.8), Saquon (95.4).
Henry and Cam drop to top-of-Franchise — correct by the product's standard.

**Tier table after adjustment:**
```
Legend           ≥ 95   (was 90)
Franchise        80 – 94.9
High-End Starter 68 – 79.9
Starter          54 – 67.9
Contributor      40 – 53.9
Bust             < 40
```

Legend: Matt 2 (Ramsey, Saquon) · Ryan 4 (Kupp, Matt Ryan, Garrett, Watt).

**Files changed:** `core/stats.py` (one line).

---

## D032 — Six score-derived tiers; HOF badge mechanism; class_grade() docstring fix (2026-06-30)

**Date:** 2026-06-30
**Status:** Active — LOCKED. Boundaries are adjustable; the "no per-player overrides" principle is not.

**Tier system (replaces old 5-tier workbook column):**
```
Legend           ≥ 90
Franchise        80 – 89.9
High-End Starter 68 – 79.9
Starter          54 – 67.9
Contributor      40 – 53.9
Bust             < 40
```

**Distribution (326 scored players, 28 TBD):**
| Tier             | Total | Matt | Ryan |
|------------------|-------|------|------|
| Legend           |     8 |    3 |    5 |
| Franchise        |    24 |    7 |   17 |
| High-End Starter |    64 |   24 |   40 |
| Starter          |   116 |   64 |   52 |
| Contributor      |    60 |   34 |   26 |
| Bust             |    54 |   31 |   23 |

Ryan is heavier at the top; Matt is heavier in the middle and bottom. This is correct and
intentional — the app is an honesty machine. Do not soften it.

**Implementation:**
- `score_to_tier(score)` in `core/stats.py` — single definition of the cutoffs.
- `TIER_CUTOFFS` (list of `(min_score, name)` tuples) and `FRANCHISE_TIERS`
  (frozenset `{"Legend", "Franchise"}`) also in `core/stats.py`.
- `load_players()` in `core/data_loader.py` now applies `score_to_tier()` on every
  load, overwriting the workbook's `CAREER_TIER` column. The workbook column is
  permanently ignored — tiers are always computed live from OVERALL SCORE.
- `load_players()` now has its own `@st.cache_data` decorator (was a passthrough).
- All `CAREER_TIER == "Franchise"` filters updated to `.isin(FRANCHISE_TIERS)`
  in `compute_league_stats`, `compute_owner_stats`, `compute_class_stats`,
  `compute_hall_of_fame`, `compute_legacy_moments`.
- `compute_hall_of_fame()` now includes Legend + Franchise players (score ≥ 80).
- `tier_badge()` in `components.py` updated with `"Legend": "tb-tier-legend"`.
- `.tb-tier-legend` CSS added to `assets/theme.css` (bright yellow, bold).
- Players.py tier filter dropdown updated to include "Legend" as first option after "All".

**HOF badge mechanism:**
- HOF is NOT a tier. It is a hand-set flag for real-life Hall of Fame inductees.
- `load_players()` reads a `HOF` column from the workbook if present; defaults to
  `False` for all players if the column is absent.
- `hof_badge()` function added to `core/components.py`.
- `.tb-hof-badge` CSS added to `assets/theme.css` (Legacy gold `#D4AF37`).
- HOF column in the workbook is currently empty — Matt marks inductees as warranted.
  Adding the column to the workbook is all that's needed; the badge appears automatically.

**class_grade() docstring fix:**
- Stale reference values updated: `best class avg = 71.0 → 76.25 (2008)`,
  `league avg = 56.5 → 57.11`. Grade thresholds (S/A/B/C/D) unchanged.
  See KI-014 in `KNOWN_ISSUES.md` — the thresholds may still need recalibration,
  but that is a product decision deferred to a future session.

**Files changed:** `core/stats.py`, `core/data_loader.py`, `core/components.py`,
`assets/theme.css`, `pages/Players.py`, `docs/DECISIONS.md`, `docs/PROJECT_STATUS.md`.

---

## D031 — Score display shows one decimal place; Rankings tie-aware featured cutoff (2026-06-30)

**Date:** 2026-06-30
**Status:** Complete

Two tightly coupled display fixes shipped together after SCORING MODEL v1.0 (D030)
exposed decimal precision that the old `int()` rendering was hiding.

**(a) `fmt_score` — single definition for score display:**
Added `fmt_score(score, pending_str="—") -> str` to `core/utils.py`. Returns one
decimal place with trailing `.0` stripped: 95.8 → "95.8", 100.0 → "100", 91.0 → "91".
Returns `pending_str` for NaN/invalid. `_fmt_score()` in `core/components.py` is now
a thin wrapper calling `fmt_score(score, pending_str="0")` for component-internal use.

All seven component display callsites updated (player_row, elite_player_card,
player_detail_card, class_dive_row, player_roster_row, legacy_leaderboard_row,
legacy_spotlight_card). Page-level callsites in Dashboard.py, Players.py, and Legacy.py
also updated. `_safe_score()` unchanged — still returns int for CSS bar-width `%`
calculations. `fmt_score` is the score display function; `_safe_score` is bar math only.

**(b) Rankings tie-aware featured cutoff:**
`_cutoff_score = float(scored.iloc[4]["OVERALL SCORE"])` (5th player's true unrounded
score). Featured = `_score >= _cutoff_score` compared on raw float; THE FIELD divider
inserts before the first non-featured player. Replaces the previous hardcoded
`_rank <= 5` / `_rank == 6` position-based split.

**Why:** With the new scoring model carrying decimal precision (95.8, 99.5 etc.),
displaying both Watt (95.8) and Saquon (95.4) as "95" looked like a tie where none
existed. For the cutoff: if two players share the exact same true score at the
featured boundary, the old position-based split would arbitrarily put one in THE FIELD.
The tie-aware version groups them correctly.

**Files changed:** `core/utils.py`, `core/components.py`, `pages/Rankings.py`,
`pages/Dashboard.py`, `pages/Players.py`, `pages/Legacy.py`.

---

## D030 — SCORING MODEL v1.0 LOCKED (2026-06-29)

**Date:** 2026-06-29
**Status:** Active — LOCKED. Formula never changes; only inputs change.

**Philosophy:** The hand-calibrated OVERALL SCORE in the `players` sheet is the
production backbone. Awards are layered as a bonus, capped to prevent double-counting
signal already embedded in the baseline. Award-less players are unchanged. The model
measures WHAT HAPPENED in a career; owner-fair.

**Formula:**
```
OVERALL SCORE = min(100, baseline + 0.6 × min(award_points, 16))
```
Award weights: MVP 6, SB_MVP 4, OPOY 3, DPOY 3, ALL_PRO 2.5, SB Win 2.5, OROY 1, DROY 1.
Award cap: 16 points (before the 0.6 multiplier). Score ceiling: 100.

**Results:** 326 players scored. ~70 moved (decorated-only; awards not yet reflected).
256 unchanged (no awards, or awards already embedded in baseline). 75 distinct score
values. Owner averages: Matt ~54.2, Ryan ~60.0 — rivalry balance preserved.

**Man Status alignment:** MATT_SCORE / RYAN_SCORE values realigned to the same scale.
Example: Matt Ryan 118 → 99.5. Zero winners flipped. Series record stays 6-10-3.

**Wildcards:** Intentionally left on their own WC Score / Cooked Meter system.
Do NOT rescale wildcard scores to the players model.

**Documentation:** Model parameters documented in the `SCORING_MODEL_v1` sheet
inside `backend/AP_Dynasty_Backend.xlsx`.

**THE RULES ARE LOCKED.** Only inputs change going forward (new awards, HOF, rings).
Never rebuild the formula. HOF credit is a future input column with a one-time weight
within this framework — not a formula change.

---

## D029 — Cosmetic cleanup batch: chip styling, Rankings restructure, page icons (2026-06-29)

**Date:** 2026-06-29
**Status:** Complete

**(a) Dashboard chip styling:** Corrected bare `tb-chip-matt`/`tb-chip-ryan` to
`tb-chip tb-chip-matt`/`tb-chip tb-chip-ryan` — the base `tb-chip` class is required
for layout/padding. Affected the GOAT Race mini-rows.

**(b) Rankings restructure:** Removed the standalone `#1 RANKED` card (single card in
a 4-column grid with dead whitespace to its right). Replaced with:
- Centered `OVERALL LEADERBOARD` header with subtitle and blue rule (`.rk-overall-header`)
- Top-5 featured emphasis via `.rk-lead-featured` (left gold accent border, larger name
  and score text)
- `THE FIELD` divider at position 6 (`.rk-field-break`)

This resolves the D027(b) deferred item.

**(c) Page icons (permanent):**
- Man Status: 🥊 (boxing glove — matches fight-card / UFC identity)
- War Room: ⚔️ (crossed-swords retained — draft battle metaphor)
These are distinct and permanent. Do not swap.

**(d) Players stat-row reworked to roster-scoped cards:**
Replaced HIGHEST SCORE / LOWEST SCORE / BEST DRAFT CLASS (record facts that duplicated
Quick Insights) with: TOTAL PLAYERS, SCORED (+ TBD count), POSITION GROUPS, FRANCHISE
PLAYERS (with % subtitle). No collision with Quick Insights below. This resolves the
D027(a) deferred item.

**Files changed:** `pages/Dashboard.py`, `pages/Rankings.py`, `pages/ManStatus.py` (icon),
`pages/WarRoom.py` (icon), `pages/Players.py` (stat-row).

---

## D028 — Phase 2: "link don't reprint" — full player lists consolidated to Rankings (2026-06-29)

**Date:** 2026-06-29
**Status:** Complete

Phase 2 of the redundancy cleanup (see D026 for Phase 1). Any page that showed a full
player leaderboard now links to Rankings instead of re-listing.

- **Dashboard GOAT Race:** Shows a top-3 mini-teaser (`.db-goat-mini-row`) +
  `st.page_link("pages/Rankings.py", label="View full rankings →")`. No more top-25 list.
- **Players — Elite Players section:** Section header subtitle reads "full leaderboard
  on Rankings" + `st.page_link("pages/Rankings.py", label="View the Overall Leaderboard →")`.
  No more full elite-card grid.

Rankings is now the sole authoritative home for the Overall Leaderboard.

**Why:** Two lists create a sync problem. If ranking order changes (new player scores,
scoring model update), Dashboard and Players would show stale order until manually
touched. Teasers drive navigation without re-printing the list.

---

## D027 — Cosmetic debt resolved: Players cards and Rankings #1 banner (2026-06-29)

**Date:** 2026-06-29
**Status:** Complete — both items resolved in D029

Two cosmetic issues deferred at Phase 1 close, batched for a small cleanup phase.
Both were addressed; see D029 for the implementation details.

**(a) Players top stat-row** — Resolved in D029(d). Reworked from record-facts
(HIGHEST/LOWEST SCORE, BEST DRAFT CLASS) to roster-scoped cards (TOTAL PLAYERS /
SCORED / POSITION GROUPS / FRANCHISE PLAYERS). No collision with Quick Insights.

**(b) Rankings #1 RANKED card** — Resolved in D029(b). Replaced with centered
OVERALL LEADERBOARD header + top-5 featured emphasis + THE FIELD divider.

---

## D026 — Phase 1 complete: redundant owner stat-blocks removed from page bodies (2026-06-29)

**Date:** 2026-06-29
**Status:** Complete

The sidebar Rivalry box (Matt 53.8 / Ryan 59.3) is now the sole authoritative home for owner-comparison numbers. Redundant reprints were removed from the body of four pages. Dashboard and Analytics were not touched in this phase.

**Per-page changes:**
- **Rankings:** Removed MATT AVG / RYAN AVG / SCORE EDGE stat cards. Kept #1 RANKED card (leaderboard pointer, not an owner-block repeat).
- **War Room:** Removed the entire RIVALRY SNAPSHOT section (comparison panel: 177/177 players, 53.8/59.3 avg, 15/33 franchise, 10/10 busts, 94/94 best) plus the three callout cards below it (Best Draft Class / Franchise Leader / Avg Score Edge). Kept the 4 series-record stat cards (draft-class wins/ties/series leader), Report Cards, and Deep Dive.
- **Legacy:** Removed the DYNASTY AT A GLANCE 6-tile grid (354 players / 20 classes / 48 franchise / 20 busts / 94 top score / 44 rings). Kept Legacy Facts panel (rendered standalone, flex wrapper removed since it no longer pairs with anything).
- **Players:** Removed MATT / RYAN / FRANCHISE / AVG SCORE cards (the owner block). Kept TOTAL PLAYERS, HIGHEST SCORE, LOWEST SCORE, BEST DRAFT CLASS in a single row.

**Now-unused variables (deliberately left in place — pruned in Phase 5):** `matt_stats`, `ryan_stats`, `leader`, `_delta` in Rankings.py and WarRoom.py; `bust_winner`, `franchise_winner`, `score_winner`, `high_score_winner`, and `callout`/`comparison_panel` imports in WarRoom.py; `ls["bust_total"]` no longer consumed on Legacy. No helpers or imports were pruned in this phase.

**Roadmap:** Phase 2 = "link don't reprint" for the top-25 score list (Rankings as home). Phase 3 = draft-class rankings consolidate to War Room. Phase 4 = Dashboard slims to landing hub. Phase 5 = Analytics rebuild (cut repeat panels, add score-over-time / draft hit-rate / wildcards) + prune unused vars from this decision.

---

## D025 — Bug fix: Dashboard/Players Franchise card subtitle corrected (2026-06-29)

**Date:** 2026-06-29
**Status:** Complete

`ls['bust_total']` (20) was appearing as the subtitle on the FRANCHISE PLAYERS card on both Dashboard and Players — correct number, wrong card. Replaced with `f"{round(ls['franchise_total']/ls['total_players']*100)}% of all drafted"` (= 14%) on both pages so the card is self-consistent. Bust count is not lost — it lives correctly in Analytics Owner Comparison.

Also corrected Dashboard-only: `ls['positions']` = 18 (raw `df["POSITION"].nunique()`) was subtitled as "18 positions" under TOTAL PLAYERS. Changed to `f"{len(POSITION_GROUPS)} position groups"` (= 12), consistent with the canonical groups used on every other page. Required adding `POSITION_GROUPS` import to `Dashboard.py`. Players.py was unaffected (it already used `draft_classes`).

**Files changed:** `pages/Dashboard.py`, `pages/Players.py`.

---

## D024 — Bug fix: Legacy exhibit tile scroll navigation implemented (2026-06-29)

**Date:** 2026-06-29
**Status:** Complete

The 8 Legacy exhibit tiles ("VIEW EXHIBIT →") had never had navigation implemented — `exhibit_card()` in `core/components.py` generated plain `<div>` elements with no `href`, no click handler, no anchor target. All 8 exhibit rooms already existed lower on the same page; the tiles were purely decorative.

**Fix:** Added `anchor: str = ""` parameter to `exhibit_card()`. When provided, the card is wrapped in `<a href="#{anchor}" class="tb-exhibit-anchor">`. Added `a.tb-exhibit-anchor` CSS rule to `assets/theme.css` (text-decoration:none; color:inherit; display:block) plus `html,body{scroll-behavior:smooth}`. Added `id=` targets at each of the 8 exhibit rooms in `Legacy.py`. For the two column-split sections (Mount Rushmore, All-Franchise) where the room `<div>` is inside a `st.columns()` context, a zero-height `st.markdown('<div id="..."></div>')` is injected immediately before the `st.columns()` call as the anchor target.

**Anchor → id mapping (8 pairs):** goat-race / mount-rushmore / legacy-hall / record-book / all-franchise / greatest-classes / hall-of-shame / dynasty-timeline.

**Files changed:** `core/components.py`, `assets/theme.css`, `pages/Legacy.py`. No other page calls `exhibit_card()`.

---

## D023 — Housekeeping verified clean (2026-06-29)

**Date:** 2026-06-29
**Status:** Complete

Verified: zero `.tmp`/`.swp`/`.bak` files in project tree; `#D4A55F` appears nowhere (all spec docs correctly carry `#D4AF37`). No changes made.

---

## D022 — Fire 4 DB split: POSITION_GROUPS expanded from 9 to 12 groups

**Date:** 2026-06-28
**Status:** Complete

Replaced the single `"DB": ["CB", "S", "SS", "FS"]` bucket in `POSITION_GROUPS` (`core/stats.py`) with four separate entries: `"CB": ["CB"]`, `"SS": ["SS"]`, `"FS": ["FS"]`, `"S": ["S"]`. One-line change — no page files touched.

**Final POSITION_GROUPS (12 groups):** QB, RB, WR, TE, OL, EDGE/DE, DT, LB, CB, SS, FS, S.

**Verified across all three consumers:**
- Rankings — position tab strip shows 12 tabs (CB/SS/FS/S replace DB); thin SS/FS buckets (8 players each) render with correct `(n=X)` annotation on the comparison panel avg; no DB tab.
- Legacy All-Franchise — exhibit shows 12 best-per-position rows (4 new DB rows replace 1); null-safety guard handles any owner with zero scored players at a thin position.
- Players — position filter dropdown shows 13 options (All + 12 groups); CB/SS/FS/S as separate filters, no DB option.

**Thin-bucket rule confirmed:** No minimum-count visibility guard added. `MIN_RANKED_SAMPLE` remains a text annotation only — never a gate.

**Analytics impact:** Fire 5 Analytics must reconcile to 12 position columns (was 9).

---

## D021 — Navigation architecture fork: hub-and-spoke vs persistent sidebar

**Date:** 2026-06-28
**Status:** Decided — 2026-06-29

**Decision:** Version A (current persistent sidebar) is the v1 architecture. Analytics and all remaining v1 pages build against the existing sidebar, consistent with the 6 shipped pages. No sidebar restructuring in v1.

Version B (hub-and-spoke, Chip's Dashboard render) is deferred to a **standalone v2 project** (`Trail_Bish_Dynasty_v2` — own folder, own theme, own core, zero shared files with v1). The intent is a working side-by-side comparison app, not a render, so Matt + Bishop can evaluate the nav model against a live build. v2 is not being built now.

**Why a separate clone, not a branch:** Merging hub-and-spoke back into v1 would touch all 7 pages, `core/sidebar.py`, and `app.py`. A standalone v2 lets both nav models run simultaneously without entangling v1 stability.

**Unblocks:** D020 (Dashboard versus-card symmetry) is no longer blocked by the nav question. The versus-card fix proceeds against the v1 sidebar layout when scheduled.

---

## D020 — Dashboard versus-card squaring-off: PAUSED

**Date:** 2026-06-28
**Status:** Paused — unblocked by D021 resolution, not yet scheduled

The Dashboard versus-card has unresolved symmetry issues: VS is not dead-center, the two owner sides are not true mirrors, and the four mini-stats are not gridded symmetrically. These are real presentation defects.

D021 is now resolved (v1 stays on sidebar), so the versus-card fix is no longer blocked. Work has not been scheduled — hold until explicitly queued.

**How to apply:** Fix targets the existing `rivalry_banner()` component / `.tb-rb-side` CSS. Do not rebuild the card structure — achieve mirror symmetry within the current flex layout.

---

## D019 — Fire 4 Legacy visual sub-pass complete

**Date:** 2026-06-28
**Status:** Complete

Presentation-only pass. No core/stats.py changes. No warm-palette color changes.

**Changes landed (all Legacy-only):**

*Part A:*
- Removed the "THE RIVALRY" upper-right panel from the hero section (`pages/Legacy.py`). Duplicated the sidebar rivalry box. `tb-lc-rival-*` / `tb-lc-win-bar-*` CSS classes remain as inert dead CSS.
- Type bump on all small-caps label text: `.tb-lc-panel-title` (9→11px), `.tb-lc-glance-label` (7→9px), `.tb-award-label` (7→9px), `.tb-lc-room-header` (9→11px), `.tb-lc-room-sub` (9→11px), `.tb-spotlight-header` (8→10px), `.tb-spotlight-sub` (7→9px), `.tb-spotlight-score-label` (10→11px), `.tb-spotlight-draft` (10→11px), `.tb-spotlight-fact` (11→12px). Big display type untouched.

*Part B:*
- Hero widened to full content width by removing the `st.columns([2.3, 1])` split and rendering the hero as a bare `st.markdown()`. Left/right edges now flush with the Glance/Facts row below.
- Legacy Facts panel presence bumped: `.tb-lc-rivalry-box` padding 14/16→18/20px; `.tb-lc-moment` row padding 7→10px, gap 7→9px; `.tb-lc-moment-dot` 5→7px; `.tb-lc-moment-text` 11→13px, line-height 1.45→1.6.

*Final touch:*
- Glance/Facts equal-height: replaced the `st.columns([1,1])` split with a single `st.markdown()` inside `.tb-lc-glance-facts-row` (flex, `align-items:stretch`). Both panels now equal height of the taller one (Glance). Facts bullets distributed via `.tb-lc-moments-wrap` (`justify-content:space-between`). Glance grid tiles remain packed top via `align-content:start`. Height treatment fully scoped under `.tb-lc-glance-facts-row` — bare `.tb-lc-rivalry-box` unchanged.

---

## D016 — Man Status reads WINNER/MARGIN from the sheet; never recomputes them

**Date:** 2026-06-28
**Status:** Active

`pages/ManStatus.py` displays the `WINNER` and `MARGIN` columns directly from
the `man status` sheet. It does not re-derive the winner from MATT_SCORE vs
RYAN_SCORE.

**Why:** The composite score that decided each bout (base OVERALL SCORE + award
and tier bonuses) is defined by the product rules baked into the workbook. The
page does not know those bonus weights and should not need to. The sheet is the
authoritative record of who won each bout. Re-deriving on the page would create
a second implementation of the scoring formula that could silently diverge.

**WINNER sentinel strings** (verified 2026-06-28 against the live sheet):
`"Matt"` | `"Ryan"` | `"Tie"` | `"Pending"`. These are normalised by
`ms_winner_state()` in `core/stats.py` — the only place they are matched.
Page code branches on the returned canonical value, never on raw strings.

**Ties vs Pending are distinct states.** Three bouts (2014, 2024, 2025) are
decided draws where both picks scored identically — WINNER=`"Tie"`, MARGIN=0.
One bout (2026) is unfought — WINNER=`"Pending"`, MARGIN=NaN. These render
differently on the page: Ties show "DRAW · Margin 0"; Pending shows "UPCOMING · TBD".
Collapsing them is a product bug.

---

## D001 — @st.cache_resource for pd.ExcelFile

**Date:** 2026-06-27
**Status:** Active

`load_workbook()` uses `@st.cache_resource` instead of `@st.cache_data`.

**Why:** `pd.ExcelFile` holds an open file handle (`BufferedReader`) and is
not picklable. `@st.cache_data` requires pickle serialization for every cache
write. Using `@st.cache_data` raises a `RuntimeError` at runtime.
`@st.cache_resource` is the correct decorator for non-serializable objects —
it stores the object reference directly without serialization.

**Impact:** All sheet DataFrames loaded from the workbook are downstream of
this cached `pd.ExcelFile` object. If this decorator changes, every loader
breaks.

---

## D002 — players sheet is the single source of truth

**Date:** 2026-06-27
**Status:** Active

All aggregate stats are computed from the `players` sheet. No other sheet
is trusted for player counts, scores, or career tiers.

**Why:** The `dashboard`, `AP Rankings`, `Legacy Center`, and `Draft War Room`
sheets are human-readable reporting sheets designed for Excel. They contain
non-tabular layouts, merged cells, stale aggregate data (the `dashboard` sheet
showed 169 players when the actual count is 354), and multi-section layouts
that require fragile offset-based parsing. The `players` sheet is a clean
354-row × 19-column table — the only reliably machine-readable source.

---

## D003 — CSS injection in render_sidebar(), not app.py

**Date:** 2026-06-27
**Status:** Active

Global CSS (`assets/theme.css`) and Streamlit chrome-hiding are applied in
`render_sidebar()`, not in `app.py`.

**Why:** `st.switch_page()` causes a full browser page re-render. Any HTML
or CSS injected by `app.py` is lost immediately after the redirect fires.
Since every page calls `render_sidebar()` first, placing CSS injection there
guarantees the theme is applied on every page without each page needing to
manage assets independently. Chrome-hiding is also included here for the
same reason.

---

## D004 — core/stats.py as the single stats computation layer

**Date:** 2026-06-28
**Status:** Active

All cross-page aggregate computations (league stats, owner stats, score leader,
player rankings) live in `core/stats.py`. Page files import and destructure
the results; they do not derive stats independently.

**Why:** Before this module, Dashboard.py and Players.py independently computed
identical stats (franchise count, avg score, draft classes, best year, etc.).
With caching, the runtime cost was minimal — but the maintenance cost was real:
changing a formula required updating multiple files, and inconsistencies could
silently appear across pages. `core/stats.py` provides a single definition for
every stat.

---

## D005 — Rankings page derives from players, not the AP Rankings sheet

**Date:** 2026-06-28
**Status:** Active

The Rankings page sorts `players` by OVERALL SCORE and uses position filtering.
It does not parse the `AP Rankings` sheet.

**Why:** The `AP Rankings` sheet is a multi-section human-readable dashboard
with 4+ layout sections, repeated headers, and mixed data types in the same
columns. Parsing it requires fragile row-offset logic. The sheet was built
by sorting the players data in the first place — computing the same output from
`players` is simpler, more reliable, and always current.

---

## D006 — Active page passed explicitly to render_sidebar(active="Label")

**Date:** 2026-06-28
**Status:** Active

Pages pass their own label to `render_sidebar(active="PageName")` to drive
the active nav indicator in the sidebar.

**Why:** Streamlit does not reliably expose the current page URL within the
app execution context. Session state alternatives require initialization guards.
Explicit parameter passing is simpler, readable, and requires no infrastructure.
The cost is one string argument per page — worth it for zero complexity.

---

## D007 — NaN scores displayed as "TBD" (not 0) for 2025–26 picks

**Date:** 2026-06-28
**Status:** Active

Players with no OVERALL SCORE (28 of 354 — 2025–26 draft classes) display
a "TBD" badge rather than a score of 0 or an empty cell.

**Why:** A score of 0 is a valid score (Bust tier) and would misrepresent
un-scored players. An empty cell would break the layout. "TBD" accurately
communicates that these players have been drafted but have not yet accumulated
a career score. The `is_score_pending(score)` function in `core/utils.py`
is the single definition for this check — all components call it.

---

## D008 — load_dashboard() removed

**Date:** 2026-06-28
**Status:** Active

`load_dashboard()` was removed from `core/data_loader.py`.

**Why:** No page imported or called it. The `dashboard` sheet is stale (shows
169 players; actual count is 354). Dashboard.py correctly reads from `players`
for all stats. The loader was dead code creating a false impression that the
`dashboard` sheet was authoritative.

---

## D012 — POSITION_GROUPS defined once in core/stats.py

**Date:** 2026-06-28
**Status:** Active

The canonical position-group mapping lives in `core/stats.py` as the module-level
constant `POSITION_GROUPS`. Pages import it rather than defining their own copy.

**Why:** Before this change, `pages/Players.py` defined the position groups inline.
When `pages/Rankings.py` also needed them, they would have been duplicated. Two
definitions of the same mapping diverge over time. A single source in the stats
module is correct because it represents domain knowledge about how positions group
in this dynasty — not a display preference.

**Impact:** Players.py now does `{"All": None, **_POS_GROUPS}` to add its "All"
option. Rankings.py imports `POSITION_GROUPS` directly with no modification.

---

## D013 — MIN_RANKED_SAMPLE enforces small-sample caveat at the stats layer

**Date:** 2026-06-28
**Status:** Active

`MIN_RANKED_SAMPLE = 5` in `core/stats.py` is the threshold below which per-owner
averages must display a sample-size indicator `(n=X)` in the comparison panel.

**Why:** Rankings.md explicitly requires small-sample guarding and says the rule
must be defined in the stats layer, not computed ad hoc in page files. The DT
position group has only 4 players per owner — below the threshold — and
automatically receives the caveat. The page renders `_avg_label()` which reads
`MIN_RANKED_SAMPLE` from stats rather than hard-coding the check.

---

## D010 — Draft War Room derives from players, not the Draft War Room sheet

**Date:** 2026-06-28
**Status:** Active

The War Room page computes all class-level statistics from the `players` sheet
via `compute_class_stats()` in `core/stats.py`. The `Draft War Room` sheet
in the workbook is not used.

**Why:** Same reasoning as D005 (Rankings). The `Draft War Room` sheet is a
non-tabular human-readable reporting layout. `load_war_room()` returns garbled
data when called directly. All class-level facts (avg score, franchise count,
bust count, per-owner per-year breakdown) are fully computable from the clean
`players` table and will always be current without a stale sheet.

---

## D011 — class_grade() thresholds live in stats.py, not components.py

**Date:** 2026-06-28
**Status:** Active

The function that maps avg_score → letter grade (S/A/B/C/D) lives in
`core/stats.py`, not in `core/components.py` or the page file.

**Why:** A grade threshold is a business rule, not a rendering decision.
Placing it in components would require importing stats logic into the view
layer, or duplicating it. Placing it in the page would scatter the definition.
`core/stats.py` is the correct home: any page that displays grades imports
`class_grade` from stats and passes the result to `grade_badge()` in
components. Components only render — they never compute.

---

## D014 — Sprint 5 workbook migration: display/engine sheets removed

**Date:** 2026-06-28
**Status:** Active

The backend workbook was replaced. `AP_Dynasty_Backend.xlsx` now contains
exactly three sheets: `players`, `man status`, `wildcard boys`. All display
and engine sheets (`dashboard`, `AP Rankings`, `Legacy Center`, `Draft War Room`,
`Player Rankings`, `🏆 Hall of Fame`, `🗿 Mount Rushmore`, `⭐ All-Franchise Teams`,
`_ENGINE`, `_ENGINE_OUTPUT`) were deleted.

**Why:** Those sheets were reporting snapshots generated from `players`, not
authoritative sources. They were non-tabular (garbled when parsed), stale
(counts like 169 players vs actual 354), or empty. Keeping them created false
impressions of a data source and required loaders with warning comments. Removing
them enforces the single-source principle: `players` is the database, the
application is the experience.

The `man status picks` sheet (702 columns, horizontal layout, no usable parser)
was replaced with `man status` — a clean 13-column tidy table with title rows
0–2 and data header at row 3. `load_man_status()` is the new loader.

**Impact:** `load_rankings()`, `load_legacy()`, `load_war_room()`, and
`load_player_rankings()` removed from `core/data_loader.py`. No built page
imported these functions — all four built pages (`Dashboard`, `Players`,
`Rankings`, `WarRoom`) use only `load_players()`. Zero page-level breakage.

---

## D015 — Legacy Center exhibits computed entirely from players sheet

**Date:** 2026-06-28
**Status:** Active

All Legacy Center exhibit data (Mount Rushmore, All-Franchise, Hall of Fame, Hall
of Shame, Greatest Classes, Awards, GOAT Race, Dynasty Timeline) is computed in-app
from the `players` sheet. No separate exhibit worksheets exist in the workbook.

**Why:** The prior workbook had dedicated exhibit sheets (`🏆 Hall of Fame`,
`🗿 Mount Rushmore`, `⭐ All-Franchise Teams`) but they were empty — no data had
ever been entered. Rather than maintain a parallel data-entry workflow, every exhibit
is now algorithmically derived:
- Mount Rushmore = top 4 scored players per owner
- All-Franchise = best scored player per POSITION_GROUP per owner
- Hall of Fame / Legacy Hall = all CAREER_TIER=="Franchise" players
- Hall of Shame = all CAREER_TIER=="Bust" players
- Greatest Classes = top N by combined avg score from compute_class_stats()
- Awards = sum each award column across all players
- GOAT Race = rank_players() output, top-N

This approach guarantees every exhibit is always current with the live workbook data
and eliminates a class of data drift bugs where exhibit sheets fall out of sync.

**Impact:** 6 new functions in `core/stats.py`. 5 new components in `core/components.py`.
408 new CSS lines in `assets/theme.css`. Pages importing these functions gain
exhibit-ready data with no additional loader required.

---

## D009 — core/utils.py as a zero-dependency helper module

**Date:** 2026-06-28
**Status:** Active

Shared pure helper functions (`safe_int`, `safe_str`, `is_score_pending`) live
in `core/utils.py` with no Streamlit or pandas imports.

**Why:** Before this module, `safe_int`-equivalent logic was duplicated as
`_int()` in Players.py and implicitly in multiple component functions. A
zero-dependency module allows any other module to import these helpers without
circular import risk. Functions that depend on workbook data belong in
`core/stats.py`; functions that depend on Streamlit belong in `core/sidebar.py`
or `core/components.py`; truly pure helpers belong in `core/utils.py`.

---

## D017 — War Room brass pass paused: canonical --gold orphaned

**Date:** 2026-06-28
**Status:** Unblocked — D018 complete; brass pass may proceed

Fire 3 item 2 (War Room brass warmth) is on hold. The War Room brass inventory
(completed 2026-06-28) revealed a gold split: `--gold: #F3BC2E` is defined in
`:root` but referenced by zero live CSS rules. Every existing gold surface in the
app uses `#F59E0B` (amber) directly — grade-S badge, franchise tier badge, MVP
award badge, gold stat card glow, gold callout accent. Deriving brass from the
orphaned `#F3BC2E` while all warm surfaces live on `#F59E0B` would add a third
gold value to an already-split surface area.

**Unblocking condition:** Gold reconciliation (D018) must land first. Once a
single canonical gold is chosen and all surfaces point to it, brass is a clean
relative derivation from that token.

**War Room inventory is saved** — no work lost. Full surface list:
- `rgba(245,158,11,...)` / `#F59E0B` — grade-S badge, franchise badge, MVP badge,
  gold stat card glow, gold callout left border
- Owner blue/red — winner badges, class-side tints, owner labels, comparison panel
  win highlights, dive row hover, inline styles in WarRoom.py (lines 180, 186, 306, 307)
- Scope mechanism confirmed: `.stApp` injection in WarRoom.py as sole injector
  (same pattern as ManStatus.py). No page wrapper exists; `.stApp` covers all elements.

---

## D018 — Gold reconciliation: queued pass, not to be done mid-fire

**Date:** 2026-06-28
**Status:** Complete — 2026-06-28

The gold token surface is currently split between two values:
- `--gold: #F3BC2E` — defined in `:root`, zero references (orphan)
- `#F59E0B` — live amber used directly by all warm surfaces app-wide

Gold reconciliation is its own atomic pass:
1. Decide the single canonical gold (`#F3BC2E` vs `#F59E0B` — product decision,
   not engineering)
2. Point every gold surface to it via `var(--gold)`
3. Remove the orphan entry or update its value to match
4. Verify zero stray literals remain across all pages and components

**Constraint:** This pass touches shared classes used on Players, Rankings,
Legacy, and War Room (`.tb-tier-franchise`, `.tb-award-mvp`, `.tb-grade-S`,
`.tb-callout.tb-gold`, `.tb-gold`). It must not run mid-fire or alongside
any other CSS pass — run it standalone and verify all pages before closing.

**Legacy exception:** `#D4AF37` is the Legacy warm-gold (Hall of Fame aesthetic).
It is intentional and permanent. Gold reconciliation touches only the cold-page
amber/gold token — never Legacy's `#D4AF37`.
