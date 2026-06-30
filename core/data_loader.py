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

def load_wildcard() -> pd.DataFrame:
    """
    Returns Wildcard Boys picks with outcome + cooked meter data.
    Skips header rows — data starts at row 6 (index 6).
    """

    df = pd.read_excel(load_workbook(), sheet_name="wildcard boys", header=None)
    data = df.iloc[6:].copy()
    data.columns = ["YEAR", "OWNER", "PLAYER", "POSITION", "CATEGORY",
                    "OUTCOME", "COOKED_METER", "NOTES", "WC_SCORE",
                    "BLANK", "SCORING_KEY", *[f"_x{i}" for i in range(data.shape[1] - 11)]]
    return data[["YEAR", "OWNER", "PLAYER", "POSITION", "CATEGORY",
                 "OUTCOME", "COOKED_METER", "NOTES", "WC_SCORE"]].reset_index(drop=True)


# ---------------------------------------------------
# Utility
# ---------------------------------------------------

def workbook_exists() -> bool:
    return BACKEND_FILE.exists()


def workbook_path() -> Path:
    return BACKEND_FILE
