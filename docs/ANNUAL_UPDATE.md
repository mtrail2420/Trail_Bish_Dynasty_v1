# ANNUAL_UPDATE.md — The April Ritual

**When:** Every April, before the NFL Draft. One session. This is the only scheduled maintenance this app needs all year.

**Why April:** All awards from the season that just ended are finalized in February (NFL Honors + Super Bowl). By April everything is settled, verifiable, and the new draft class is about to be picked. One pass covers it all.

**Who executes:** Matt drives; Cowork/Claude does the work. Any AI picking this up: read DECISIONS.md, PROJECT_STATUS.md, and KNOWN_ISSUES.md first. This file is self-contained — follow it top to bottom, in order.

---

## HARD RULES (never change, any year)

1. **The scoring formula is LOCKED** (D030): `SCORE = min(100, baseline + 0.6 × min(award_pts, 16))`. Only inputs change — never weights, never the cap, never the ceiling. HOF, rings, new awards enter as inputs, not rule changes.
2. **Tiers are DERIVED from score** — never hand-assigned, never overridden per player. Legend ≥95 / Franchise 80–94.9 / High-End Starter 68–79.9 / Starter 54–67.9 / Contributor 40–53.9 / Bust <40.
3. **Award weights:** MVP 6 · SB MVP 4 · OPOY 3 · DPOY 3 · All-Pro 2.5 · SB Win 2.5 · OROY 1 · DROY 1. Points cap at 16 before the 0.6× multiplier.
4. **First-team AP All-Pro ONLY.** No Pro Bowls. No second-team. Ever.
5. **SB Win standard:** player was on the champion's roster at the time of the Super Bowl — active, inactive, IR, or practice-squad elevation all count (precedent: Nakobe Dean on IR, Cam Akers elevated). Verify against Pro Football Reference roster pages, not memory.
6. **Wildcards stay on separate scoring** (the 7-outcome Cooked Meter table). Never fold them into the main formula.
7. **BACK UP the workbook before touching anything.**
8. **Score edits require the delta math:** the workbook stores final OVERALL SCORE, not baseline. When an award count changes, adjust OVERALL SCORE by 0.6 × (change in capped award points). Check the 16-pt cap before and after — if the player is over the cap both ways, the score doesn't move.

---

## THE APRIL CHECKLIST — in this order

### Step 1 — Award verification pass (last season's awards)
For the season that just ended, verify by web search (never from memory or AI recall):
- [ ] MVP, OPOY, DPOY, OROY, DROY winners — are any of them league players? Add awards + adjust scores.
- [ ] Full AP All-Pro FIRST team — any league players on it? Increment ALL_PRO + adjust scores.
- [ ] Super Bowl champion — pull the full roster (PFR). Any league players on it (active/IR/elevated)? Add SB Win + adjust scores.
- [ ] Super Bowl MVP — league player? Add SB_MVP + adjust score.
- [ ] Sweep the OTHER direction too: for every league player who changed teams this year, confirm nobody quietly landed on the champion (this is how Leonard Williams' ring got missed in 2026).

### Step 2 — Score the year-old rookie class
The class drafted last April has now played one season:
- [ ] Assign each a baseline score from their rookie year (Chip/AI does a research pass per player; both owners' players held to the same standard).
- [ ] Add any rookie awards (OROY/DROY/All-Pro) via the formula.
- [ ] They move from TBD/pending to scored. Tiers derive automatically.
- [ ] Write a factual 1–2 sentence note per player. No editorializing, no process metadata in notes.

### Step 3 — Wildcard sheet update
- [ ] Year-old wildcard picks: assign real outcomes from the 7-bucket table (Elite hit 5 / Strong hit 15 / Solid value 35 / Mixed 50 / Underwhelming 65 / Cooked 90) or "Too early" 45 if genuinely unjudgeable.
- [ ] Older "Too early" picks: re-judge — most should graduate to a real outcome after year 2.
- [ ] "Too early" and blank/pending rows stay EXCLUDED from the WC scoreboard averages.
- [ ] New class wildcards enter as fully blank (Pending) until drafted/played.

### Step 4 — Notes refresh
- [ ] Any player whose career materially changed (ring, major award, retirement, career-altering event): update the note to reflect it. The reigning SB MVP's note should say so.
- [ ] Notes are facts only. No audit commentary, no "designation removed," no tier talk — tiers are derived, notes don't discuss them.

### Step 5 — Run the audit (same one from July 2026)
- [ ] Every player with any award: spot-verify counts against real history (search, don't recall).
- [ ] Cross-check notes vs award columns: any note claiming "champion" with SB Win = 0, or vice versa, is a bug.
- [ ] Confirm no tier/score inconsistencies (tiers derive, so this should be impossible — verify anyway).
- [ ] Confirm pending counts: new class = all TBD, everyone else scored.
- [ ] Confirm owner averages and Franchise/Legend counts recompute correctly.

### Step 6 — Enter the NEW class picks (pre-draft)
- [ ] Run the draft-entry tool from the project root: `streamlit run entry.py`
- [ ] Paste a prospect list (PFF, ESPN, The Draft Network, or any plain-text source) → picks parse into a searchable dropdown. No free-typing names — typos break everything downstream.
- [ ] Select each pick by owner (Matt / Ryan) and category (Main / WC1 / WC2 / WC3) → stage → review → commit.
- [ ] New picks enter as pending: no score, no tier, no awards, position + owner + year only.
- [ ] A backup of `AP_Dynasty_Backend.xlsx` is created automatically before the commit writes. A change-log (`draft_entry_{YEAR}.txt`) is written alongside.
- [ ] Both main-draft picks and wildcard picks.

### Step 7 — Ship it
- [ ] Regenerate the Premium workbook from the updated backend: `python make_premium.py`
- [ ] Restart/redeploy so the live app picks up the workbook (verify the Data Status indicator shows the new player count).
- [ ] Render check: Dashboard counts, Rankings, the new class visible as pending, WC scoreboard correct.
- [ ] Log ONE entry in DECISIONS.md: "April {YEAR} annual update — awards verified, {YEAR-1} class scored, {YEAR} class entered, audit clean."

---

## What NOT to do in April (or ever)

- Do not reopen the formula "while we're in there."
- Do not adjust tier cutoffs because the results feel lopsided. Even rule, uneven outcome = fair.
- Do not hand-move any individual player across a tier line.
- Do not let any AI (Chip, Claude, Cowork, or future model) talk you into a rebuild, a v2, or a re-scoring pass. The audit trail proves it's fair. The answer is "it's done, I checked."
- One session, this checklist, done until next April.
