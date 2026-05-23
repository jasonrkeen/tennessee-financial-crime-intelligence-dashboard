import csv
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    END_YEAR,
    RAW_DATA_DIR,
    TBI_CONTEXT_FILE,
    TBI_CONTEXT_FLAGS_FILE,
    TBI_CONTEXT_SUMMARY_FILE,
    TBI_EXPORTS_DIR,
    TBI_STATEWIDE_2024_CONTEXT_FILE,
)


TBI_DETAIL_FILE = TBI_CONTEXT_SUMMARY_FILE.parent / "tbi_financial_crime_context_detail.csv"


# ------------------------------------------------------------
# Authoritative 2024 statewide TBI context
#
# Source basis:
# Crime in Tennessee 2024
# Tennessee Statewide - NIBRS Agency Crime Overview - 2024
# ------------------------------------------------------------

TBI_STATEWIDE_2024_ROWS = [
    {
        "year": 2024,
        "crime_category": "Counterfeiting / Forgery",
        "reported_count": 4462,
        "cleared_count": 1520,
    },
    {
        "year": 2024,
        "crime_category": "Embezzlement",
        "reported_count": 1673,
        "cleared_count": 614,
    },
    {
        "year": 2024,
        "crime_category": "Extortion / Blackmail",
        "reported_count": 1038,
        "cleared_count": 43,
    },
    {
        "year": 2024,
        "crime_category": "Fraud - False Pretenses",
        "reported_count": 14258,
        "cleared_count": 2420,
    },
    {
        "year": 2024,
        "crime_category": "Fraud - Credit Card / ATM",
        "reported_count": 7036,
        "cleared_count": 715,
    },
    {
        "year": 2024,
        "crime_category": "Fraud - Impersonation",
        "reported_count": 4142,
        "cleared_count": 1471,
    },
    {
        "year": 2024,
        "crime_category": "Fraud - Welfare",
        "reported_count": 163,
        "cleared_count": 23,
    },
    {
        "year": 2024,
        "crime_category": "Fraud - Wire",
        "reported_count": 1951,
        "cleared_count": 101,
    },
    {
        "year": 2024,
        "crime_category": "Fraud - Identity Theft",
        "reported_count": 457,
        "cleared_count": 61,
    },
    {
        "year": 2024,
        "crime_category": "Fraud - Computer Hacking / Invasion",
        "reported_count": 209,
        "cleared_count": 8,
    },
    {
        "year": 2024,
        "crime_category": "Stolen Property Offenses",
        "reported_count": 2060,
        "cleared_count": 1471,
    },
    {
        "year": 2024,
        "crime_category": "Bribery",
        "reported_count": 17,
        "cleared_count": 14,
    },
    {
        "year": 2024,
        "crime_category": "Human Trafficking - Commercial Sex Acts",
        "reported_count": 87,
        "cleared_count": 35,
    },
    {
        "year": 2024,
        "crime_category": "Human Trafficking - Involuntary Servitude",
        "reported_count": 8,
        "cleared_count": 1,
    },
]


FINANCIAL_CRIME_KEYWORDS = [
    "bribery",
    "counterfeiting",
    "forgery",
    "embezzlement",
    "extortion",
    "blackmail",
    "fraud",
    "identity theft",
    "computer hacking",
    "computer invasion",
    "stolen property",
    "welfare fraud",
    "credit card",
    "atm",
    "wire",
    "false pretenses",
    "impersonation",
    "bad checks",
    "swindle",
    "commercial sex acts",
    "involuntary servitude",
    "human trafficking",
]


TBI_TEMPLATE_COLUMNS = [
    "year",
    "crime_category",
    "reported_count",
    "count_type",
    "jurisdiction",
    "source",
    "notes",
]


