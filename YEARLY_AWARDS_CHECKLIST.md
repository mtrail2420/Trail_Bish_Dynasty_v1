# Yearly Awards Update — Checklist

Run after the season concludes (awards are final ~February). Awards must match
across the players sheet and Man Status. Wildcard doesn't need award syncing
(guys overlap there), but its notes should reflect the season.

## Steps

1. **Update award columns** in `backend/AP_Dynasty_Backend.xlsx` (players sheet):
   MVP, SB_MVP, OPOY, DPOY, ALL_PRO, SB Win, OROY, DROY.
   - Do NOT hand-edit OVERALL SCORE — it recalculates automatically from the
     frozen baselines (`score_baseline_snapshot.json`) on every app load.
   - Clipboard rings (player was on the roster but not a starter): record the
     ring in SB Win but note it as clipboard in NOTES. v1 scores all rings;
     the v2.1 model in the React app zeroes clipboard rings.
2. **Mirror the players sheet** to the root `AP_Dynasty_Backend.xlsx`
   (same edits, both copies stay identical).
3. **Man Status scrutiny** — this is THE boy-of-boys page, give it the most care:
   - Bout scores, margins, and winners now sync automatically from the player
     scores in code (`_sync_man_status_scores`), so no hand math needed.
   - But REVIEW the page: if any bout winner flipped on new awards, that's a
     real rivalry event — confirm it's right before it goes live.
   - Update MATT_RESUME / RYAN_RESUME and MATT_NOTES / RYAN_NOTES to reflect
     new awards.
4. **Wildcard notes** should be reflective of the season — update NOTES where
   a player's year changed the story. Scores there are editorial; awards don't
   need syncing.
5. **Run the audit**: `python3 verify_scores.py` — must PASS (exit 0).
   It checks baseline drift, note/ring consistency, score bounds, pending
   count, and that every Man Status pick name matches a player row.
6. **Regenerate the premium workbook**: `python3 make_premium.py`
7. **Push**: text files via the normal file API; the two `.xlsx` workbooks via
   the GitHub web uploader (the file API corrupts binaries — never push
   workbooks through it).

## Standing rules (don't break these)

- v1 scoring formula is LOCKED (SCORING_MODEL_v1 sheet, 2026-06-29).
  Baselines in `score_baseline_snapshot.json` NEVER change.
- Never name the draft board's authors — "the draft board" / "the board".
- Pick-order history: only what's recorded. 2026: Matt went first.
  2027: Ryan goes first. 2007–2025: not recorded — never fabricate.
