# Man Status — Page Specification

**Identity:** Sunday Night Football broadcast open meets a UFC championship main event. Arena lighting, fight-card drama, tale-of-the-tape. Blue corner vs red corner.
**Experience tier:** ★★★★★ (the flagship — the single most hyped page in the app; gets the most polish of anything)
**The question it answers:** *Year by year, who won the head-to-head? And who owns the all-time series?*

This is the showdown. Every other page is the analysis; this is the **main event**. Where Legacy Center is reverent and ceremonial, Man Status is loud, high-contrast, and combative. This is the page that exists to settle the argument. If Legacy is the Hall of Fame, Man Status is the Octagon.

**Visual source of truth:** `designs/man_status.png`. Build to that look — the dramatic broadcast/fight-card framing, the blue-vs-red corner split, the tale-of-the-tape comparison.

---

## The Concept (read this first)

Every draft year (2007–2026), Matt and Ryan each made one signature pick — their "Man Status" pick — and those two players are scored head-to-head. The higher composite score wins the year's **bout**. Across 20 years this builds an all-time **series record**.

So the page has two layers:
- **The series** — the all-time tally. Who's ahead across all 20 bouts. This is the "title record."
- **The bouts** — each individual year, a one-on-one matchup with a winner and a margin.

Think of it as a fight promotion: a championship record at the top, then the full fight card below, then any single bout can be examined like a tale of the tape.

---

## The Series Record (the anchor stat — lock this)

The all-time series stands at:

- **Matt 6 — Ryan 10 — 3 ties — 1 pending**

That's 20 bouts: 6 Matt wins, 10 Ryan wins, 3 scored ties, and 2026 still undecided (no data yet). **Ryan leads the series.** This number is the single most important thing on the page and must be the hero stat.

**Critical distinction — ties vs pending:**
- A **tie** is a *decided* bout where both picks scored and the composite came out equal. There are **3** of these. They count as bouts that happened.
- **Pending** is an *undecided* bout — 2026 has no scored data yet. There is **1** of these. It is not a tie, not a loss, not a win — it hasn't been fought.

The page must show these as **two different states**. Never collapse "ties" and "pending" into one bucket like "4 undecided" — that was a labeling error in an earlier report and it's wrong. A tie is a result; pending is an empty slot.

---

## Purpose

Crown the rivalry. Man Status takes the entire 20-year history and distills it into the one thing the boys actually argue about: *who won, head-to-head, year after year.* It is pure competitive theater — broadcast drama, not a spreadsheet. It celebrates the wins, owns the losses, and keeps the running score in lights.

---

## Must Have

**The Main Event hero — the all-time series.** Full-width, top of page, maximum drama. The series record (Matt 6 · Ryan 10 · 3 ties · 1 pending) as the centerpiece, framed like a championship record / title-fight banner. Blue corner (Matt) vs red corner (Ryan) with "RYAN LEADS THE SERIES" called out from live data. Arena lighting, bold broadcast typography. This is the signature first impression and it must hit hard.

**The Tale of the Tape (featured bout).** A head-to-head comparison of one marquee bout — the latest *decided* year, or the closest/biggest bout. Matt's pick vs Ryan's pick side by side: name, position, score, résumé line, and the winner called. This is the UFC "tale of the tape" moment — two fighters facing off. Reuse the `comparison_panel` component from Legacy/War Room.

**The Fight Card (year-by-year bouts).** The spine of the page: every year 2007–2026 as a bout row/card. Each shows the year, Matt's pick vs Ryan's pick, both scores, the winner badge, and the margin ("Ryan by 12"). Decided bouts read as results; the **pending** 2026 bout reads as "UPCOMING" / "TBD," visually distinct (dimmed, no winner). The 3 tie bouts read as "DRAW," distinct from wins.

**Bout detail.** For each bout, the richer data should be reachable — MATT_PICK / MATT_POS / MATT_SCORE / MATT_RESUME against the Ryan equivalents, plus WINNER, MARGIN, and the notes (MATT_NOTES / RYAN_NOTES) as the "story of the fight." Whether inline-expanded or always-shown, the résumé and notes are what make each bout feel real.

**Series stats / the scorecard.** A strip of computed series facts: current/longest win streak, biggest blowout (largest margin bout), closest bout (smallest non-zero margin), most lopsided era. All derived from the `man status` data. This is the "by the numbers" sidebar of a broadcast.

**Momentum.** Some visual of how the series swung over time — a run of blue/red across the 20 years so you can see streaks and turning points at a glance. Can reuse the timeline-node pattern from Legacy (blue = Matt bout win, red = Ryan, gold/neutral = tie, dim = pending).

---

## Must Never