DEFAULT_TBI_CONTEXT_ROWS = [
    {
        "year": 2024,
        "crime_category": "Fraud Offenses",
        "reported_count": np.nan,
        "count_type": "crimes",
        "jurisdiction": "Tennessee",
        "source": "TBI CrimeInsight / TIBRS",
        "notes": "Manual entry placeholder or export-derived aggregate.",
    },
    {
        "year": 2024,
        "crime_category": "Counterfeiting / Forgery",
        "reported_count": np.nan,
        "count_type": "crimes",
        "jurisdiction": "Tennessee",
        "source": "TBI CrimeInsight / TIBRS",
        "notes": "Manual entry placeholder or export-derived value.",
    },
    {
        "year": 2024,
        "crime_category": "Embezzlement",
        "reported_count": np.nan,
        "count_type": "crimes",
        "jurisdiction": "Tennessee",
        "source": "TBI CrimeInsight / TIBRS",
        "notes": "Manual entry placeholder or export-derived value.",
    },
    {
        "year": 2024,
        "crime_category": "Extortion / Blackmail",
        "reported_count": np.nan,
        "count_type": "crimes",
        "jurisdiction": "Tennessee",
        "source": "TBI CrimeInsight / TIBRS",
        "notes": "Manual entry placeholder or export-derived value.",
    },
    {
        "year": 2024,
        "crime_category": "Bribery",
        "reported_count": np.nan,
        "count_type": "crimes",
        "jurisdiction": "Tennessee",
        "source": "TBI CrimeInsight / TIBRS",
        "notes": "Manual entry placeholder or export-derived value.",
    },
]


def clean_number(value):
    """
    Convert CrimeInsight count strings into numeric values.
    """

    if value is None:
        return np.nan

    text = str(value).strip().replace(",", "")

    if text == "":
        return np.nan

    try:
        return float(text)
    except ValueError:
        return np.nan


def normalize_category_name(category: str) -> str:
    """
    Normalize TBI category names for cleaner reporting and comparison.
    """

    text = str(category).strip()
    text = re.sub(r"\s+", " ", text)

    rename_map = {
        "Counterfeiting/Forgery": "Counterfeiting / Forgery",
        "Extortion/Blackmail": "Extortion / Blackmail",
        "Fraud - Credit Card/ATM": "Fraud - Credit Card / ATM",
        "Fraud - Computer Hacking/Invasion": "Fraud - Computer Hacking / Invasion",
        "Fraud - False Pretenses": "Fraud - False Pretenses",
        "Fraud - Identity Theft": "Fraud - Identity Theft",
        "Fraud - Impersonation": "Fraud - Impersonation",
        "Fraud - Wire": "Fraud - Wire",
        "Fraud - Welfare": "Fraud - Welfare",
        "Commercial Sex Acts": "Human Trafficking - Commercial Sex Acts",
        "Involuntary Servitude": "Human Trafficking - Involuntary Servitude",
    }

    return rename_map.get(text, text)


def calculate_clearance_rate(reported_count, cleared_count):
    """
    Calculate clearance rate safely.
    """

    if pd.isna(reported_count) or reported_count <= 0:
        return np.nan

    if pd.isna(cleared_count):
        return np.nan

    return cleared_count / reported_count


def build_statewide_2024_context() -> pd.DataFrame:
    """
    Build authoritative TBI 2024 statewide financial-crime context table.

    This is preferred over CrimeInsight CSV parsing because it avoids accidentally
    using export/report dates as offense years.
    """

    rows = []

    for row in TBI_STATEWIDE_2024_ROWS:
        reported_count = float(row["reported_count"])
        cleared_count = float(row["cleared_count"])

        rows.append(
            {
                "year": 2024,
                "crime_category": normalize_category_name(row["crime_category"]),
                "reported_count": reported_count,
                "cleared_count": cleared_count,
                "clearance_rate": calculate_clearance_rate(
                    reported_count,
                    cleared_count,
                ),
                "count_type": "crimes",
                "jurisdiction": "Tennessee",
                "source": "Crime in Tennessee 2024 / TBI TIBRS statewide table",
                "source_file": "Crime in Tennessee 2024",
                "data_basis": (
                    "Tennessee Statewide - NIBRS Agency Crime Overview - 2024; "
                    "Crime in Tennessee 2024"
                ),
                "notes": (
                    "Authoritative statewide 2024 context manually encoded from the "
                    "Crime in Tennessee 2024 report."
                ),
            }
        )

    detail = pd.DataFrame(rows)

    fraud_rows = detail[
        detail["crime_category"].astype(str).str.lower().str.startswith("fraud")
    ].copy()

    if not fraud_rows.empty:
        fraud_reported = fraud_rows["reported_count"].sum()
        fraud_cleared = fraud_rows["cleared_count"].sum()

        aggregate_row = {
            "year": 2024,
            "crime_category": "Fraud Offenses",
            "reported_count": fraud_reported,
            "cleared_count": fraud_cleared,
            "clearance_rate": calculate_clearance_rate(fraud_reported, fraud_cleared),
            "count_type": "crimes",
            "jurisdiction": "Tennessee",
            "source": "Crime in Tennessee 2024 / TBI TIBRS statewide table",
            "source_file": "Crime in Tennessee 2024",
            "data_basis": (
                "Aggregate of statewide 2024 TBI/TIBRS fraud subcategories from "
                "Crime in Tennessee 2024."
            ),
            "notes": "Aggregate of all Fraud-prefixed statewide 2024 rows.",
        }

        detail = pd.concat([detail, pd.DataFrame([aggregate_row])], ignore_index=True)

    detail = detail.sort_values(["year", "crime_category"])
    detail.to_csv(TBI_STATEWIDE_2024_CONTEXT_FILE, index=False)
    detail.to_csv(TBI_DETAIL_FILE, index=False)

    print(f"TBI statewide 2024 context saved to: {TBI_STATEWIDE_2024_CONTEXT_FILE}")
    print(f"TBI context detail saved to: {TBI_DETAIL_FILE}")

    return detail


