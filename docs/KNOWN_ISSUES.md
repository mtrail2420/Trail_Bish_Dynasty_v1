# Known Issues

Issues are categorized as Open or Resolved.
Severities: Critical / High / Medium / Low

---

## Open

---

### KI-R014 — Analytics.py: hardcoded SB Win / SB MVP counts and franchise ratio

**Resolved:** 2026-06-30 (D034)
**KIs closed:** KI-011, KI-012

SB Win and SB MVP counts now extracted live from `badge_rows_data`. Franchise ratio
now computed from `ryan_st['franchise'] / matt_st['franchise']` with division-by-zero
guard. Leader names computed dynamically. See D034(b).

---

### KI-R015 — stats.py: int(MARGIN) truncated decimal margins on Man Status cards

**Resolved:** 2026-06-30 (D034)
**KI closed:** KI-013

Changed `int(big_row["MARGIN"])` and `int(close_row["MARGIN"])` to
`round(float(...), 1)`. Verified: biggest_margin = 46.5, closest_margin = 8.0.
ManStatus.py display unchanged — f-string renders floats correctly. See D034(c).

---

### KI-014 — stats.py: class_grade() thresholds may need recalibration (post-rescale)

**Severity:** Low
**Affects:** Draft War Room page — class grade badges (S / A / B / C / D)
**Verified:** 2026-06-30
**Partial fix:** 2026-06-30 (D032) — docstring corrected; thresholds deferred.

The `class_grade()` docstring stale values (`71.0 / 56.5`) have been updated to
the correct post-rescale figures (`76.25 / 57.11`). The grade thresholds themselves
(≥68 = S, ≥60 = A, ≥52 = B, ≥44 = C, else D) may still be miscalibrated against
post-rescale class averages — recalibrating requires a product decision about what
percentage of classes should earn each grade.

**Remaining fix:** Decide S/A/B/C/D frequency targets, re-run thresholds against
live data, update `class_grade()` accordingly. Product decision, not just engineering.

---

### KI-007 — DT position group has only 4 players per owner (n < MIN_RANKED_SAMPLE)

**Severity:** Low
**Affects:** Rankings page — DT owner comparison

The DT position group has 8 total players (4 Matt, 4 Ryan). All 8 are scored.
With MIN_RANKED_SAMPLE=5, the comparison panel automatically shows `(n=4)` next
to DT averages, flagging the small-sample nature. Matt avg 38.5 vs Ryan avg 61.0
is a real gap, but readers should know it's based on 4 players each.

**Workaround:** Already handled — `(n=4)` caveat appears automatically.

**Resolution:** Will self-resolve as more DT players are drafted in future classes.

---

### KI-006 — 28 players with no OVERALL SCORE (2025–26 draft picks)

**Severity:** Low
**Affects:** All pages showing player scores

28 of 354 players have `NaN` OVERALL SCORE — all from the 2025–26 draft
classes. They are correctly displayed with a "TBD" badge instead of a score.
When filtering by Score ↓ / Score ↑, these players sort to the bottom (pandas
NaN sorting behavior with `na_position="last"`).

**Workaround:** Score pending badge implemented. `is_score_pending()` in
`core/utils.py` is the authoritative check.

**Resolution:** These scores will fill in naturally as players complete careers.
No code change needed — the TBD badge handles missing data gracefully.

---

## Resolved

### KI-R001 — @st.cache_data on pd.ExcelFile

**Resolved:** 2026-06-27
**Issue:** `load_workbook()` used `@st.cache_data` which requires pickle serialization.
`pd.ExcelFile` is not picklable — raised `RuntimeError` on every cache write.
**Fix:** Changed to `@st.cache_resource`. See Decision D001.

---

### KI-R002 — Wrong sheet names in data_loader.py

