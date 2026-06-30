# Project Status

**Last updated:** 2026-06-30
**Current sprint:** Sprint 7 — Analytics (in progress)
**Previous sprint:** Sprint 6 — Man Status ✓ Complete

**Recent change (D032):** Six score-derived tiers now live. `score_to_tier()` in
`core/stats.py` is the single definition. `load_players()` derives CAREER_TIER on
every load — workbook column ignored. HOF badge mechanism added. See D032.

For decisions history see `DECISIONS.md`. For open bugs see `KNOWN_ISSUES.md`.

---

## What This App Is

Trail & Bish Dynasty is a premium Streamlit NFL-draft-rivalry application. Two friends
(Matt and Ryan) have run a fantasy draft for 20 years — 354 players, 20 draft classes
(2007–2026), one all-time rivalry. The app surfaces the history, stats, and stories of
that rivalry in a broadcast-quality sports experience. Every page has a locked identity
(SportsCenter, PFF, Hall of Fame Museum, etc.). Owner colors are permanent: Matt = Blue
`#2E7DF7`, Ryan = Red `#E63B3B`.

---

## Data Pipeline

```
NFL_Boys_-_The_OG.xlsx          ← Hand-kept source of truth (OG ledger)
        │ (manual scoring + award entry)
        ▼
AP_Dynasty_Backend.xlsx         ← Derived backend (app reads this)
  • players sheet: 354 rows × 19 cols — primary truth for all pages
  • man status sheet: 20 rows × 13 cols — Man Status picks
  • wildcard boys sheet: fun picks, separate scoring system
        │
        ▼
Trail & Bish Dynasty app (Streamlit)
```

Flow is **one-directional**: edits happen in the OG ledger, then the backend is updated.
The app never writes to the workbook. Scoring is LOCKED (see SCORING MODEL below).

---

## Scoring Model v1.0 (LOCKED)

Formula: `OVERALL SCORE = min(100, baseline + 0.6 × min(award_points, 16))`

Award weights: MVP 6, SB_MVP 4, OPOY/DPOY 3, ALL_PRO/SB Win 2.5, OROY/DROY 1.

The model is documented in the `SCORING_MODEL_v1` sheet inside `AP_Dynasty_Backend.xlsx`.
Rules are frozen. Only inputs change going forward (new awards, HOF, rings). See D030.

Man Status is on the same scale. Wildcards are intentionally on their own system.

---

## Page Completion

| Page | Status | Identity |
|---|---|---|
| Dashboard | ✓ Complete | SportsCenter |
| Players | ✓ Complete | PFF |
| Rankings | ✓ Complete | ESPN Stats |
| Draft War Room | ✓ Complete | NFL Front Office |
| Analytics | In progress | Bloomberg Terminal |
| Legacy Center | ✓ Complete | Hall of Fame Museum |
| Man Status | ✓ Complete | Sunday Night Football / UFC |

**Completion: 6 / 7 pages (86%)**

---

## Architecture Status

| Module | Status | Notes |
|---|---|---|
| `core/utils.py` | ✓ Production | `safe_int`, `safe_str`, `is_score_pending`, `fmt_score` |
| `core/stats.py` | ✓ Production | All cross-page stats + Man Status series aggregates |
| `core/components.py` | ✓ Production | 32+ components; `_fmt_score` wraps `fmt_score` from utils |
| `core/data_loader.py` | ✓ Production | 3 loaders: `load_players`, `load_man_status`, `load_wildcard` |
| `core/sidebar.py` | ✓ Production | CSS injection, nav, rivalry scoreboard, active page |
| `assets/theme.css` | ✓ Production | ~2150 lines |
| `pages/Dashboard.py` | ✓ Production | GOAT Race = top-3 teaser + link to Rankings |
| `pages/Players.py` | ✓ Production | Roster-scoped stat cards; Elite = teaser + link to Rankings |
| `pages/Rankings.py` | ✓ Production | Featured top-5 emphasis + THE FIELD divider; tie-aware cutoff |
| `pages/WarRoom.py` | ✓ Production | Class stats, series record, class deep dive |
| `pages/Legacy.py` | ✓ Production | 8 exhibits with working scroll anchors |
| `pages/ManStatus.py` | ✓ Production | Arena/fight-card identity — 20-bout fight card |
| `pages/Analytics.py` | In progress | Bloomberg Terminal identity — Sprint 7 |

---

## Build Order (Sprint Plan)

| Sprint | Focus | Status |
|---|---|---|
| 1 | Architecture, Infrastructure, Core Modules | ✓ Complete |
| 2 | Players page | ✓ Complete |
| 3 | Draft War Room | ✓ Complete |
| 4 | Rankings page | ✓ Complete |
| 5a | Data-layer migration (workbook → AP_Dynasty_Backend.xlsx) | ✓ Complete |
| 5b | Legacy Center | ✓ Complete · LOCKED |
| 6 | Man Status (flagship) | ✓ Complete |
| 7 | Analytics | In progress |
| 8 | Production Polish | Final |

---

## What's Next

**Sprint 7 (current):** Complete the Analytics page. The page shell exists
(`pages/Analytics.py`), but has two hardcoded strings that must be computed live
(KI-011, KI-012). The Bloomberg Terminal identity is defined in `docs/Analytics.md`.

**Queued feature: Draft-entry tool.** Pre-draft pick entry into the OG ledger.
Picks are made BEFORE the NFL draft each year (annual cadence). This is a new
dropdown/form tool that writes to the OG ledger — not part of the main app display.
Implementation TBD.

---

## Workbook Coverage

Backend: `backend/AP_Dynasty_Backend.xlsx` (3 sheets — Sprint 5 migration)

| Sheet | Loader | Page Consumer | Notes |
|---|---|---|---|
| `players` | `load_players()` | All pages except Man Status, Wildcard | 354 rows × 19 cols |
| `man status` | `load_man_status()` | `pages/ManStatus.py`, `pages/Analytics.py` | 20 rows × 13 cols; header at row 3 |
| `wildcard boys` | `load_wildcard()` | Not yet consumed | 11 cols; data from row 6 |

Display/engine sheets removed from workbook in Sprint 5. All features derive in-app from `players`.