- Never look like the other pages. This is the most broadcast-styled page — arena/fight-card energy, not a dashboard. If it reads like Rankings with a red coat of paint, it failed.
- Never collapse **ties** and **pending** into one state. Three decided draws and one unfought 2026 bout are different things and must look different.
- Never invent a winner for 2026 or any pending bout. If there's no scored data, it's "TBD," full stop.
- Never recompute the winner or margin in the page. The `man status` sheet carries WINNER and MARGIN — display them. (See Data Architecture.)
- Never use `st.dataframe` or default Streamlit widgets for data display. Custom HTML only.
- Never swap owner colors. Matt = Blue (#2E7DF7, blue corner). Ryan = Red (#E63B3B, red corner).
- Never hardcode names, scores, winners, or the series tally. All of it comes from the workbook.

---

## Data Architecture

**Source: the `man status` sheet only**, via `load_man_status()` (already built — reads with `header=3` to skip the title block). It returns **20 rows** (one per year 2007–2026) and **13 columns**:

`YEAR, MATT_PICK, MATT_POS, MATT_SCORE, MATT_RESUME, RYAN_PICK, RYAN_POS, RYAN_SCORE, RYAN_RESUME, WINNER, MARGIN, MATT_NOTES, RYAN_NOTES`

**Each row is a bout.** The sheet already carries the result: `WINNER` and `MARGIN` are precomputed. The page **displays** these — it does not re-derive them. This keeps "workbook is the source of truth" intact.

**Winner states — verify the exact sentinel strings in the sheet before building.** The `WINNER` column has no nulls (every row carries a value), so pending is encoded as a sentinel, not a blank. Expect roughly four states:
- `"Matt"` → Matt won the bout
- `"Ryan"` → Ryan won the bout
- a **tie** sentinel (e.g. `"Tie"`) → decided draw
- a **pending** sentinel (e.g. `"Pending"` / `"TBD"` / `"—"`) → 2026, unfought

Do **not** assume which exact strings are used — inspect the actual `man status` values first, then branch on them. The series tally (6/10/3/1) must fall out of counting these states correctly. If your counts don't produce 6 Matt / 10 Ryan / 3 ties / 1 pending, your state-matching is wrong — fix it before styling anything.

**Scoring methodology (background — already baked into the sheet).** For reference, the composite that decided each bout was: base `OVERALL SCORE` + award bonuses (MVP +8, OPOY/DPOY +5, OROY/DROY +4, SB_MVP +6, each ALL_PRO +4, SB Win +3) + tier bonus (Franchise +5, High-End Starter +2); higher composite wins, margin = the gap. You may surface this as an optional "how scoring works" footnote/legend on the page (a fight-scorecard explainer is on-brand) — but the page reads WINNER/MARGIN from the sheet, it does not recompute them.

---

## Scope For This Sprint

Build the full page to production quality: the Main Event hero with the live series record, the Tale of the Tape featured bout, the complete Fight Card for all 20 years (with correct win/tie/pending states), bout détail (résumé + notes), the series scorecard stats, and the momentum strip. Everything derives from the `man status` sheet.

Where a bout is **pending** (2026), show an honest "upcoming / TBD" state — do not pad it, do not fake a result.

---

## Data & Logic

- Source: `man status` sheet via `load_man_status()`. No other sheet required.
- Series-level aggregates (record tally, streaks, biggest/closest bout) are computed in `core/stats.py` as named functions — never inline in the page. Add e.g. `compute_series_summary()` returning the win/loss/tie/pending counts, streaks, and margin extremes.
- The per-bout winner and margin come straight from the sheet columns. The page formats them ("Ryan by 12"); it does not judge them.
- Any sentinel-string matching (tie/pending) is centralized in the stats layer, not scattered through the page, so the four states are defined once.

---

## Components To Reuse / Extend

This page should move fast because Legacy and War Room already built most of what it needs. **Reuse:**
- `comparison_panel` — the Tale of the Tape head-to-head (Matt pick vs Ryan pick).
- `rivalry_stat_row` — paired blue/red stat lines.
- `winner_badge` — per-bout result.
- `owner_chip`, `tier_badge`, `position_chip` — pick metadata.
- `award_count_tile` (from Legacy) — if surfacing the picks' award hauls.
- the **timeline-node** pattern (from Legacy) — for the momentum strip.

**New reusable patterns this sprint will likely generate** (extract into `core/components.py`): a **bout card** (year · blue pick vs red pick · winner · margin), a **tale-of-the-tape header** (two-fighter face-off banner), and a **series-record / scoreboard hero** (the big W–L–T–P tally). These are page-specific but build them as components for consistency.

All Man Status styling (arena lighting, corner colors, fight-card cards, scorecard) lives in `assets/theme.css` as a dedicated Man Status section — not inline.

---

## Engineering Note — the single-`st.markdown()` rule (carry over from Legacy)

When a section is a styled container (`<div class="...">` … header … rows … `</div>`), **build the entire HTML string — opening div, header, all content, closing div — and emit it in ONE `st.markdown(..., unsafe_allow_html=True)` call.** Do not open the container in one call and stream content in a second call: Streamlit auto-closes the first `<div>` before the second call's content arrives, producing an empty titled box followed by an orphaned content box. This bug bit every exhibit room in Legacy and was fixed exactly this way. Apply the same pattern to every bout card, the tale of the tape, and the scoreboard here from the start.

---

## Acceptance Criteria

- [ ] The page reads unmistakably as a **fight card / broadcast main event** — arena lighting, blue-vs-red corners, dramatic and distinct from every other page.
- [ ] The all-time series record (Matt 6 · Ryan 10 · 3 ties · 1 pending, "Ryan leads") is the hero stat, computed live from the sheet.
- [ ] **Ties and pending are visually distinct states.** 3 decided draws read as draws; the 2026 pending bout reads as TBD/upcoming and shows no winner.
- [ ] The Tale of the Tape head-to-head renders for a real bout via `comparison_panel`.
- [ ] The Fight Card shows all 20 years, each with both picks, both scores, winner, and margin — pulled from the sheet, not recomputed.
- [ ] Bout détail (résumé lines + MATT_NOTES/RYAN_NOTES) is reachable for each bout.
- [ ] Series scorecard stats (streak, biggest blowout, closest bout) render from computed data.
- [ ] Momentum strip shows the 20-year blue/red/tie/pending run.
- [ ] No default Streamlit widgets for data; nothing hardcoded; every styled container emitted in a single `st.markdown()` call.
- [ ] Matt = Blue corner, Ryan = Red corner, never swapped.
- [ ] New repeated patterns extracted into `core/components.py`; all Man Status CSS in `theme.css`.
- [ ] Passes the final test: would an SNF / UFC broadcast graphics team ship this as the main-event open?