def extract_year_from_metadata(lines: list[list[str]]) -> int | None:
    """
    Extract the incident year from CrimeInsight metadata rows.

    Only accepts explicit incident-date/year style labels. This avoids grabbing
    generic report/export years.
    """

    patterns = [
        r"Incident Date:\s*(20\d{2})",
        r"Incident Year:\s*(20\d{2})",
        r"Incident Year\(s\):\s*(20\d{2})",
        r"Year of Incident:\s*(20\d{2})",
    ]

    for row in lines[:25]:
        if not row:
            continue

        row_text = " ".join(str(cell) for cell in row if cell is not None)

        for pattern in patterns:
            match = re.search(pattern, row_text, flags=re.IGNORECASE)
            if match:
                year = int(match.group(1))

                if year <= END_YEAR:
                    return year

    return None


def extract_source_from_metadata(lines: list[list[str]]) -> str:
    """
    Extract source description from CrimeInsight metadata rows.
    """

    for row in lines[:20]:
        if not row:
            continue

        row_text = " ".join(str(cell) for cell in row if cell is not None)

        if "Data source:" in row_text:
            return row_text.replace("Data source:", "").strip()

        if "TIBRS" in row_text.upper():
            return row_text.strip()

    return "TBI CrimeInsight / TIBRS"


def is_financial_crime_offense(offense_type: str) -> bool:
    """
    Identify financial-crime-adjacent offense rows.
    """

    lowered = str(offense_type).lower()

    return any(keyword in lowered for keyword in FINANCIAL_CRIME_KEYWORDS)


def parse_tbi_crimeinsight_export(file_path: Path) -> pd.DataFrame:
    """
    Parse a TBI CrimeInsight 'Crimes and Clearances by Offense Type' CSV export.

    This is retained as a fallback. The authoritative 2024 statewide table is
    preferred for the final report.
    """

    try:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin1", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

    if not rows:
        return pd.DataFrame()

    year = extract_year_from_metadata(rows)
    source_detail = extract_source_from_metadata(rows)

    if year is None:
        print(
            f"Could not identify explicit incident year in {file_path}; "
            "skipping export to avoid using report/export year."
        )
        return pd.DataFrame()

    header_idx = None

    for idx, row in enumerate(rows):
        normalized = [str(cell).strip().lower() for cell in row]

        if "incident clearance" in normalized and "all clearances" in normalized:
            header_idx = idx
            break

        if "offense type" in normalized and len(normalized) >= 2:
            header_idx = idx
            break

    if header_idx is None:
        print(f"Could not identify TBI export header in: {file_path}")
        return pd.DataFrame()

    data_rows = []

    for row in rows[header_idx + 1 :]:
        if not row:
            continue

        offense_type = str(row[0]).strip() if len(row) > 0 else ""

        if not offense_type or offense_type.lower() == "offense type":
            continue

        reported_count = clean_number(row[1]) if len(row) > 1 else np.nan
        cleared_count = clean_number(row[2]) if len(row) > 2 else np.nan

        if pd.isna(reported_count):
            continue

        if not is_financial_crime_offense(offense_type):
            continue

        normalized_category = normalize_category_name(offense_type)

        data_rows.append(
            {
                "year": int(year),
                "crime_category": normalized_category,
                "reported_count": reported_count,
                "cleared_count": cleared_count,
                "clearance_rate": calculate_clearance_rate(
                    reported_count,
                    cleared_count,
                ),
                "count_type": "crimes",
                "jurisdiction": "Tennessee",
                "source": f"TBI CrimeInsight / {source_detail}",
                "source_file": file_path.name,
                "data_basis": "TBI CrimeInsight / TIBRS Crimes and Clearances by Offense Type export",
                "notes": "Parsed from TBI CrimeInsight Crimes and Clearances by Offense Type export.",
            }
        )

    detail = pd.DataFrame(data_rows)

    if detail.empty:
        return detail

    fraud_rows = detail[
        detail["crime_category"].astype(str).str.lower().str.startswith("fraud")
    ].copy()

    if not fraud_rows.empty:
        fraud_reported = fraud_rows["reported_count"].sum()
        fraud_cleared = fraud_rows["cleared_count"].sum()

        aggregate_row = {
            "year": int(year),
            "crime_category": "Fraud Offenses",
            "reported_count": fraud_reported,
            "cleared_count": fraud_cleared,
            "clearance_rate": calculate_clearance_rate(fraud_reported, fraud_cleared),
            "count_type": "crimes",
            "jurisdiction": "Tennessee",
            "source": f"TBI CrimeInsight / {source_detail}",
            "source_file": file_path.name,
            "data_basis": "TBI CrimeInsight / TIBRS aggregate of Fraud-prefixed offense rows",
            "notes": "Aggregate of all offense rows beginning with 'Fraud -'.",
        }

        detail = pd.concat([detail, pd.DataFrame([aggregate_row])], ignore_index=True)

    return detail


