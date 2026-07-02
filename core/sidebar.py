"""
core/sidebar.py

Shared sidebar renderer.  Call ``render_sidebar(active="PageLabel")`` at
the top of every page, immediately after ``st.set_page_config()``.

Responsibilities
----------------
• Inject global CSS (theme.css) — necessary because st.switch_page() triggers
  a full page re-render, discarding anything injected in app.py.
• Hide Streamlit chrome (header, footer, main menu, auto-nav).
• Render branding, navigation, and live rivalry scoreboard.
• Highlight the current page in the nav (via the ``active`` parameter).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.data_loader import load_players, workbook_exists


_CSS_PATH = Path("assets/theme.css")

_CHROME_HIDE = """
<style>
#MainMenu                       { visibility: hidden; }
header                          { visibility: hidden; }
footer                          { visibility: hidden; }
[data-testid="stSidebarNav"]    { display: none; }
.block-container                { padding-top:1rem; padding-bottom:2rem; max-width:1600px; }
</style>
"""

# Navigation registry — add new pages here as they are built.
# Format: (icon, display_label, page_path)
_NAV: list[tuple[str, str, str]] = [
    ("🏠",  "Dashboard",   "pages/Dashboard.py"),
    ("🗂️", "Players",     "pages/Players.py"),
    ("📊", "Rankings",    "pages/Rankings.py"),
    ("⚔️", "War Room",   "pages/WarRoom.py"),
    ("🏛️", "Legacy",     "pages/Legacy.py"),
    ("🥊", "Man Status", "pages/ManStatus.py"),
    ("📈", "Analytics",  "pages/Analytics.py"),
    ("📐", "Formula",    "pages/Formula.py"),
]


def render_sidebar(active: str = "") -> None:
    """
    Render the global sidebar and inject the page theme.

    Parameters
    ----------
    active:
        Display label of the current page (e.g. ``"Dashboard"``).
        Matched against ``_NAV`` labels to highlight the active item.
        Pass empty string (default) when no highlight is needed.
    """
    # ── CSS + chrome-hiding ───────────────────────────────────────────────────
    if _CSS_PATH.exists():
        st.markdown(
            f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
    st.markdown(_CHROME_HIDE, unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:

        # Branding
        st.markdown(
            """
            <div class="tb-sidebar-logo">
                <div class="tb-sidebar-title">🏈 Trail &amp; Bish</div>
                <div class="tb-sidebar-subtitle">Boys Dynasty · 2007–2026</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="tb-sidebar-divider"></div>', unsafe_allow_html=True)

        # Navigation
        for icon, label, path in _NAV:
            if label == active:
                # Active page: styled div (cannot be clicked; distinct visual state)
                st.markdown(
                    f'<div class="tb-nav-active">{icon}&nbsp;&nbsp;{label}</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                    st.switch_page(path)

        st.markdown('<div class="tb-sidebar-spacer"></div>', unsafe_allow_html=True)

        # Live rivalry scoreboard
        if not workbook_exists():
            return

        try:
            df         = load_players()
            matt_avg   = df[df["OWNER"] == "Matt"]["OVERALL SCORE"].mean()
            ryan_avg   = df[df["OWNER"] == "Ryan"]["OVERALL SCORE"].mean()
            leader     = "Matt" if matt_avg >= ryan_avg else "Ryan"
            leader_cls = "tb-matt" if leader == "Matt" else "tb-ryan"

            st.markdown(
                f"""
                <div class="tb-rivalry-box">
                    <div class="tb-rivalry-title">⚔️ Rivalry</div>
                    <div class="tb-score-row">
                        <span class="tb-matt">Matt</span>
                        <span class="tb-matt">{matt_avg:.1f} avg</span>
                    </div>
                    <div class="tb-score-row">
                        <span class="tb-ryan">Ryan</span>
                        <span class="tb-ryan">{ryan_avg:.1f} avg</span>
                    </div>
                    <div class="tb-sidebar-leader {leader_cls}">{leader} leads</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            pass
