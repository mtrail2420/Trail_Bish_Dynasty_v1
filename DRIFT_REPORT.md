# DRIFT REPORT — Trail_Bish_Dynasty_v1 repo vs React app canonical data

Generated 2026-10-15. Compares the v1 Streamlit repo workbook
(`backend/AP_Dynasty_Backend.xlsx`, after the 4 award fixes applied today)
against the React app's canonical data
(`~/workspace/dynasty-rebuild/source/AP_Dynasty_Backend.xlsx` and
`data/players.json`, `data/man_status.json`, `data/wildcard.json`).

The v2.1 clipboard-ring rule is EXCLUDED from this report (known, approved).

## 1. Player pool — identical

354 players in both. Zero name-level diffs in either direction
(v1 repo = canonical Excel = canonical JSON).

## 2. Award input columns — 6 genuine drifts (all: canonical is ahead)

Verified cell-by-cell after today's 4 fixes (Bates ALL_PRO already 0,
Fuller ALL_PRO already 1, Akers SB Win 2→1, Jackson SB Win 0→1 — all now
match canonical inputs). Remaining disagreements, v1 vs canonical:

| Player | Column | v1 repo | Canonical | Note |
|---|---|---|---|---|
| RG III | OROY | 0 | 1 | Won OROY 2012; v1 missing |
| Obi Melifonwu | SB Win | 0 | 1 | Ring recorded in canonical (clipboard, scores 0 there) |
| Ceedee Lamb | ALL_PRO | 0 | 1 | 2023 first-team All-Pro; v1 missing |
| Ja'marr Chase | OROY | 0 | 1 | Won OROY 2021; v1 missing |
| Ja'marr Chase | ALL_PRO | 0 | 2 | First-team 2021 + 2024; v1 missing |
| Christian Haynes | SB Win | 0 | 1 | Ring recorded in canonical (clipboard, scores 0 there) |

Every drift is v1 *missing* an award the canonical data has. The canonical
values passed the 2026-10-15 award verification (Wikipedia/PFR). Fixing
these in v1 would raise those players' v1 scores via the award formula —
left for Matt's call, not changed here.

## 3. Man Status — scores differ by design; 3 winner flips

20 bouts in both, same years, same picks (one spelling fix in canonical:
2026 "Jeremiah Love" → "Jeremiyah Love"). Bout SCORES differ in every
bout — expected, different scoring models (see §7). Winner flips
(model-driven, not data errors):

| Year | v1 repo winner | Canonical winner |
|---|---|---|
| 2014 | Tie (42–42) | Matt (37–34) |
| 2020 | Matt (58.0–34.6) | Ryan (44–39) |
| 2024 | Tie (60–60) | Matt (33–28) |

Resume wording conventions also differ (v1: "All-Pro, Franchise";
canonical: "First-Team All-Pro", "SB×2 (clipboard — not scored)").
2026 bout is Pending in both.

## 4. Wildcard — same 78 entries, editorial drift

78 entries both sides. 7 name spellings corrected in canonical
(v1 → canonical): Bryon Jones → Byron Jones, Christian Hackenburg →
Christian Hackenberg, Damien Porter → Darien Porter, Emeka Ubuka →
Emeka Egbuka, Jaylen Hyatt → Jalin Hyatt, Nick Hundley → Brett Hundley
(v1's "Nick Hundley" is a baseball catcher — canonical note says so),
Quentin Johnson → Quentin Johnston. 28 of 78 OUTCOME assessments differ
(e.g. Paxton Lynch: v1 "Underwhelming" vs canonical "Cooked"; DeForest
Buckner: v1 "Strong hit" vs canonical "Elite hit"). Full list available
on request — these are editorial judgments, not data errors.

## 5. 2026 class (in progress) — same meaning, different sentinel

v1 repo: 28 players, OVERALL SCORE = NaN (pending, unscored).
Canonical: 28 players, OVERALL SCORE = 0 (unscored).
Same 28 names. Both treat the class as unscored; only the sentinel
differs (NaN vs 0).

## 6. Structural differences

Sheets: v1 repo has `players`, `man status`, `wildcard boys`,
`SCORING_MODEL_v1`. Canonical Excel adds a `QB_Stats` sheet (40 QBs,
career passing stats — feeds the React QB Room).

Columns: canonical `players` adds `JEWELRY_ORIG`, `JEWELRY_PTS`,
`PS_RING` (v2.1 ring-rule bookkeeping). v1 repo has
`CHAMPIONSHIP_IMPACT` / `PRODUCTION` / `LONGEVITY` columns that the
canonical JSON does not carry (v1's baseline inputs; the React app
dropped them). Canonical JSON adds `PEAK_GRADE`, `PEAK_PTS`,
`MOTOR_PTS`, `HARDWARE_PTS`, `QUALITY_SEASONS`, `BAG_CHECK`, `RECEIPT`
(v2 component breakdown).

## 7. v1-vs-v2 model difference (why scores differ by design)

v1: OVERALL = hand-calibrated baseline + 0.6 × min(16, raw award pts),
ceiling 100. Awards are a small bonus on top of a production baseline.
v2: OVERALL = PEAK (50) + MOTOR (20) + HARDWARE (20) + JEWELRY (10) —
four scored components, no hand baseline; young/unproven players score
much lower until they produce.

Mean absolute score gap across 326 scored players: 22.9 pts. 10 largest
(v1 minus canonical):

| Player | v1 | Canonical | Δ |
|---|---|---|---|
| Sony Michel | 73.0 | 27 | +46.0 |
| Christian Haynes | 54.0 | 14 | +40.0 |
| Jonathon Brooks | 46.0 | 6 | +40.0 |
| Abdul Carter | 68.0 | 30 | +38.0 |
| Ashton Jeanty | 68.0 | 30 | +38.0 |
| Joshua Uche | 64.0 | 27 | +37.0 |
| Caden Sterns | 54.0 | 17 | +37.0 |
| MarShawn Lloyd | 46.0 | 9 | +37.0 |
| Shavon Revel | 54.0 | 18 | +36.0 |
| Luther Burden | 54.0 | 18 | +36.0 |

Pattern: v1's hand baselines were generous to young/role players; v2
withholds points until production exists. Direction is one-sided —
v1 scores higher in all 10.

## Appendix: repo-internal notes (2026-10-15 session)

- Root `AP_Dynasty_Backend.xlsx` (unreferenced by any code — the app
  reads `backend/`) already contained 3 of the 4 award fixes plus ~25
  additional `[PFR correction]` edits (SB Win/OROY/ALL_PRO additions)
  that were never ported to `backend/`. Only the 4 in-scope fixes were
  synced; the rest are out of scope for this task.
- `Trail_Bish_Dynasty_Premium.xlsx` is generated output — regenerated
  via `make_premium.py` after the fixes (354 rows verified).
- New: `recompute_overall_score()` in `core/stats.py`, wired into
  `load_players()` — OVERALL SCORE now recalculates from award inputs
  at load time on every page. Verified exact identity on all 326 scored
  players before the fixes.