def find_tbi_export_files() -> list[Path]:
    """
    Find CrimeInsight export files in data/raw/tbi_exports and data/raw.
    """

    TBI_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    candidates = []

    for folder in [TBI_EXPORTS_DIR, RAW_DATA_DIR]:
        if not folder.exists():
            continue

        for path in folder.glob("*.csv"):
            if path.name in {
                TBI_CONTEXT_FILE.name,
                TBI_STATEWIDE_2024_CONTEXT_FILE.name,
            }:
                continue

            name = path.name.lower()

            if (
                "crime" in name
                or "clearance" in name
                or "offense" in name
                or "tbi" in name
            ):
                candidates.append(path)

    return sorted(set(candidates))


def load_tbi_exports() -> pd.DataFrame:
    """
    Load and parse all available TBI CrimeInsight export files.

    Fallback only. The statewide 2024 table is preferred.
    """

    export_files = find_tbi_export_files()

    if not export_files:
        return pd.DataFrame()

    parsed_frames = []

    for file_path in export_files:
        print(f"Parsing TBI export: {file_path}")
        parsed = parse_tbi_crimeinsight_export(file_path)

        if not parsed.empty:
            parsed_frames.append(parsed)

    if not parsed_frames:
        return pd.DataFrame()

    detail = pd.concat(parsed_frames, ignore_index=True)

    detail["crime_category"] = detail["crime_category"].apply(normalize_category_name)

    detail = detail[detail["year"].le(END_YEAR)].copy()

    detail = detail.drop_duplicates(
        subset=[
            "year",
            "crime_category",
            "reported_count",
            "cleared_count",
            "source_file",
        ]
    )

    detail = detail.sort_values(["year", "crime_category"])

    detail.to_csv(TBI_DETAIL_FILE, index=False)
    print(f"TBI context detail saved to: {TBI_DETAIL_FILE}")

    return detail


def create_tbi_context_template() -> pd.DataFrame:
    """
    Create a starter manual-entry TBI context CSV if no export files exist.
    """

    TBI_CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)

    template = pd.DataFrame(DEFAULT_TBI_CONTEXT_ROWS, columns=TBI_TEMPLATE_COLUMNS)
    template.to_csv(TBI_CONTEXT_FILE, index=False)

    print(f"TBI context template created: {TBI_CONTEXT_FILE}")
    return template


