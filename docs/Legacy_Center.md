# Legacy Center — Page Specification

**Identity:** Hall of Fame museum. Black marble, gold trim, trophy-room lighting, ceremony.
**Experience tier:** ★★★★★ (one of the two flagship pages — gets the most polish)
**The question it answers:** *What history matters? Who will be remembered?*

This is the soul of the application. Anyone can build a player database; nobody builds a dynasty museum. This is the page people show their friends. It must feel **completely different** from the rest of the app — not another dark dashboard, but a place you walk into — while sharing the same chrome (sidebar, fonts, owner colors).

**Visual source of truth:** `designs/legacy_center_lobby.png` and `designs/legacy_center_entrance.png`. These are two halves of one page, not competing designs — see "The Merge" below.

---

## The Merge (read this first)

The two renders represent one experience in two states:

- **`legacy_center_entrance.png`** is the **welcome hall / landing state** — cinematic, torch-lit, the Lombardi trophy in a glass case on a pedestal, the two dynasty banners (MATT / RYAN) flanking the hall, "WELCOME TO THE LEGACY CENTER — Where Boys Become Legends," and "Explore the Legacy" below. This is the ceremony.
- **`legacy_center_lobby.png`** is the **populated state** — the same museum, with the live data panels filled in: GOAT Race leaders, Dynasty Awards leaders, Greatest Draft Classes, Legacy Spotlight, and the horizontal Dynasty Timeline.

**Build them as one page:** a museum lobby that is both immediately useful (data visible) and explorable (exhibit rooms you enter). The hero welcome hall sits at the top; the live data panels populate below it; the exhibit cards act as navigation into individual rooms.

---

## Purpose

Celebrate careers, accomplishments, and history with ceremony. Legacy Center is about *prestige and storytelling*, not analysis. It tells you who the legends are and lets you walk through the dynasty's history.

It computes from the `players` sheet (and related legacy sheets where populated), exactly like the pages already built — no special parser required.

---

## Must Have

**Hero — the Welcome Hall.** Full-width museum hall at the top: the central trophy on its pedestal/in glass, the two dynasty banners (MATT EST. 2007 / RYAN EST. 2007 with championship counts), the "Legacy Center — Where Boys Become Legends" title, and an "Explore the Legacy" cue leading the eye down to the exhibits. Black-and-gold, dramatic lighting. This is the signature first impression.

**The Rivalry panel (top-right).** Matt vs Ryan, blue vs red, the overall scores, "Ryan Leads" (from live data), and a win-split bar. This is the anchor that ties Legacy back to the rivalry. Consistent across both renders — keep it.

**Dynasty at a Glance.** A compact stat strip: Total Players, Draft Classes, Franchise Players, Hall of Famers, Busts. Live from the workbook.

**Recent Legacy Moments.** A dated feed of milestone events (e.g. "added to Mount Rushmore," "climbs to #2 all-time," "wins Defensive Player of the Dynasty"), owner-tagged. ESPN-news styling, museum-skinned.

**The Exhibit Cards (signature feature).** A row of exhibit entrances, each its own "room": **GOAT Race, Mount Rushmore, Record Book, Legacy Hall, All-Franchise, Timeline, Hall of Shame.** Each card has its own icon/imagery and an "ENTER ROOM →" / "VIEW EXHIBIT" affordance (see `legacy_center_entrance.png` lower rows — the goat statue, the Rushmore busts, the leather record book, the trophy hall, the jersey wall, the red-lit Hall of Shame). These are navigation, not just decoration.

**Live data panels (the populated lobby).** Below the exhibits: **GOAT Race Leaders** (top all-time legacy scores with owner-colored bars), **Dynasty Awards Leaders** (the trophy grid — MVP, AP OPOY, Pro Bowl, 1st-Team All-Pro, SB Champ, etc.), **Greatest Draft Classes** (top 5 all-time with grades), **Legacy Spotlight** (a featured player card). All live from the workbook.

**Dynasty Timeline.** A horizontal timeline across the bottom marking era highlights by year ("The Beginning 2007," "Ryan's Breakout," "Historic Class," etc.).

---

## Must Never

- Never look like the rest of the app. The dark-navy dashboard theme is replaced here by black-marble-and-gold museum styling. If it looks like Analytics with different data, it has failed.
- Never become another analytics or rankings page. No heatmaps, no efficiency charts, no sortable stat tables. This is a museum, not a terminal.
- Never use `st.dataframe` or default Streamlit widgets for data display.
- Never hardcode names, scores, awards, or counts. All content derives from the workbook.
- Never swap owner colors. Matt = Blue, Ryan = Red.

---

## Data Architecture — IMPORTANT CHANGE

