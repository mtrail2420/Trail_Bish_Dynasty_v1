from pathlib import Path
import pandas as pd
import streamlit as st

from core.stats import score_to_tier


# ── Project Paths ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BACKEND_FILE = (
    PROJECT_ROOT
    / "backend"
    / "AP_Dynasty_Backend.xlsx"
)


# ── Cache-busting ──────────────────────────────────────────────────────────────

def _backend_mtime() -> float:
    """Return the backend workbook's modification time (epoch seconds)."""
    try:
        return BACKEND_FILE.stat().st_mtime
    except (FileNotFoundError, OSError):
        return 0.0


def bust_stale_cache() -> None:
    """
    Call once per page render — render_sidebar() handles this automatically.

    Compares the backend workbook's current mtime against the value seen when
    the caches were last filled.  If the file changed (e.g. after a push),
    all Streamlit caches are cleared so the very next load_* call reads fresh
    data from disk.  A stat() call is the only overhead on cache-hit runs.
    """
    current = _backend_mtime()
    if st.session_state.get("_tb_mtime") != current:
        st.cache_resource.clear()
        st.cache_data.clear()
        st.session_state["_tb_mtime"] = current


# ── Required columns (used for validation and friendly error messages) ─────────

_PLAYERS_REQUIRED = ["PLAYER", "POSITION", "OWNER", "YEAR", "OVERALL SCORE"]
_MAN_STATUS_REQUIRED = ["YEAR", "MATT_PICK", "RYAN_PICK", "WINNER"]


# ── Workbook Loader ────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_workbook():
    """
    Opens the backend workbook one time and caches it.
    Uses cache_resource (not cache_data) because pd.ExcelFile is not picklable.
    """
    if not BACKEND_FILE.exists():
        raise FileNotFoundError(
            f"Backend workbook not found:\n{BACKEND_FILE}"
        )
    return pd.ExcelFile(BACKEND_FILE)


# ── Generic Sheet Loader ───────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_sheet(sheet_name: str) -> pd.DataFrame:
    """Load any sheet from the backend workbook."""
    workbook = load_workbook()
    return pd.read_excel(workbook, sheet_name=sheet_name)


# ── Error Message Formatter ────────────────────────────────────────────────────

def _fmt_load_error(sheet: str, exc: Exception) -> str:
    """
    Converts a raw loading exception into a plain-English message
    that tells the user exactly what to fix in the workbook.
    """
    s = str(exc)
    sl = s.lower()

    if "not found" in sl and "worksheet" not in sl:
        return (
            f"⚠️ **Workbook not found.**  \n"
            f"Can't find `backend/AP_Dynasty_Backend.xlsx`. "
            f"Make sure the file exists and hasn't been renamed or moved."
        )

    if ("worksheet" in sl and "not found" in sl) or "no sheet named" in sl:
        return (
            f"⚠️ **Couldn't load the '{sheet}' sheet.**  \n"
            f"The app expects a sheet tab named exactly `{sheet}` (case-sensitive). "
            f"Check for typos or accidental renames in `backend/AP_Dynasty_Backend.xlsx`."
        )

    if isinstance(exc, KeyError) or "missing required" in sl:
        return (
            f"⚠️ **The '{sheet}' sheet loaded, but a required column is missing.**  \n"
            f"{s}  \n"
            f"Check the header row in `backend/AP_Dynasty_Backend.xlsx` for typos or renamed columns."
        )

    return (
        f"⚠️ **Error loading the '{sheet}' sheet.**  \n"
        f"`{s}`  \n"
        f"Check `backend/AP_Dynasty_Backend.xlsx` — sheet name, header row, and column names."
    )


# ── Internal Cached Implementations ───────────────────────────────────────────
#
# These do the actual work and are cached.  They raise plain exceptions on
# failure — never call st.stop().  The public wrappers below convert those
# exceptions to friendly Streamlit messages.
#
# get_data_status() calls these directly so it can probe without stopping.

@st.cache_data(show_spinner=False)
def _load_players_raw() -> pd.DataFrame:
    df = load_sheet("players").copy()

    missing = [c for c in _PLAYERS_REQUIRED if c not in df.columns]
    if missing:
        raise KeyError(
            f"Missing required columns in 'players': {', '.join(missing)}. "
            f"Required: {', '.join(_PLAYERS_REQUIRED)}"
        )

    # Derive CAREER_TIER from score — never trust the workbook column.
    df["CAREER_TIER"] = df["OVERALL SCORE"].apply(
        lambda s: score_to_tier(float(s)) if pd.notna(s) else ""
    )

    # HOF badge column — falls back to False if not yet in workbook.
    if "HOF" not in df.columns:
        df["HOF"] = False
    else:
        df["HOF"] = df["HOF"].fillna(False).astype(bool)

    return df