def load_manual_tbi_context() -> pd.DataFrame:
    """
    Load manual TBI context CSV if available.
    """

    if not TBI_CONTEXT_FILE.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(TBI_CONTEXT_FILE)
    except Exception as exc:
        print(f"Could not read manual TBI context file: {exc}")
        return pd.DataFrame()

    if df.empty or "reported_count" not in df.columns:
        return pd.DataFrame()

    df["reported_count"] = pd.to_numeric(df["reported_count"], errors="coerce")
    df = df.dropna(subset=["reported_count"])

    if df.empty:
        return pd.DataFrame()

    df["crime_category"] = df["crime_category"].apply(normalize_category_name)

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df = df[df["year"].le(END_YEAR)].copy()

    if df.empty:
        return pd.DataFrame()

    if "cleared_count" not in df.columns:
        df["cleared_count"] = np.nan

    if "clearance_rate" not in df.columns:
        df["clearance_rate"] = df.apply(
            lambda row: calculate_clearance_rate(
                row.get("reported_count"),
                row.get("cleared_count"),
            ),
            axis=1,
        )

    if "source_file" not in df.columns:
        df["source_file"] = TBI_CONTEXT_FILE.name

    if "data_basis" not in df.columns:
        df["data_basis"] = "Manual TBI context CSV"

    if "notes" not in df.columns:
        df["notes"] = "Manual entry."

    if "count_type" not in df.columns:
        df["count_type"] = "crimes"

    if "jurisdiction" not in df.columns:
        df["jurisdiction"] = "Tennessee"

    return df


def load_tbi_context() -> pd.DataFrame:
    """
    Load TBI context data.

    Preferred order:
    1. Authoritative statewide 2024 table from Crime in Tennessee 2024.
    2. CrimeInsight exports with explicit incident year.
    3. Manual context file.
    4. Empty manual-entry template.
    """

    statewide_2024_df = build_statewide_2024_context()

    if not statewide_2024_df.empty:
        return statewide_2024_df

    export_df = load_tbi_exports()

    if not export_df.empty:
        return export_df

    manual_df = load_manual_tbi_context()

    if not manual_df.empty:
        return manual_df

    return create_tbi_context_template()