**Resolved:** 2026-06-27
**Issue:** `load_dashboard()` referenced `"Draft Dashboard"` (doesn't exist);
`load_players()` referenced `"Players"` (correct is `"players"` lowercase).
Both would raise `ValueError: Worksheet not found`.
**Fix:** Corrected to `"dashboard"` and `"players"`.

---

### KI-R003 — NaN scores causing ValueError in component rendering

**Resolved:** 2026-06-27
**Issue:** `min(int(score), 100)` raised `ValueError: cannot convert float NaN
to integer` when rendering the 28 un-scored players.
**Fix:** Added `_safe_score()` helper in `core/components.py` backed by
`is_score_pending()` from `core/utils.py`. All components now handle NaN safely.

---

### KI-R004 — CSS not applied after st.switch_page()

**Resolved:** 2026-06-27
**Issue:** CSS injected in `app.py` was lost after redirect because
`st.switch_page()` triggers a full browser page re-render.
**Fix:** Moved CSS injection into `render_sidebar()`. See Decision D003.

---

### KI-R005 — Dead CSS classes in theme.css

**Resolved:** 2026-06-28
**Issue:** `.landing-container`, `.landing-title`, `.landing-subtitle`,
`.landing-card` (~53 lines) existed in `theme.css` but were not referenced
by any Python component. Dead weight.
**Fix:** Removed from theme.css in Sprint 1 cleanup.

---

### KI-R006 — load_dashboard() dead code

**Resolved:** 2026-06-28
**Issue:** `load_dashboard()` existed in `data_loader.py` but was called by
no page. The `dashboard` sheet is stale (169 players vs actual 354).
**Fix:** Removed. See Decision D008.

---

### KI-R007 — Duplicate stats derivation in Dashboard and Players

**Resolved:** 2026-06-28
**Issue:** Both pages independently computed total players, franchise count,
avg scores, draft classes, best year, etc. Changing one stat definition
required updating two files.
**Fix:** All stats now computed via `core/stats.py`. See Decision D004.

---

### KI-R008 — import math mid-file in components.py

**Resolved:** 2026-06-28
**Issue:** `import math as _math` was placed at line ~194 of `components.py`,
after callout() and before award_badges(). `_safe_score()` was similarly
defined after components that called it at runtime.
**Fix:** All imports moved to top of file. Private helpers moved immediately
after imports in Sprint 1 restructure.

---

### KI-R009 — AP Rankings sheet required multi-section custom parser

**Resolved:** 2026-06-28 (Sprint 5 workbook migration)
**Issue:** The `AP Rankings` sheet was a non-tabular layout with 4+ sections,
repeated headers, and mixed data types. `load_rankings()` returned garbled data.
**Fix:** Sheet deleted from workbook. `load_rankings()` removed from data_loader.
Rankings page has always derived data from `players` via `rank_players()`. (D005)

---

### KI-R010 — man status picks sheet was 702 columns wide

**Resolved:** 2026-06-28 (Sprint 5 workbook migration)
**Issue:** The `man status picks` sheet used a horizontal year-by-year layout
across 702 columns. No usable parser existed.
**Fix:** Workbook replaced. New `man status` sheet is a clean 13-column table
(YEAR, MATT_PICK, MATT_POS, MATT_SCORE, MATT_RESUME, RYAN_PICK, RYAN_POS,
RYAN_SCORE, RYAN_RESUME, WINNER, MARGIN, MATT_NOTES, RYAN_NOTES) with a 3-row
title block. `load_man_status()` added to data_loader with `header=3`.

---

### KI-R011 — Legacy Center / Draft War Room / Player Rankings sheets non-tabular

**Resolved:** 2026-06-28 (Sprint 5 workbook migration)
**Issue:** These three sheets were human-readable reporting layouts returning
garbled data when parsed directly.
**Fix:** All three sheets deleted from workbook. Their loaders (`load_legacy`,
`load_war_room`, `load_player_rankings`) removed from data_loader. Pages derive
all data from `players` via `core/stats.py`. (D002, D005, D010)

---

### KI-R012 — _ENGINE_OUTPUT was empty; _ENGINE sheets stale

**Resolved:** 2026-06-28 (Sprint 5 workbook migration)
**Issue:** `_ENGINE` and `_ENGINE_OUTPUT` sheets existed but the engine had
never run. `_ENGINE_OUTPUT` contained 0 rows.
**Fix:** Both sheets deleted. All ranks and scores derive from `players["OVERALL SCORE"]`
via `rank_players()`. No change needed to page logic.

---

### KI-R013 — Hall of Fame / Mount Rushmore / All-Franchise sheets were empty

**Resolved:** 2026-06-28 (Sprint 5 workbook migration)
**Issue:** These three legacy sheets had framework structure but zero player data.
**Fix:** All three sheets deleted. Per product decision, these features now derive
in-app from `players` (Franchise tier players, top scores by owner/position).
`core/stats.py` is the correct home for the algorithmic HOF / Rushmore criteria.
