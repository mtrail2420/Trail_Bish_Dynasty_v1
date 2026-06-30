Rankings — Page Specification
Identity: ESPN Stats — the definitive dynasty leaderboard.
Experience tier: ★★★☆☆
The question it answers: Who is the best?
This page is the authoritative ranking surface for the whole dynasty. It is about objective standing — who ranks where, by player, by owner, by position. It is not about why (that's Analytics) and not about head-to-head drama (that's Man Status).
---
Purpose
Give a clear, scannable, authoritative answer to "who's best" at every level:
Best players overall
Best players at each position
How the two owners stack up across positions
Everything derives live from the `players` sheet. No hardcoded ranks or names.
---
Must Have
Hero header — ESPN Stats identity, with a live-data subtitle (e.g. total players ranked, leaders).
Top stat row — a few `stat_card`s framing the leaderboard (e.g. #1 overall player, highest-rated owner avg, number of Franchise-tier players).
Overall Top Players leaderboard — ranked list using `player_row` / `player_table`, owner-colored, with score bars, tier badges, and position chips. This is the spine of the page.
Position Leaderboards (signature feature) — tabbed or scrollable position groups (QB, RB, WR, TE, OL, EDGE, DT, LB, DB), each showing the top 5 at that position with owner-colored rankings, pulling from `rank_players_by_position()`.
Owner-vs-owner position comparison — reuse `comparison_panel` + `rivalry_stat_row` to show, per position, how Matt and Ryan compare (e.g. avg score or top-player score at each position), with the per-row winner highlighted.
---
Must Never
Never become Analytics. No heatmaps, trend explanations, or "why" narratives.
Never become Man Status. No fight-card framing, momentum, or smack talk.
Never become Players. It ranks; it does not host a full search/filter/profile explorer.
Never use `st.dataframe` or any default Streamlit table. Rankings render through `player_row` / `player_table` and the comparison components.
Never hardcode ranks, names, or counts.
---
Data & Logic
Source: `players` sheet (live), via `core/data_loader.load_players()`.
Ranking: `core/stats.rank_players()` and `core/stats.rank_players_by_position()` — these already exist; no new stats functions should be needed.
Grades, if shown, come from the stats layer (e.g. `grade_badge`), never computed inline in the page.
Small class / small sample handling: when ranking by averages at the position or owner level, guard against misleading outliers from tiny samples (the 2008 class has only 2 picks). Either show the sample size next to the number, or apply a minimum-sample rule defined in the stats layer — not ad hoc in the page.
---
Components To Reuse
`page_header`, `section_header`, `stat_card`, `player_row`, `player_table`, `tier_badge`, `position_chip`, `owner_chip`, `comparison_panel`, `rivalry_stat_row`, `grade_badge`.
If a new repeated pattern appears (e.g. a position-tab control), extract it into `core/components.py` rather than leaving page-specific HTML.
---
Interactions
Position group selection: tabs or a selectbox switches the active position leaderboard with no full-page jank.
Hover states on ranked rows (lift/glow), consistent with the rest of the app.
Pending-score players (28 currently) are handled gracefully — shown as pending, never as a 0 that distorts ranking.
---
Acceptance Criteria
[ ] Identity reads unmistakably as "ESPN Stats" — clean, authoritative, leaderboard-first.
[ ] Overall leaderboard renders via `player_row` / `player_table`, owner-colored, with score bars.
[ ] Every position group (QB, RB, WR, TE, OL, EDGE, DT, LB, DB) has a top-5 leaderboard.
[ ] Owner-vs-owner position comparison uses `comparison_panel` + `rivalry_stat_row` with winners highlighted.
[ ] All data is live from `players`; nothing hardcoded.
[ ] No default Streamlit widgets for data display.
[ ] Small-sample averages don't produce misleading outliers.
[ ] Matt = Blue, Ryan = Red, never swapped.
[ ] Passes the final test: would ESPN ship this leaderboard?