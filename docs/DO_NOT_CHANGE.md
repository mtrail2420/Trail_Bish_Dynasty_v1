DO NOT CHANGE
Locked product decisions for Trail & Bish Dynasty.
These decisions are approved and final. Engineering may improve how they are implemented but may not change what they are without explicit approval.
If an engineering improvement conflicts with anything in this file, preserve the locked decision and ask for clarification rather than changing it. This file exists to prevent slow, accidental redesign drift over many sprints.
---
1. Product Identity
Trail & Bish Dynasty is a premium sports analytics experience. It is not a spreadsheet viewer, an admin dashboard, or a stats website. Do not redesign it into one.
2. The Workbook
The Excel workbook in `backend/` is the permanent database. The application presents and analyzes that data. Do not restructure the workbook schema to make the code easier. The code adapts to the workbook, not the other way around.
3. Master Data
The `players` sheet is the primary source of truth (354 rows). Derived pages should calculate from `players` whenever practical. Aggregate/summary sheets are presentation, not authority.
4. Owner Colors
Matt = Blue (`#2E7DF7`)
Ryan = Red (`#E63B3B`)
These are permanent. Never swap them. Gold (`#D4AF37`) is reserved for legacy.
5. Navigation Order
```
Dashboard
Players
Rankings
Draft War Room
Analytics
Legacy Center
Man Status
```
New pages may be added later. This order remains.
6. Page Purposes
Each page answers one question and must not absorb another page's job.
Dashboard → Overview
Players → Player exploration
Rankings → Competition / leaderboard
Draft War Room → Draft analysis
Analytics → Insight (the why)
Legacy Center → History
Man Status → Rivalry
Do not create seven variations of the same dashboard.
7. Page Identities
Dashboard → SportsCenter
Players → PFF
Rankings → ESPN Stats
Draft War Room → NFL Front Office
Analytics → Bloomberg Terminal
Legacy Center → Hall of Fame Museum
Man Status → Sunday Night Football + UFC Main Event
These identities are permanent and must remain consistent.
8. Experience Hierarchy
The five-star ranking (Man Status and Legacy Center at the top) determines where polish and effort go. Do not flatten it — these pages are not all equal.
9. Legacy Center Concept
Legacy Center is a museum. Its role is to celebrate careers and accomplishments with ceremony — black and gold, trophy-room aesthetic, exhibit-style sections (e.g. GOAT Race, Mount Rushmore, Record Book, Hall of Shame, All-Franchise Teams, Timeline). It is not another analytics or rankings page. It should look and feel different from the rest of the app while sharing the same chrome (sidebar, fonts, colors).
10. Man Status Concept
Man Status is the emotional centerpiece of the application — a head-to-head showdown styled like a primetime fight card (giant VS, position battles, momentum, power meters, prediction, Mount Rushmore faceoff). It receives the highest level of polish. It is not another dashboard and must never be reduced to a plain stats table.
---
What Engineering CAN Change Freely
Engineering has standing authorization to improve any of the following without asking, provided the locked decisions above stay intact:
Architecture and module organization (within the `core/` convention)
Reusable components and helper extraction
CSS organization in `assets/theme.css`
Performance, caching, and load behavior
Responsiveness and accessibility
Animations and micro-interactions
Testing, validation, and documentation
Removing duplication and technical debt
The repository should become stronger after every sprint — not merely larger.
---
Conflict Resolution
When two priorities collide, resolve in this order:
Product decision beats engineering convenience.
Maintainability beats clever brevity.
Usability beats aesthetics.
The rivalry experience is never sacrificed for any of the above.
If an improvement would violate a locked decision, stop and ask. Do not change the product to make the code easier.