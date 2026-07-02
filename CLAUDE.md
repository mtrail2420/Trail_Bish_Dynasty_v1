CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
---
Mission
Trail & Bish Dynasty is a premium sports analytics application — not a spreadsheet viewer.
It should feel like a television broadcast. The workbook is the database. The application is the experience.
The concept: Two friends. Twenty draft classes. Hundreds of players. One rivalry.
Every page must reinforce this rivalry.
---
Product Identity
Trail & Bish Dynasty is not a data visualization tool. It is an interactive sports experience.
Every page has its own identity:
Page	Identity
Dashboard	SportsCenter
Players	PFF
Rankings	ESPN Stats
Draft War Room	NFL Front Office
Analytics	Bloomberg Terminal
Legacy Center	Hall of Fame Museum
Man Status	Sunday Night Football + UFC Main Event
These identities are LOCKED. Do not reinterpret or dilute them.
---
Approved UI Renders
The `designs/` folder contains approved page renders. These renders are the visual source of truth.
Do not redesign them.
Do not simplify them.
Implement them as faithfully as Streamlit allows.
If implementation becomes difficult, preserve visual fidelity over engineering convenience.
---
Running the App
```bash
streamlit run app.py
```
---
Architecture
```
app.py                  Entry point — page config, global CSS injection, redirects to Dashboard
pages/                  One file per page (Streamlit multipage)
core/data_loader.py     All workbook I/O — single source of truth
core/components.py      Reusable UI components only — never duplicate component logic
core/sidebar.py         Shared sidebar — call render_sidebar() on every page
assets/theme.css        Complete dark-theme + tb-* component CSS system
backend/*.xlsx          Single Excel workbook — all data lives here
docs/                   Product documentation — read before coding
designs/                Approved UI renders — visual source of truth
.streamlit/config.toml  Streamlit theme + server config
```
`core/` is the canonical home for shared code. Data loading, UI components, and the sidebar live in `core/data_loader.py`, `core/components.py`, and `core/sidebar.py` respectively. Do not introduce parallel module trees (e.g. a separate `components/` or `helpers/` folder) that compete with `core/`. New shared logic extends an existing `core/` module or, only when genuinely warranted, a new module under `core/`.
Data flow: Every page calls `render_sidebar()`, loads data via `core/data_loader.py`, and renders UI via `core/components.py` using `st.markdown(..., unsafe_allow_html=True)`.
Caching: `load_workbook()` uses `@st.cache_resource` (ExcelFile is not picklable). All sheet loaders use `@st.cache_data`.
---
Workbook Sheet Names (exact, case-sensitive)
Loader	Sheet
`load_dashboard()`	`dashboard`
`load_players()`	`players`
`load_rankings()`	`AP Rankings`
`load_legacy()`	`Legacy Center`
`load_war_room()`	`Draft War Room`
`load_wildcard()`	`wildcard boys`
`load_player_rankings()`	`Player Rankings`
Key facts from `players` (354 rows — primary source of truth):
Matt: 177 players, 53.8 avg score
Ryan: 177 players, 59.3 avg score — Ryan leads
48 Franchise players, 20 draft classes (2007–2026)
Never trust aggregate sheets when `players` can compute the value live
---
Component System
All UI is rendered via HTML. Never use `st.metric`, `st.dataframe`, or bare `st.write`.
`core/components.py` — use on every page:
`page_header(title, subtitle)` — ESPN-style page title
`section_header(title, subtitle)` — accent-line section divider
`stat_card(label, value, subtitle, color)` — glow metric card
`rivalry_banner(matt_df, ryan_df)` — full-width head-to-head comparison
`player_row(rank, name, owner, position, year, score, tier)` — ranked player row with score bar
`player_table(rows_html)` — styled container for player rows
`callout(label, value, detail, color)` — highlight card with colored left border
`owner_chip(owner)` — inline Matt/Ryan colored pill
`tier_badge(tier)` — Franchise / High-End Starter / Starter / Contributor / Bust
`position_chip(position)` — dark position label
`core/sidebar.py` — call `render_sidebar()` at the top of every page (after `st.set_page_config`). Handles branding, nav, and live rivalry scoreboard.
---
Styling
Dark navy scheme (`#070B13` bg, `#2E7DFF` primary). CSS classes in `assets/theme.css`:
Class	Use
`.tb-card` + `.tb-blue/.tb-red/.tb-green/.tb-gold`	Glow stat cards
`.tb-chip-matt` / `.tb-chip-ryan`	Owner inline chips
`.tb-tier-franchise/.tb-tier-elite/.tb-tier-starter/.tb-tier-contrib/.tb-tier-bust`	Tier badges
`.tb-rivalry-banner`	Side-by-side rivalry block
`.tb-player-row` / `.tb-player-table`	Ranked player list
`.tb-matt` (`#2E7DF7`) / `.tb-ryan` (`#E63B3B`)	Owner text colors — never swap
Streamlit header, footer, main menu, and sidebar nav are hidden in `app.py`.
---
Experience Hierarchy
Not every page carries equal weight. Spend implementation effort accordingly.
Tier	Page
★★★★★	Man Status
★★★★★	Legacy Center
★★★★☆	Dashboard
★★★★☆	Draft War Room
★★★☆☆	Players
★★★☆☆	Rankings
★★★☆☆	Analytics
---
Adding a Page
Audit `core/components.py` first. Check whether any existing component covers the UI you need, or can cover it with a new parameter. Extend the shared component before writing page-specific HTML.
Create `pages/PageName.py`
Call `render_sidebar()` after `st.set_page_config`
Import loaders from `core/data_loader.py`
Use components from `core/components.py` — no default Streamlit widgets
Add the page to `_NAV` in `core/sidebar.py`
If a new UI pattern appears on this page that another page will also need — add it to `core/components.py` now, not later.
Component discipline: Page files should read like an assembly of named components, not raw HTML. No inline `style=` except for dynamic values (e.g. bar widths computed from data). All CSS lives in `assets/theme.css`.
Every page must have: a large hero header, strong visual hierarchy, multiple custom cards, color + icons + whitespace, hover effects, and at least one signature feature unique to that page.
---
V1 Status: COMPLETE (closed July 2026)
All sprints are done. The open roadmap no longer applies. Do not treat sprint or feature language below as a to-do list — it is build history. The only scheduled work is the April annual update (see docs/ANNUAL_UPDATE.md). Any future session should read DECISIONS.md and PROJECT_STATUS.md before proposing changes.
---
Page Philosophies
Page	Philosophy
Dashboard	The broadcast. Answers: what happened, what matters, what's next. Never a table.
Players	The database explorer. All stats derive from the `players` sheet.
Legacy Center	The museum. Prestigious. Celebrates careers, tells stories.
Draft War Room	Strategy and competition. Wins, misses, trends.
Wildcard Boys	Entertainment first. Cooked Meter. Crazy picks.
Man Status	The rivalry.
---
Component Rules
If the same UI appears twice, it becomes a reusable component in `core/components.py`.
If a CSS rule appears twice, it belongs in `assets/theme.css`.
If business logic appears twice, move it into `core/data_loader.py` or a dedicated `core/` helper module.
New data → `core/data_loader.py`. New styles → `assets/theme.css`. New components → `core/components.py`. New pages → `pages/`.
Never duplicate UI, styles, or logic. Edit the canonical source; do not copy it.
---
Implementation Philosophy
Always build for production. Never build temporary code.
Never leave TODO placeholders.
Never ship partially implemented components.
If a feature cannot be completed, finish the supporting architecture first.
Complete one production-quality feature before beginning the next.
Production quality always beats implementation speed.
---
Definition of Done
A feature is complete only when it is:
Production-ready and fully tested
Built from reusable components
Driven by real workbook data (no hardcoded values)
Consistent with the locked visual identity
Meeting ESPN-quality expectations
An improvement to the overall architecture
Testing checklist before any feature is complete:
[ ] Imports verified
[ ] Syntax verified
[ ] Workbook loads
[ ] Streamlit launches without error
[ ] Navigation not broken
[ ] No missing assets
[ ] Real data displayed (no hardcoded values)
---
Core Rules
No fake data. Never hardcode player names, stats, or counts. All values derive from the workbook.
No unstyled Streamlit defaults. Every surface uses the `tb-*` system.
Owner colors are permanent. Matt = Blue (`#2E7DF7`). Ryan = Red (`#E63B3B`). Never swap.
Never break existing pages and never remove working features.
---
Final Test
Before completing any feature, ask:
Would ESPN release this?
Would Apple ship this?
Would PFF use this?
If the answer is no, keep improving.
Success is measured by product quality, not lines of code.