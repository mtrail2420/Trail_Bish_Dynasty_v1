from pathlib import Path
import pandas as pd
import streamlit as st

from core.stats import score_to_tier


# ---------------------------------------------------
# Project Paths
# ---------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BACKEND_FILE = (
    PROJECT_ROOT
    / "backend"
    / "AP_Dynasty_Backend.xlsx"
)


# ---------------------------------------------------
# Workbook Loader
# ---------------------------------------------------

@st.cache_resource(show_spinner=False)
def load_workbook():
    """
    Opens the backend workbook one time and caches it.
    Uses cache_resource (not cache_data) because pd.ExcelFile is not picklable.

    Returns
    -------
    pandas.ExcelFile
    """

    if not BACKEND_FILE.exists():
        raise FileNotFoundError(
            f"Backend workbook not found:\n{BACKEND_FILE}"
        )

    return pd.ExcelFile(BACKEND_FILE)


# ---------------------------------------------------
# Generic Sheet Loader
# ---------------------------------------------------

@st.cache_data(show_spinner=False)
def load_sheet(sheet_name: str) -> pd.DataFrame:
    """
    Load any sheet from the backend workbook.
    """

    workbook = load_workbook()

    return pd.read_excel(
        workbook,
        sheet_name=sheet_name,
    )


# ---------------------------------------------------
# Players
# ---------------------------------------------------

@st.cache_data(show_spinner=False)
def load_players() -> pd.DataFrame:
    """
    Returns Players database with score-derived CAREER_TIER.
    Primary source of truth: 354 rows × 19+ columns.

    CAREER_TIER is computed from OVERALL SCORE on every load using
    score_to_tier() — the workbook column is intentionally ignored.
    This guarantees tiers are always current with the scoring formula.

    HOF column: read from the workbook if present; defaulted to False
    otherwise.  Matt adds real HOF inductees to the workbook; the badge
    appears automatically.  HOF is NOT a tier — it is a separate flag.
    """
    df = load_sheet("players").copy()

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


# ---------------------------------------------------
# Man Status
# ---------------------------------------------------

@st.cache_data(show_spinner=False)
def load_man_status() -> pd.DataFrame:
    """
    Returns the Man Status picks table.

    Sheet layout: title in rows 0–1, blank row 2, column headers in row 3,
    data starting at row 4. Uses header=3 to skip the decorative title block.

    Columns: YEAR, MATT_PICK, MATT_POS, MATT_SCORE, MATT_RESUME,
             RYAN_PICK, RYAN_POS, RYAN_SCORE, RYAN_RESUME,
             WINNER, MARGIN, MATT_NOTES, RYAN_NOTES

    Returns 20 rows — one per draft class (2007–2026).
    """
    workbook = load_workbook()
    df = pd.read_excel(workbook, sheet_name="man status", header=3)
    return df.reset_index(drop=True)


# ---------------------------------------------------
# Wildcard Boys
# ---------------------------------------------------

@st.cache_data(show_spinner=False)
def load_wildcard() -> pd.DataFrame:
    """
    Returns the Wildcard Boys picks table, clean and typed.

    Sheet layout: rows 0-5 are metadata/description; row 6 (index 6) is the
    column-header row; data begins at row 7 (index 7).  We skip directly to
    row 7 so no header-row filtering is needed downstream.

    Columns returned:
      YEAR (int), OWNER (str), PLAYER (str), POSITION (str),
      CATEGORY (str: WC1–WC4), OUTCOME (str | NaN), COOKED_METER (float | NaN),
      NOTES (str | NaN)

    WC Score is intentionally NOT stored — derive it live as ``100 - COOKED_METER``.
    Exclude 'Too early' rows from scoreboard averages (see page implementation).
    Rows where OUTCOME is NaN are 2026-class pending picks (not yet drafted).
    """
    workbook = load_workbook()
    df = pd.read_excel(workbook, sheet_name="wildcard boys", header=None)

    # Skip metadata block and column-header row → data starts at index 7
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

    # Drop rows that are scoring-key table fragments (no PLAYER value)
    picks = picks[picks["PLAYER"].notna() & (picks["PLAYER"].astype(str).str.strip() != "")].copy()

    # Type coercions
    picks["YEAR"]         = pd.to_numeric(picks["YEAR"],         errors="coerce")
    picks["COOKED_METER"] = pd.to_numeric(picks["COOKED_METER"], errors="coerce")

    # Drop any lingering non-year rows
    picks = picks[picks["YEAR"].notna()].copy()

    return picks.reset_index(drop=True)


# ---------------------------------------------------
# Utility
# ---------------------------------------------------

def workbook_exists() -> bool:
    return BACKEND_FILE.exists()


def workbook_path() -> Path:
    return BACKEND_FILE
