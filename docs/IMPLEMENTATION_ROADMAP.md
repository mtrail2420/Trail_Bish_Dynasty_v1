IMPLEMENTATION ROADMAP
Trail & Bish Dynasty — build plan and sprint structure.
This is the authoritative build order. It reconciles the page priorities (`PRODUCT_BIBLE.md` → Experience Hierarchy) with a sprint workflow. Work proceeds one sprint at a time; each sprint is completed to production quality before the next begins.
At the end of every sprint, update `docs/PROJECT_STATUS.md`, `docs/DECISIONS.md`, and `docs/KNOWN_ISSUES.md`.
---
Status Snapshot
Sprint	Focus	Status
Sprint 1	Foundation	✅ Complete
Sprint 2	Core pages	🟡 In progress
Sprint 3	Depth pages	🟡 War Room underway
Sprint 4	Centerpiece & intelligence	⬜ Not started
Sprint 5	Hardening	⬜ Not started
> Note: Draft War Room (a Sprint 3 page) is being built ahead of sequence because it generates the largest number of reusable components (draft cards, grade badges, comparison panels, class rows) that later pages reuse. This is a deliberate, approved exception — component leverage outranks strict ordering.
---
Sprint 1 — Foundation ✅
The shared infrastructure every page depends on.
Theme and global CSS (`assets/theme.css`)
Sidebar + navigation (`core/sidebar.py`, `render_sidebar(active=...)`)
Shared components (`core/components.py`)
Data layer (`core/data_loader.py`)
Pure helpers (`core/utils.py`) and computed stats (`core/stats.py`)
Validation/test scaffolding and the `docs/` status files
Done. Repository architecture is production-grade.
---
Sprint 2 — Core Pages
The three most-used pages, matched to their approved identities.
Dashboard (SportsCenter) — ★★★★☆ — complete, eligible for a later polish pass
Players (PFF) — ★★★☆☆
Rankings (ESPN Stats) — ★★★☆☆
These reuse the foundation heavily and establish the patterns the rest of the app follows.
---
Sprint 3 — Depth Pages
The pages that give the app its differentiated personality.
Draft War Room (NFL Front Office) — ★★★★☆ — in progress
Analytics (Bloomberg Terminal) — ★★★☆☆
Legacy Center (Hall of Fame Museum) — ★★★★★
Legacy Center is five-star and deserves museum-grade ceremony even though it lands in this sprint.
---
Sprint 4 — Centerpiece & Intelligence
The emotional payoff and the smart layer.
Man Status (SNF + UFC main event) — ★★★★★ — the flagship; budget roughly the effort of several normal pages
Animations — fade, slide, lift, glow, count-up, staggered reveals
AI layer — Insight of the Day, Smack Talk, predictions, "Did You Know?"
Polish — transitions and consistency pass across all pages
---
Sprint 5 — Hardening
Make it fast, stable, and shippable.
Performance tuning and caching review
Responsive fixes (desktop → laptop → tablet)
Bug fixes and edge cases (empty states, pending scores)
Final QA against the Definition of Done
---
Page Priority Reference
When choosing what to build next within a sprint, weight by the Experience Hierarchy:
Priority	Page	Sprint
★★★★★	Man Status	4
★★★★★	Legacy Center	3
★★★★☆	Dashboard	2
★★★★☆	Draft War Room	3
★★★☆☆	Players	2
★★★☆☆	Rankings	2
★★★☆☆	Analytics	3
---
Definition of Done (per page)
A page is complete only when it is:
Production-ready and fully tested
Built from reusable components (no copy-pasted UI)
Driven by real workbook data (no hardcoded values)
Consistent with its locked identity and the shared visual language
Passing the final test (Would ESPN/Apple/PFF ship this?)
An improvement to the overall architecture
Testing checklist before sign-off:
[ ] Imports verified
[ ] Syntax verified
[ ] Workbook loads
[ ] Streamlit launches without error
[ ] Navigation not broken
[ ] No missing assets
[ ] Real data displayed
---
The Next Three Things
Finish Draft War Room to production quality (in progress). Lock in its reusable components.
Backfill the page specs that influence current work — starting with `DraftWarRoom.md`, then `Players.md` and `Dashboard.md` — so the active sprint has explicit acceptance criteria.
Proceed to Analytics and Legacy Center (Sprint 3), reusing War Room's component output wherever possible.
Do not jump to a new major feature until the current one is complete and stable.