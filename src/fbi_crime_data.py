import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from src.config import (
    END_YEAR,
    FBI_API_BASE_URL,
    FBI_API_KEY,
    FBI_CONTEXT_FLAGS_FILE,
    FBI_CONTEXT_RAW_FILE,
    FBI_CONTEXT_SUMMARY_FILE,
    FBI_EXPORTS_DIR,
    START_YEAR,
)


FBI_OFFENSES = {
    "fraud": "Fraud Offenses",
    "counterfeiting": "Counterfeiting / Forgery",
    "embezzlement": "Embezzlement",
    "extortion": "Extortion / Blackmail",
    "bribery": "Bribery",
}


FINANCIAL_CRIME_KEYWORDS = [
    "fraud",
    "counterfeit",
    "forgery",
    "embezzlement",
    "extortion",
    "blackmail",
    "bribery",
    "stolen property",
    "identity theft",
    "computer hacking",
    "computer invasion",
    "hacking",
    "human trafficking",
    "commercial sex acts",
    "involuntary servitude",
]


FBI_DETAIL_FILE = FBI_CONTEXT_RAW_FILE


def build_api_url(endpoint: str) -> str:
    """
    Build an FBI Crime Data API URL.
    """

    endpoint = endpoint.strip("/")
    return f"{FBI_API_BASE_URL}/{endpoint}"


def request_json(url: str, params: dict[str, Any] | None = None) -> dict:
    """
    Request JSON from the FBI Crime Data API.
    """

    if params is None:
        params = {}

    params = dict(params)
    params["API_KEY"] = FBI_API_KEY

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"WARNING: FBI API request failed: {url}")
        print(f"Reason: {exc}")
        return {}


def extract_results(payload: dict) -> list[dict]:
    """
    Extract results from FBI API payloads with common response shapes.
    """

    if not payload:
        return []

    if isinstance(payload, list):
        return payload

    for key in ["results", "data", "offenses", "counts"]:
        value = payload.get(key)

        if isinstance(value, list):
            return value

    return []


def normalize_fbi_records(
    records: list[dict],
    offense_slug: str,
    offense_label: str,
    geography: str,
) -> pd.DataFrame:
    """
    Normalize FBI API records into a standard table.
    """

    rows = []

    for record in records:
        year = (
            record.get("data_year")
            or record.get("year")
            or record.get("report_year")
            or record.get("published_year")
        )

        value = (
            record.get("actual")
            or record.get("count")
            or record.get("offense_count")
            or record.get("reported_count")
            or record.get("value")
            or record.get("incident_count")
        )

        try:
            year = int(year)
        except Exception:
            continue

        try:
            value = float(value)
        except Exception:
            continue

        rows.append(
            {
                "year": year,
                "geography": geography,
                "crime_category": offense_label,
                "reported_count": value,
                "source": "FBI Crime Data API",
                "source_file": "",
                "context_type": "api",
                "count_type": "records",
                "unique_incidents": np.nan,
                "data_basis": "FBI Crime Data API summarized state offense endpoint",
                "methodology_note": (
                    "FBI data is law-enforcement offense context. It is not SAR filing data "
                    "and is not included in the SAR Pressure Index."
                ),
            }
        )

    return pd.DataFrame(rows)