@st.cache_data(show_spinner=False)
def _load_man_status_raw() -> pd.DataFrame:
    workbook = load_workbook()
    df = pd.read_excel(workbook, sheet_name="man status", header=3)

    missing = [c for c in _MAN_STATUS_REQUIRED if c not in df.columns]
    if missing:
        raise KeyError(
            f"Missing required columns in 'man status': {', '.join(missing)}. "
            f"Required: {', '.join(_MAN_STATUS_REQUIRED)}"
        )

    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _load_wildcard_raw() -> pd.DataFrame:
    workbook = load_workbook()
    df = pd.read_excel(workbook, sheet_name="wildcard boys", header=None)

    data = df.iloc[7:].copy()
    n_extra = max(0, data.shape[1] - 11)
    data.columns = (
        ["YEAR", "OWNER", "PLAYER", "POSITION", "CATEGORY",
         "OUTCOME", "COOKED_METER", "NOTES", "_wc_score",
         "_blank", "_scoring_key"]
        + [f"_x{i}" for i in range(n_extra)]
    )

    picks = data[["YEAR", "OWNER", "PLAYER", "POSITION",
                  "CATEGORY", "OUTCOME", "COOKED_METER", "NOTES"]].copy()

    picks = picks[
        picks["PLAYER"].notna() &
        (picks["PLAYER"].astype(str).str.strip() != "")
    ].copy()

    picks["YEAR"]         = pd.to_numeric(picks["YEAR"],         errors="coerce")
    picks["COOKED_METER"] = pd.to_numeric(picks["COOKED_METER"], errors="coerce")
    picks = picks[picks["YEAR"].notna()].copy()

    return picks.reset_index(drop=True)


# ── Public API — Friendly Error Wrappers ───────────────────────────────────────
#
# Pages call these.  On failure: show a plain-English st.error() message that
# says which sheet or column is the problem, then st.stop() the page cleanly.
#
# Note: st.stop() raises StopException (a subclass of Exception).  The sidebar
# re-raises it from its try/except so it isn't accidentally swallowed.

def load_players() -> pd.DataFrame:
    """
    Returns Players database with score-derived CAREER_TIER.
    Primary source of truth: 354 rows × 19+ columns.

    Shows a plain-English error and stops the page on any data problem.
    """
    try:
        return _load_players_raw()
    except Exception as exc:
        st.error(_fmt_load_error("players", exc))
        st.stop()


def load_man_status() -> pd.DataFrame:
    """
    Returns the Man Status picks table.

    Sheet layout: title in rows 0–1, blank row 2, column headers in row 3,
    data starting at row 4.  Uses header=3 to skip the decorative title block.

    Shows a plain-English error and stops the page on any data problem.
    """
    try:
        return _load_man_status_raw()
    except Exception as exc:
        st.error(_fmt_load_error("man status", exc))
        st.stop()


def load_wildcard() -> pd.DataFrame:
    """
    Returns the Wildcard Boys picks table, clean and typed.

    Sheet layout: rows 0-5 are metadata; row 6 is the column-header row;
    data begins at row 7.

    Shows a plain-English error and stops the page on any data problem.
    """
    try:
        return _load_wildcard_raw()
    except Exception as exc:
        st.error(_fmt_load_error("wildcard boys", exc))
        st.stop()


# ── Data Status ────────────────────────────────────────────────────────────────

def get_data_status() -> dict:
    """
    Probe all three sheets and return a status dict.
    Never calls st.stop() — safe to call from the sidebar.

    Returns
    -------
    dict
        players    : int | None   — row count on success, None on failure
        sheets_ok  : int          — sheets that loaded successfully (0–3)
        errors     : list[str]    — one short message per failed sheet
    """
    status: dict = {"players": None, "sheets_ok": 0, "errors": []}

    if not BACKEND_FILE.exists():
        status["errors"].append("workbook file not found")
        return status

    try:
        df = _load_players_raw()
        status["players"] = len(df)
        status["sheets_ok"] += 1
    except Exception as exc:
        status["errors"].append(f"'players': {str(exc)[:70]}")

    try:
        _load_man_status_raw()
        status["sheets_ok"] += 1
    except Exception as exc:
        status["errors"].append(f"'man status': {str(exc)[:70]}")

    try:
        _load_wildcard_raw()
        status["sheets_ok"] += 1
    except Exception as exc:
        status["errors"].append(f"'wildcard boys': {str(exc)[:70]}")

    return status


# ── Utility ────────────────────────────────────────────────────────────────────

def workbook_exists() -> bool:
    return BACKEND_FILE.exists()


def workbook_path() -> Path:
    return BACKEND_FILE
