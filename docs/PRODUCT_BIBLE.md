PRODUCT BIBLE
Trail & Bish Dynasty — Version 1.0
This document defines what the product is and why it exists. It is the highest-level reference in the repository. `CLAUDE.md` governs engineering; this governs product. When an engineering decision and a product decision conflict, the product decision wins (see `DO_NOT_CHANGE.md`).
Read this before writing code. Read `DO_NOT_CHANGE.md` immediately after.
---
Product Identity
Trail & Bish Dynasty is a premium sports analytics application built around a twenty-year NFL Draft rivalry between two friends, Matt and Ryan.
What it is: an interactive sports experience. It should feel like a broadcast — closer to ESPN, PFF, The Athletic, or Apple Sports than to a business dashboard.
What it is not: a spreadsheet viewer, an admin panel, or a statistics website. The Excel workbook stores the truth. The application tells the story.
The product exists to turn two decades of draft history into something that feels alive, competitive, and worth showing a friend.
---
Mission
Transform twenty years of draft data into a modern sports application that celebrates competition, scouting, history, legacy, and — above all — the rivalry.
Every page must reinforce that rivalry. If a feature doesn't make the rivalry more visible, more felt, or more fun, it needs a strong reason to exist.
---
Core Principles
The workbook is the database. The application is the experience. Data lives in Excel; the app presents and dramatizes it.
Every page answers a different question. No two pages share a purpose.
Every page has a distinct personality while sharing one visual language.
Data tells stories — it doesn't just fill tables.
Reusable components over duplicated implementations. Build it once, use it everywhere.
Quality beats speed. Production-ready or not shipped.
The rivalry is felt on every page. Matt vs Ryan is the spine of the product.
---
Page Identities (LOCKED)
Each page has a fixed identity that dictates its tone, layout, and density. These do not change.
Page	Identity	The question it answers
Dashboard	SportsCenter	What's happening right now?
Players	PFF scouting database	Who is this player?
Rankings	ESPN Stats	Who is the best?
Draft War Room	NFL front office	Who drafted better?
Analytics	Bloomberg Terminal	Why is one owner winning?
Legacy Center	Hall of Fame museum	What history matters?
Man Status	Sunday Night Football + UFC main event	Who owns the rivalry?
---
Experience Hierarchy
Not every page carries equal weight. Implementation effort, polish, and signature features should follow this ranking.
Tier	Page
★★★★★	Man Status
★★★★★	Legacy Center
★★★★☆	Dashboard
★★★★☆	Draft War Room
★★★☆☆	Players
★★★☆☆	Rankings
★★★☆☆	Analytics
Man Status and Legacy Center are the pages people will show their friends. They get the most ceremony.
---
The User Journey
The application is designed to build toward an emotional climax. The natural path is:
```
Dashboard      →  "Here's the state of the rivalry."
Players        →  "Learn who everyone is."
Rankings       →  "Who's objectively best?"
Draft War Room →  "Who drafted better?"
Analytics      →  "Why did they draft better?"
Legacy Center  →  "Who made history?"
Man Status     →  "Who's winning the war?"
```
Every page should feel like a step toward Man Status, which is the payoff.
---
Page Purposes (do not merge them)
Dashboard — Overview. The broadcast open. What happened, what matters, what's next. Never a table.
Players — Player exploration. The scouting database. All stats derive from the `players` sheet.
Rankings — Competition. The authoritative leaderboard across players, owners, positions, and draft classes.
Draft War Room — Draft analysis. Class-by-class evaluation: winners, steals, busts, grades. A front office, not a spreadsheet.
Analytics — Insight. The page you open to win an argument. Trends, heatmaps, efficiency, why.
Legacy Center — History. A museum that celebrates careers and accomplishments. Not another analytics page.
Man Status — Rivalry. The head-to-head showdown. The emotional centerpiece. Not another dashboard.
---
Data Philosophy
The `players` sheet (354 rows) is the master database and the single source of truth.
Whenever practical, compute values live from `players` rather than trusting pre-aggregated summary sheets.
The workbook schema is owned by the product, not engineering. Don't restructure it without approval.
Never hardcode player names, stats, or counts. If it's a fact about the league, it comes from the workbook.
Known anchors (from `players`):
Matt: 177 players, 53.8 avg score
Ryan: 177 players, 59.3 avg score — Ryan currently leads
48 Franchise players, 20 draft classes (2007–2026)
Tiers: Franchise / High-End Starter / Starter / Contributor / Bust
---
Design Philosophy
Visual identity: dark theme, broadcast energy, premium feel. One shared design language across all pages, expressed through `assets/theme.css` and the `tb-*` component system.
Owner colors (permanent):
Matt = Blue (`#2E7DF7`)
Ryan = Red (`#E63B3B`)
These never swap. Gold (`#D4AF37`) represents legacy.
Tone: premium, confident, modern, competitive, immersive. Never corporate. Never generic. Never spreadsheet-like.
Rules of thumb:
Every page has a large hero header, strong visual hierarchy, multiple custom cards, generous whitespace, hover states, and at least one signature feature unique to that page.
Custom HTML/CSS over default Streamlit widgets — always.
Cards never touch. Spacing follows an 8-point rhythm.
---
Product Quality Standard
Before any feature is considered done, it must pass the final test:
> Would ESPN release this? Would Apple ship this? Would PFF use this?
If the answer is no, it isn't finished. Success is measured by product quality, not lines of code. A first-time user should assume this was built by a professional sports-analytics company — not as a personal Streamlit project.
---
Division of Labor
This project runs like a small software team:
Product owns the experience: vision, page identities, layouts, visual direction, what each page is for.
Engineering owns the implementation: architecture, components, performance, refactoring, testing.
Engineering is encouraged to improve architecture freely. Engineering does not redesign the product. When in doubt, preserve the approved experience and ask.
---
Future Vision
Version 1 ships the seven core pages to production quality. Beyond that, candidate directions (not commitments) include: Ask Boys AI, mobile responsiveness, player comparison tools, a trade machine, a draft simulator, an expanded historical timeline, and league mode.
None of these justify delaying or compromising the core seven. The product earns its future by nailing the present.