The backend workbook has been cleaned. It now contains **only three data sheets**: `players`, `man status`, and `wildcard boys`. The old per-exhibit sheets (Hall of Fame, Mount Rushmore, All-Franchise Teams) **no longer exist** and are not coming back.

**Therefore every Legacy exhibit derives in-app from `players`** — exactly like Dashboard, Rankings, and War Room already do. There are no exhibit data sheets to read. Compute everything:

- **GOAT Race** = all players ranked by legacy/overall score, owner-colored.
- **Mount Rushmore** = top 4 players per owner by `OVERALL SCORE` (computed default). These are the data-driven "faces." If a future curated override is wanted it'll be added later — for now, compute it.
- **All-Franchise** = best player per position per owner by `OVERALL SCORE`.
- **Hall of Fame** = there is no separate HOF dataset. For v1, treat **Franchise-tier players** as the de facto Hall (or a score threshold defined in `core/stats.py`). Do not invent a separate enshrinement list.
- **Greatest Draft Classes** = from `compute_class_stats()` (already exists).
- **Dynasty Awards Leaders** = sum the award columns in `players` (MVP, OPOY, DPOY, OROY, DROY, ALL_PRO, SB Win, SB_MVP) per owner.
- **Hall of Shame** = lowest-scoring picks / Bust-tier players.

All of these are computable today — nothing is blocked. The "empty sheet" problem is gone because we no longer depend on those sheets.

---

## Scope For This Sprint

Build the **lobby to production quality** — hero welcome hall, rivalry panel, Dynasty at a Glance, Recent Legacy Moments, the live data panels (GOAT Race, Awards, Greatest Classes, Spotlight), and the Timeline. The **exhibit cards render as navigation** with full museum styling.

For the **individual exhibit rooms**, build each one from the computed data above. They're real now — GOAT Race, Mount Rushmore (top-4 computed), All-Franchise, Greatest Classes, Hall of Shame, Record Book (career stat leaders), and Timeline all have a live data source. Legacy Hall = top-20 by score. Build them; none are blocked.

Where a room would be thin (e.g. very few qualifying players), show an honest "few entries" state rather than padding — but do not fabricate players. Every name shown must exist in `players`.

---

## Data & Logic

- Source: **`players` sheet only** (plus `man status` if a Legacy panel references the rivalry pick-offs, and `wildcard boys` if relevant). No exhibit-specific sheets exist.
- All derived rankings (GOAT, Mount Rushmore top-4, All-Franchise best-per-position, Legacy Hall top-20, Hall of Shame) are computed in `core/stats.py` as named functions, never inline in the page.
- `compute_class_stats()` already covers Greatest Classes grades and franchise/bust counts. Reuse it.
- Any threshold rule (what counts as "Hall of Fame," "Legacy Hall top 20") is a named constant/function in the stats layer.

---

## Components To Reuse / Extend

Reuse: `page_header` / a museum-skinned hero, `section_header`, `stat_card`, `callout`, `owner_chip`, `tier_badge`, `winner_badge`, `comparison_panel`, `rivalry_stat_row`, `draft_class_card`, `class_dive_row`.

New reusable components this sprint will likely generate (extract into `core/components.py`, they feed Man Status later): a **GOAT/legacy leaderboard row** (portrait + name + owner + score bar), an **exhibit card** (icon/image + title + subtitle + enter affordance), an **award-count tile** (trophy icon + count + label), a **timeline node**, and a **legacy spotlight / featured-player card**.

All museum styling (black marble, gold trim, trophy lighting, exhibit cards) lives in `assets/theme.css` as a dedicated Legacy section — not inline.

---

## Acceptance Criteria

- [ ] The page reads unmistakably as a **museum** — black/gold, ceremonial, distinct from every other page.
- [ ] Hero welcome hall with central trophy and the two dynasty banners is the dominant first impression.
- [ ] The Rivalry panel (Matt vs Ryan, live scores, leader) is present and anchors the page.
- [ ] Dynasty at a Glance, Recent Legacy Moments, GOAT Race Leaders, Dynasty Awards Leaders, Greatest Draft Classes, Legacy Spotlight, and Dynasty Timeline all render from live data.
- [ ] Exhibit cards present for all seven exhibits as styled navigation.
- [ ] Rooms are built from computed `players` data; no fabricated names — every player shown exists in `players`.
- [ ] No default Streamlit widgets for data display; nothing hardcoded.
- [ ] Matt = Blue, Ryan = Red, never swapped.
- [ ] New repeated patterns extracted into `core/components.py`; all museum CSS in `theme.css`.
- [ ] Passes the final test: would the NFL Hall of Fame ship this?