def summarize_tbi_context(tbi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize TBI financial-crime context data.
    """

    if tbi_df.empty:
        summary = pd.DataFrame()
        summary.to_csv(TBI_CONTEXT_SUMMARY_FILE, index=False)
        return summary

    numeric = tbi_df.dropna(subset=["reported_count"]).copy()

    if numeric.empty:
        summary = pd.DataFrame(
            [
                {
                    "summary_note": (
                        "TBI context file exists, but no numeric reported_count values "
                        "have been entered or parsed yet."
                    )
                }
            ]
        )

        summary.to_csv(TBI_CONTEXT_SUMMARY_FILE, index=False)
        print(f"TBI context summary saved to: {TBI_CONTEXT_SUMMARY_FILE}")

        return summary

    numeric["crime_category"] = numeric["crime_category"].apply(normalize_category_name)
    numeric = numeric[pd.to_numeric(numeric["year"], errors="coerce").le(END_YEAR)].copy()

    rows = []

    for category, group in numeric.groupby("crime_category"):
        group = group.sort_values("year")

        first = group.iloc[0]
        latest = group.iloc[-1]

        if len(group) >= 2 and first["reported_count"] > 0:
            total_change_pct = latest["reported_count"] / first["reported_count"] - 1
        else:
            total_change_pct = np.nan

        rows.append(
            {
                "crime_category": category,
                "first_year": int(first["year"]),
                "latest_year": int(latest["year"]),
                "first_reported_count": first["reported_count"],
                "latest_reported_count": latest["reported_count"],
                "cleared_count": latest.get("cleared_count", np.nan),
                "clearance_rate": latest.get("clearance_rate", np.nan),
                "absolute_change": latest["reported_count"] - first["reported_count"],
                "total_change_pct": total_change_pct,
                "count_type": latest.get("count_type", "crimes"),
                "jurisdiction": latest.get("jurisdiction", "Tennessee"),
                "source": latest.get("source", ""),
                "source_file": latest.get("source_file", ""),
                "data_basis": latest.get(
                    "data_basis",
                    "TBI CrimeInsight / TIBRS financial-crime-adjacent offense context",
                ),
                "methodology_note": (
                    "TBI data is law-enforcement reported offense context. "
                    "It is not SAR filing data and is not included in the SAR Pressure Index."
                ),
                "notes": latest.get("notes", ""),
            }
        )

    summary = pd.DataFrame(rows).sort_values(
        ["latest_reported_count", "crime_category"],
        ascending=[False, True],
    )

    summary.to_csv(TBI_CONTEXT_SUMMARY_FILE, index=False)
    print(f"TBI context summary saved to: {TBI_CONTEXT_SUMMARY_FILE}")

    return summary


def build_tbi_context_flags(tbi_df: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    """
    Build TBI context flags for the intelligence report.
    """

    flags = []

    if tbi_df.empty:
        flags.append(
            {
                "flag_type": "TBI Context Missing",
                "severity": "Informational",
                "description": "No TBI context data was available.",
                "methodology_scope": "Supporting law-enforcement context",
            }
        )
    else:
        flags.append(
            {
                "flag_type": "TBI Context Available",
                "severity": "Informational",
                "description": (
                    "TBI/TIBRS statewide 2024 context is included as law-enforcement "
                    "context for Tennessee financial-crime-adjacent offense categories."
                ),
                "methodology_scope": "Supporting law-enforcement context",
            }
        )

    if not summary.empty and "latest_year" in summary.columns:
        max_year = pd.to_numeric(summary["latest_year"], errors="coerce").max()

        if not pd.isna(max_year) and int(max_year) > END_YEAR:
            flags.append(
                {
                    "flag_type": "TBI Year Validation",
                    "severity": "Moderate",
                    "description": (
                        f"TBI context contains latest_year {int(max_year)}, which is beyond "
                        f"the project study end year of {END_YEAR}. Review source-year parsing."
                    ),
                    "methodology_scope": "Supporting context data-quality flag",
                }
            )

    if not summary.empty and "crime_category" in summary.columns:
        fraud_row = summary[
            summary["crime_category"].astype(str).str.lower().eq("fraud offenses")
        ]

        if not fraud_row.empty:
            row = fraud_row.iloc[0]
            flags.append(
                {
                    "flag_type": "Fraud Offense Context",
                    "severity": "Moderate",
                    "description": (
                        f"TBI/TIBRS context shows {row['latest_reported_count']:,.0f} "
                        f"reported Fraud Offenses in {int(row['latest_year'])}, "
                        "providing law-enforcement context for SAR fraud, payments-risk, "
                        "and elder financial exploitation themes."
                    ),
                    "methodology_scope": "Supporting law-enforcement context",
                }
            )

        identity_rows = summary[
            summary["crime_category"]
            .astype(str)
            .str.lower()
            .str.contains("identity theft", na=False)
        ]

        if not identity_rows.empty:
            row = identity_rows.iloc[0]
            flags.append(
                {
                    "flag_type": "Identity Theft Context",
                    "severity": "Moderate",
                    "description": (
                        f"TBI/TIBRS context includes {row['latest_reported_count']:,.0f} "
                        f"reported identity-theft-related crimes in {int(row['latest_year'])}, "
                        "aligning with SAR identity theft and elder exploitation themes."
                    ),
                    "methodology_scope": "Supporting law-enforcement context",
                }
            )

        extortion_rows = summary[
            summary["crime_category"]
            .astype(str)
            .str.lower()
            .str.contains("extortion|blackmail", na=False, regex=True)
        ]

        if not extortion_rows.empty:
            row = extortion_rows.iloc[0]
            flags.append(
                {
                    "flag_type": "Extortion / Blackmail Context",
                    "severity": "Moderate",
                    "description": (
                        f"TBI/TIBRS context includes {row['latest_reported_count']:,.0f} "
                        f"reported Extortion/Blackmail crimes in {int(row['latest_year'])}, "
                        "supporting broader coercion, fraud, and exploitation context."
                    ),
                    "methodology_scope": "Supporting law-enforcement context",
                }
            )

        for _, row in summary.head(5).iterrows():
            flags.append(
                {
                    "flag_type": "TBI Numeric Context",
                    "severity": "Informational",
                    "description": (
                        f"{row.get('crime_category')} had "
                        f"{row.get('latest_reported_count'):,.0f} reported "
                        f"{row.get('count_type', 'records')} in "
                        f"{int(row.get('latest_year'))} for "
                        f"{row.get('jurisdiction', 'Tennessee')}."
                    ),
                    "methodology_scope": "Supporting law-enforcement context",
                }
            )

    flags_df = pd.DataFrame(flags)
    flags_df.to_csv(TBI_CONTEXT_FLAGS_FILE, index=False)

    print(f"TBI context flags saved to: {TBI_CONTEXT_FLAGS_FILE}")

    return flags_df


def run_tbi_context_analysis() -> dict:
    """
    Run the full TBI context layer.
    """

    tbi_df = load_tbi_context()
    summary = summarize_tbi_context(tbi_df)
    flags = build_tbi_context_flags(tbi_df, summary)

    return {
        "tbi_context": tbi_df,
        "tbi_summary": summary,
        "tbi_flags": flags,
    }