def fetch_summarized_state_offense(
    state_abbr: str,
    offense_slug: str,
    offense_label: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """
    Try to fetch summarized state offense data from FBI API.
    """

    url = build_api_url(f"summarized/state/{state_abbr}/{offense_slug}")

    payload = request_json(
        url,
        params={
            "from": start_year,
            "to": end_year,
        },
    )

    records = extract_results(payload)

    return normalize_fbi_records(
        records=records,
        offense_slug=offense_slug,
        offense_label=offense_label,
        geography=state_abbr,
    )


def fetch_fbi_api_context(
    state_abbr: str = "TN",
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> pd.DataFrame:
    """
    Attempt FBI API pulls for configured financial-crime categories.

    Local FBI flat-file exports are preferred. This is retained as a fallback.
    """

    frames = []

    for offense_slug, offense_label in FBI_OFFENSES.items():
        print(f"Fetching FBI Crime Data API offense: {offense_label}")

        df = fetch_summarized_state_offense(
            state_abbr=state_abbr,
            offense_slug=offense_slug,
            offense_label=offense_label,
            start_year=start_year,
            end_year=end_year,
        )

        if not df.empty:
            frames.append(df)

        time.sleep(0.25)

    if not frames:
        return pd.DataFrame()

    raw = pd.concat(frames, ignore_index=True)
    raw = raw[raw["year"].between(start_year, end_year)].copy()

    return raw


def find_fbi_zip_exports() -> list[Path]:
    """
    Find FBI ZIP exports in data/raw/fbi_exports.
    """

    FBI_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(FBI_EXPORTS_DIR.glob("*.zip"))


def is_financial_crime_offense(offense_name: str) -> bool:
    """
    Identify financial-crime-adjacent offense names.
    """

    lowered = str(offense_name).lower()
    return any(keyword in lowered for keyword in FINANCIAL_CRIME_KEYWORDS)


def normalize_category_name(category: str) -> str:
    """
    Normalize FBI category names for cleaner reporting.
    """

    text = str(category).strip()

    rename_map = {
        "Credit Card/Automated Teller Machine Fraud": "Credit Card / ATM Fraud",
        "Counterfeiting/Forgery": "Counterfeiting / Forgery",
        "Extortion/Blackmail": "Extortion / Blackmail",
        "Hacking/Computer Invasion": "Hacking / Computer Invasion",
        "Computer Hacking/Invasion": "Hacking / Computer Invasion",
        "Fraud - Computer Hacking/Invasion": "Hacking / Computer Invasion",
        "Human Trafficking, Commercial Sex Acts": "Human Trafficking - Commercial Sex Acts",
        "Human Trafficking, Involuntary Servitude": "Human Trafficking - Involuntary Servitude",
        "Commercial Sex Acts": "Human Trafficking - Commercial Sex Acts",
        "Involuntary Servitude": "Human Trafficking - Involuntary Servitude",
    }

    return rename_map.get(text, text)


def parse_tn_nibrs_zip(zip_path: Path) -> pd.DataFrame:
    """
    Parse a Tennessee annual NIBRS flat-file ZIP export.

    Required files:
    - NIBRS_OFFENSE.csv
    - NIBRS_OFFENSE_TYPE.csv
    """

    print(f"Parsing FBI/NIBRS Tennessee ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())

        required = {"NIBRS_OFFENSE.csv", "NIBRS_OFFENSE_TYPE.csv"}

        if not required.issubset(names):
            return pd.DataFrame()

        offense = pd.read_csv(
            z.open("NIBRS_OFFENSE.csv"),
            usecols=["data_year", "offense_id", "incident_id", "offense_code"],
        )

        offense_type = pd.read_csv(z.open("NIBRS_OFFENSE_TYPE.csv"))

    merged = offense.merge(
        offense_type[
            [
                "offense_code",
                "offense_name",
                "crime_against",
                "offense_category_name",
                "offense_group",
            ]
        ],
        on="offense_code",
        how="left",
    )

    merged = merged[merged["data_year"].between(START_YEAR, END_YEAR)].copy()

    filtered = merged[
        merged["offense_name"].apply(is_financial_crime_offense)
    ].copy()

    if filtered.empty:
        return pd.DataFrame()

    filtered["crime_category"] = filtered["offense_name"].apply(normalize_category_name)

    summary = (
        filtered.groupby(["data_year", "crime_category"], as_index=False)
        .agg(
            reported_count=("offense_id", "count"),
            unique_incidents=("incident_id", "nunique"),
        )
        .rename(columns={"data_year": "year"})
    )

    summary["geography"] = "TN"
    summary["source"] = "FBI Crime Data Explorer / NIBRS flat file"
    summary["source_file"] = zip_path.name
    summary["context_type"] = "nibrs_flat_file"
    summary["count_type"] = "offenses"
    summary["data_basis"] = (
        "FBI Crime Data Explorer NIBRS flat file parsed from NIBRS_OFFENSE "
        "and NIBRS_OFFENSE_TYPE."
    )
    summary["methodology_note"] = (
        "FBI/NIBRS offense data is used as law-enforcement context. "
        "It is not SAR filing data and is not included in the SAR Pressure Index."
    )

    return summary


def parse_human_trafficking_zip(zip_path: Path) -> pd.DataFrame:
    """
    Parse FBI human trafficking ZIP export.
    """

    print(f"Parsing FBI Human Trafficking ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path) as z:
        csv_names = [name for name in z.namelist() if name.lower().endswith(".csv")]

        if not csv_names:
            return pd.DataFrame()

        csv_name = csv_names[0]
        ht = pd.read_csv(z.open(csv_name))

    required_cols = {
        "DATA_YEAR",
        "STATE_ABBR",
        "OFFENSE_NAME",
        "OFFENSE_SUBCAT_NAME",
        "ACTUAL_COUNT",
    }

    if not required_cols.issubset(ht.columns):
        return pd.DataFrame()

    tn = ht[ht["STATE_ABBR"].astype(str).str.upper().eq("TN")].copy()
    tn = tn[tn["DATA_YEAR"].between(START_YEAR, END_YEAR)].copy()

    if tn.empty:
        return pd.DataFrame()

    tn["crime_category"] = (
        tn["OFFENSE_NAME"].astype(str)
        + " - "
        + tn["OFFENSE_SUBCAT_NAME"].astype(str)
    )

    tn["crime_category"] = tn["crime_category"].apply(normalize_category_name)

    summary = (
        tn.groupby(["DATA_YEAR", "crime_category"], as_index=False)
        .agg(reported_count=("ACTUAL_COUNT", "sum"))
        .rename(columns={"DATA_YEAR": "year"})
    )

    summary["unique_incidents"] = np.nan
    summary["geography"] = "TN"
    summary["source"] = "FBI Crime Data Explorer / Human Trafficking flat file"
    summary["source_file"] = zip_path.name
    summary["context_type"] = "human_trafficking_flat_file"
    summary["count_type"] = "actual_count"
    summary["data_basis"] = "FBI Crime Data Explorer Human Trafficking flat file."
    summary["methodology_note"] = (
        "Human trafficking is included as broader exploitation and illicit-finance context. "
        "It is not SAR filing data and is not included in the SAR Pressure Index."
    )

    return summary


def load_fbi_flat_file_exports() -> pd.DataFrame:
    """
    Load local FBI ZIP exports from data/raw/fbi_exports.
    """

    zip_files = find_fbi_zip_exports()

    if not zip_files:
        return pd.DataFrame()

    frames = []

    for zip_path in zip_files:
        lower_name = zip_path.name.lower()

        try:
            if "ht" in lower_name or "human" in lower_name:
                parsed = parse_human_trafficking_zip(zip_path)
            else:
                parsed = parse_tn_nibrs_zip(zip_path)

            if not parsed.empty:
                frames.append(parsed)

        except Exception as exc:
            print(f"WARNING: Could not parse FBI export {zip_path}: {exc}")

    if not frames:
        return pd.DataFrame()

    raw = pd.concat(frames, ignore_index=True)

    raw["crime_category"] = raw["crime_category"].apply(normalize_category_name)

    raw = raw.drop_duplicates(
        subset=[
            "year",
            "crime_category",
            "reported_count",
            "source_file",
            "context_type",
        ]
    )

    raw = raw.sort_values(["crime_category", "year"])

    raw.to_csv(FBI_CONTEXT_RAW_FILE, index=False)
    print(f"FBI financial-crime context raw data saved to: {FBI_CONTEXT_RAW_FILE}")

    return raw


def load_fbi_context(
    state_abbr: str = "TN",
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> pd.DataFrame:
    """
    Load FBI context from local flat-file exports first, then API fallback.
    """

    flat_file_df = load_fbi_flat_file_exports()

    if not flat_file_df.empty:
        return flat_file_df

    api_df = fetch_fbi_api_context(
        state_abbr=state_abbr,
        start_year=start_year,
        end_year=end_year,
    )

    if not api_df.empty:
        api_df.to_csv(FBI_CONTEXT_RAW_FILE, index=False)
        print(f"FBI financial-crime context raw data saved to: {FBI_CONTEXT_RAW_FILE}")

    return api_df


def summarize_fbi_context(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize FBI financial-crime context data by category.
    """

    if raw.empty:
        summary = pd.DataFrame()
        summary.to_csv(FBI_CONTEXT_SUMMARY_FILE, index=False)
        return summary

    raw = raw.copy()
    raw["crime_category"] = raw["crime_category"].apply(normalize_category_name)

    rows = []

    for category, group in raw.groupby("crime_category"):
        group = group.sort_values("year")

        first = group.iloc[0]
        latest = group.iloc[-1]

        if first["reported_count"] > 0 and len(group) >= 2:
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
                "absolute_change": latest["reported_count"] - first["reported_count"],
                "total_change_pct": total_change_pct,
                "geography": latest.get("geography", "TN"),
                "source": latest.get("source", "FBI Crime Data Explorer"),
                "source_file": latest.get("source_file", ""),
                "context_type": latest.get("context_type", ""),
                "count_type": latest.get("count_type", ""),
                "data_basis": latest.get(
                    "data_basis",
                    "FBI Crime Data Explorer / NIBRS offense context",
                ),
                "methodology_note": latest.get(
                    "methodology_note",
                    (
                        "FBI/NIBRS data is law-enforcement offense context. "
                        "It is not SAR filing data and is not included in the SAR Pressure Index."
                    ),
                ),
            }
        )

    summary = pd.DataFrame(rows).sort_values(
        ["latest_reported_count", "crime_category"],
        ascending=[False, True],
    )

    summary.to_csv(FBI_CONTEXT_SUMMARY_FILE, index=False)
    print(f"FBI financial-crime context summary saved to: {FBI_CONTEXT_SUMMARY_FILE}")

    return summary


def build_fbi_context_flags(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Build FBI context flags for the intelligence report.
    """

    flags = []

    if summary.empty:
        flags.append(
            {
                "flag_type": "FBI Context Unavailable",
                "severity": "Informational",
                "description": (
                    "FBI Crime Data API/export context was attempted, but no financial-crime "
                    "offense records were returned or parsed."
                ),
                "methodology_scope": "Supporting law-enforcement context",
            }
        )
    else:
        max_year = pd.to_numeric(summary["latest_year"], errors="coerce").max()

        flags.append(
            {
                "flag_type": "FBI Context Available",
                "severity": "Informational",
                "description": (
                    "FBI Crime Data Explorer flat-file context is included as a law-enforcement "
                    "data layer for financial-crime-adjacent offense categories."
                ),
                "methodology_scope": "Supporting law-enforcement context",
            }
        )

        if not pd.isna(max_year) and int(max_year) > END_YEAR:
            flags.append(
                {
                    "flag_type": "FBI Year Validation",
                    "severity": "Moderate",
                    "description": (
                        f"FBI context includes a latest_year value of {int(max_year)}, which is beyond "
                        f"the project study end year of {END_YEAR}. Review FBI export filtering before publication."
                    ),
                    "methodology_scope": "Supporting context data-quality flag",
                }
            )

        for _, row in summary.head(8).iterrows():
            flags.append(
                {
                    "flag_type": "FBI Numeric Context",
                    "severity": "Informational",
                    "description": (
                        f"{row['crime_category']} had "
                        f"{float(row['latest_reported_count']):,.0f} reported "
                        f"{row.get('count_type', 'records')} in "
                        f"{int(row['latest_year'])} for {row['geography']}."
                    ),
                    "methodology_scope": "Supporting law-enforcement context",
                }
            )

        trafficking_rows = summary[
            summary["crime_category"]
            .astype(str)
            .str.lower()
            .str.contains("human trafficking", na=False)
        ]

        if not trafficking_rows.empty:
            trafficking_total = trafficking_rows["latest_reported_count"].sum()

            flags.append(
                {
                    "flag_type": "Human Trafficking Context",
                    "severity": "Informational",
                    "description": (
                        f"FBI/NIBRS context includes {float(trafficking_total):,.0f} "
                        "latest-year human-trafficking-related records for Tennessee. "
                        "This supports broader exploitation and illicit-finance context, "
                        "but is not a direct SAR measure."
                    ),
                    "methodology_scope": "Supporting exploitation and law-enforcement context",
                }
            )

    flags_df = pd.DataFrame(flags)
    flags_df.to_csv(FBI_CONTEXT_FLAGS_FILE, index=False)

    print(f"FBI financial-crime context flags saved to: {FBI_CONTEXT_FLAGS_FILE}")

    return flags_df


def run_fbi_crime_data_analysis(
    state_abbr: str = "TN",
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> dict:
    """
    Run the FBI Crime Data context layer.
    """

    raw = load_fbi_context(
        state_abbr=state_abbr,
        start_year=start_year,
        end_year=end_year,
    )

    summary = summarize_fbi_context(raw)
    flags = build_fbi_context_flags(summary)

    return {
        "fbi_context_raw": raw,
        "fbi_summary": summary,
        "fbi_flags": flags,
    }