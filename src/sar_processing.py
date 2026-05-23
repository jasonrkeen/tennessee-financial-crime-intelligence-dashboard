import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.config import (
    END_YEAR,
    FINCEN_SAR_WORKBOOKS,
    INDUSTRY_TREND_FILE,
    RAW_DATA_DIR,
    RAW_EXTRACT_FILE,
    START_YEAR,
    TN_VS_US_TREND_FILE,
)
from src.sar_loader import normalize_text, read_sheet_raw


def clean_number(value):
    """
    Convert messy numeric Excel values into floats.
    """

    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip()
    text = text.replace(",", "")
    text = text.replace("$", "")
    text = text.replace("%", "")
    text = text.replace("(", "-").replace(")", "")

    try:
        return float(text)
    except ValueError:
        return np.nan


def cell_is_year(value) -> Optional[int]:
    """
    Determine whether a cell value represents a study-window year.
    """

    if pd.isna(value):
        return None

    if isinstance(value, (int, float, np.integer, np.floating)):
        year = int(value)

        if START_YEAR <= year <= END_YEAR:
            return year

    text = str(value).strip()
    match = re.fullmatch(r"(20\d{2})", text)

    if match:
        year = int(match.group(1))

        if START_YEAR <= year <= END_YEAR:
            return year

    return None


def find_year_header_row_and_columns(df: pd.DataFrame) -> tuple[Optional[int], Dict[int, int]]:
    """
    Find the row and columns that contain annual year headers.

    Returns
    -------
    tuple
        (header_row_index, {column_index: year})
    """

    for row_idx in range(df.shape[0]):
        year_columns = {}

        for col_idx in range(df.shape[1]):
            year = cell_is_year(df.iat[row_idx, col_idx])

            if year is not None:
                year_columns[col_idx] = year

        if len(set(year_columns.values())) >= 5:
            return row_idx, year_columns

    return None, {}


def extract_annual_values_from_row(
    row: pd.Series,
    year_columns: Dict[int, int],
) -> Dict[int, float]:
    """
    Extract year-value pairs from a row using detected year columns.
    """

    values = {}

    for col_idx, year in year_columns.items():
        if col_idx < len(row):
            values[year] = clean_number(row.iloc[col_idx])

    return values


def row_text(row: pd.Series) -> str:
    """
    Normalize all cells in a row into one searchable string.
    """

    return " | ".join(normalize_text(value) for value in row.tolist())


def is_excluded_total_candidate(row: pd.Series) -> bool:
    """
    Exclude rows that should not be treated as U.S. total filing-count rows.
    """

    text = row_text(row)

    excluded_terms = [
        "subtotal",
        "sub total",
        "total by",
        "total for",
        "total amount",
        "total dollar",
        "total transactions",
        "total suspicious activity",
        "total other",
        "percentage",
        "percent",
        "pct",
        "rank",
        "ranking",
        "state",
        "territory",
        "unknown",
        "not applicable",
        "form type",
        "filing type",
        "amount",
        "dollar",
        "transaction amount",
    ]

    return any(term in text for term in excluded_terms)


def is_total_row(row: pd.Series) -> bool:
    """
    Identify a national / total filing row conservatively.

    This is used first. If no clear total row is found in Exhibit 1, the
    pipeline falls back to a numeric candidate selector.
    """

    if is_excluded_total_candidate(row):
        return False

    text = row_text(row)

    strong_total_terms = [
        "grand total",
        "total sars",
        "total filings",
        "total number of sars",
        "total number of suspicious activity reports",
        "total suspicious activity reports",
        "number of sars",
        "number of suspicious activity reports",
    ]

    if any(term in text for term in strong_total_terms):
        return True

    cells = [normalize_text(value) for value in row.tolist()]
    populated_cells = [cell for cell in cells if cell]

    if populated_cells:
        first_cell = populated_cells[0]
        if first_cell in {"total", "totals", "sar filings", "sars"}:
            return True

    return False


def annual_value_quality_score(row: pd.Series, year_columns: Dict[int, int]) -> tuple[int, float]:
    """
    Score a row based on how many annual numeric values it has and the total scale.

    Used as a fallback for Exhibit 1 when the U.S. total row is not labeled
    cleanly as 'Total'.
    """

    annual_values = extract_annual_values_from_row(row, year_columns)

    non_null_values = [
        value
        for value in annual_values.values()
        if not pd.isna(value)
    ]

    positive_values = [
        value
        for value in non_null_values
        if value >= 0
    ]

    if not positive_values:
        return 0, 0.0

    return len(positive_values), float(np.nansum(positive_values))


def find_best_us_total_row(
    df: pd.DataFrame,
    header_row: int,
    year_columns: Dict[int, int],
) -> Optional[int]:
    """
    Find the best U.S. total row in Exhibit 1.

    Priority:
    1. A clearly labeled total/SAR filing row.
    2. The strongest numeric annual row after excluding percentages, ranks,
       dollar amounts, subtotals, and metadata rows.

    This fixes workbooks where Exhibit 1 contains the U.S. annual trend row
    but does not label it with a simple 'Total' value.
    """

    exact_candidates = []

    for row_idx in range(header_row + 1, df.shape[0]):
        row = df.iloc[row_idx]

        if not is_total_row(row):
            continue

        count, total_sum = annual_value_quality_score(row, year_columns)

        if count >= 3:
            exact_candidates.append(
                {
                    "row_idx": row_idx,
                    "numeric_count": count,
                    "total_sum": total_sum,
                    "match_type": "labeled_total",
                }
            )

    if exact_candidates:
        candidates_df = pd.DataFrame(exact_candidates).sort_values(
            ["numeric_count", "total_sum"],
            ascending=[False, False],
        )

        return int(candidates_df.iloc[0]["row_idx"])

    fallback_candidates = []

    for row_idx in range(header_row + 1, df.shape[0]):
        row = df.iloc[row_idx]

        if is_excluded_total_candidate(row):
            continue

        text = row_text(row)

        if not text.strip():
            continue

        count, total_sum = annual_value_quality_score(row, year_columns)

        if count < 5:
            continue

        # Avoid rows that look like very small codes, ranks, or percentages.
        if total_sum <= 0:
            continue

        fallback_candidates.append(
            {
                "row_idx": row_idx,
                "numeric_count": count,
                "total_sum": total_sum,
                "row_text": text[:160],
                "match_type": "numeric_fallback",
            }
        )

    if not fallback_candidates:
        return None

    candidates_df = pd.DataFrame(fallback_candidates).sort_values(
        ["numeric_count", "total_sum"],
        ascending=[False, False],
    )

    selected = candidates_df.iloc[0]

    print(
        "  Exhibit 1 total row selected by numeric fallback: "
        f"row {int(selected['row_idx'])}"
    )

    return int(selected["row_idx"])


def is_tennessee_row(row: pd.Series) -> bool:
    """
    Identify Tennessee state rows.
    """

    cells = [normalize_text(value) for value in row.tolist()]
    return any(cell == "tennessee" for cell in cells)


def extract_rows_from_specific_sheet(
    df: pd.DataFrame,
    workbook_key: str,
    industry_name: str,
    sheet_name: str,
    target_geo: str,
) -> List[dict]:
    """
    Extract annual values from a specific sheet.

    Method:
    - Exhibit 1 is treated as industry-level U.S. total.
    - Exhibit 2 is treated as state-level ranking / state totals.
    """

    rows = []

    header_row, year_columns = find_year_header_row_and_columns(df)

    if header_row is None or not year_columns:
        print(f"No year header found: {industry_name} / {sheet_name}")
        return rows

    if target_geo == "United States / Total":
        selected_row_idx = find_best_us_total_row(
            df=df,
            header_row=header_row,
            year_columns=year_columns,
        )

        if selected_row_idx is None:
            print(f"  No U.S. total row found: {industry_name} / {sheet_name}")
            return rows

        candidate_rows = [(selected_row_idx, df.iloc[selected_row_idx])]

    elif target_geo == "Tennessee":
        candidate_rows = []

        for row_idx in range(header_row + 1, df.shape[0]):
            row = df.iloc[row_idx]

            if is_tennessee_row(row):
                candidate_rows.append((row_idx, row))

    else:
        return rows

    for row_idx, row in candidate_rows:
        annual_values = extract_annual_values_from_row(row, year_columns)

        non_null_values = {
            year: value
            for year, value in annual_values.items()
            if not pd.isna(value)
        }

        if len(non_null_values) < 3:
            continue

        for year, value in non_null_values.items():
            rows.append(
                {
                    "workbook_key": workbook_key,
                    "industry_name": industry_name,
                    "sheet_name": sheet_name,
                    "row_index": row_idx,
                    "geo_label": target_geo,
                    "year": int(year),
                    "sar_filings": float(value),
                    "source_scope": (
                        "FinCEN SAR Stats Exhibit 1 U.S. total row"
                        if target_geo == "United States / Total"
                        else "FinCEN SAR Stats Exhibit 2 Tennessee state row"
                    ),
                    "methodology_note": (
                        "Extracted from public FinCEN SAR Stats workbook tables. "
                        "SAR filings measure reporting activity, not confirmed criminal activity."
                    ),
                }
            )

        if target_geo == "United States / Total":
            break

    return rows


def validate_extracted_rows(extracted: pd.DataFrame) -> pd.DataFrame:
    """
    Build simple data-quality checks for extracted SAR rows.

    The checks are printed to the console and returned as a dataframe.
    """

    if extracted.empty:
        return pd.DataFrame()

    checks = []

    expected_years = set(range(START_YEAR, END_YEAR + 1))

    for (industry, geo_label), group in extracted.groupby(["industry_name", "geo_label"]):
        observed_years = set(group["year"].dropna().astype(int).tolist())
        missing_years = sorted(expected_years - observed_years)

        duplicate_count = group.duplicated(
            subset=["industry_name", "geo_label", "year"],
            keep=False,
        ).sum()

        checks.append(
            {
                "industry_name": industry,
                "geo_label": geo_label,
                "observed_year_count": len(observed_years),
                "missing_years": ", ".join(str(year) for year in missing_years),
                "duplicate_year_rows": int(duplicate_count),
                "status": (
                    "review"
                    if missing_years or duplicate_count > 0
                    else "ok"
                ),
            }
        )

    checks_df = pd.DataFrame(checks)

    review_rows = checks_df[checks_df["status"].eq("review")]

    if not review_rows.empty:
        print("\nSAR extraction data-quality checks flagged rows for review:")
        print(review_rows)
    else:
        print("SAR extraction data-quality checks passed.")

    return checks_df


def extract_sar_rows_from_workbooks() -> pd.DataFrame:
    """
    Extract clean annual industry-level SAR rows.

    Uses:
    - Exhibit 1 for U.S. / total industry filings
    - Exhibit 2 for Tennessee state industry filings
    """

    all_rows = []

    for workbook_key, meta in FINCEN_SAR_WORKBOOKS.items():
        workbook_path = RAW_DATA_DIR / meta["filename"]

        if not workbook_path.exists():
            print(f"Missing workbook, skipping: {workbook_path}")
            continue

        print(f"Processing workbook: {meta['industry_name']}")

        try:
            excel_file = pd.ExcelFile(workbook_path, engine="openpyxl")
        except Exception as exc:
            print(f"Could not open workbook {workbook_path}: {exc}")
            continue

        available_sheets = set(excel_file.sheet_names)

        if "Exhibit 1" in available_sheets:
            try:
                df = read_sheet_raw(workbook_path, "Exhibit 1")

                rows = extract_rows_from_specific_sheet(
                    df=df,
                    workbook_key=workbook_key,
                    industry_name=meta["industry_name"],
                    sheet_name="Exhibit 1",
                    target_geo="United States / Total",
                )

                all_rows.extend(rows)
                print(f"  Exhibit 1 rows extracted: {len(rows)}")

            except Exception as exc:
                print(f"Could not process Exhibit 1 for {meta['industry_name']}: {exc}")

        else:
            print(f"  Exhibit 1 not found for {meta['industry_name']}")

        if "Exhibit 2" in available_sheets:
            try:
                df = read_sheet_raw(workbook_path, "Exhibit 2")

                rows = extract_rows_from_specific_sheet(
                    df=df,
                    workbook_key=workbook_key,
                    industry_name=meta["industry_name"],
                    sheet_name="Exhibit 2",
                    target_geo="Tennessee",
                )

                all_rows.extend(rows)
                print(f"  Exhibit 2 Tennessee rows extracted: {len(rows)}")

            except Exception as exc:
                print(f"Could not process Exhibit 2 for {meta['industry_name']}: {exc}")

        else:
            print(f"  Exhibit 2 not found for {meta['industry_name']}")

    extracted = pd.DataFrame(all_rows)

    if extracted.empty:
        print("No candidate rows were extracted.")
        return extracted

    extracted = extracted.drop_duplicates(
        subset=[
            "workbook_key",
            "industry_name",
            "sheet_name",
            "geo_label",
            "year",
            "sar_filings",
        ]
    )

    extracted = extracted.sort_values(
        ["industry_name", "geo_label", "year"]
    )

    validate_extracted_rows(extracted)

    extracted.to_csv(RAW_EXTRACT_FILE, index=False)
    print(f"Raw extracted SAR rows saved to: {RAW_EXTRACT_FILE}")
    print(f"Raw extracted SAR rows shape: {extracted.shape}")

    return extracted


def build_industry_trend_table(extracted: pd.DataFrame) -> pd.DataFrame:
    """
    Build Tennessee SAR filings by industry and year.
    """

    if extracted.empty:
        return pd.DataFrame()

    tn_rows = extracted[extracted["geo_label"].eq("Tennessee")].copy()

    if tn_rows.empty:
        print("No Tennessee rows found in extracted data.")
        return pd.DataFrame()

    industry_trend = (
        tn_rows.groupby(["industry_name", "year"], as_index=False)["sar_filings"]
        .sum()
        .sort_values(["industry_name", "year"])
    )

    industry_trend["yoy_growth"] = industry_trend.groupby("industry_name")[
        "sar_filings"
    ].pct_change()

    industry_trend["total_tn_filings_year"] = industry_trend.groupby("year")[
        "sar_filings"
    ].transform("sum")

    industry_trend["industry_share_of_tn_filings"] = np.where(
        industry_trend["total_tn_filings_year"] > 0,
        industry_trend["sar_filings"] / industry_trend["total_tn_filings_year"],
        np.nan,
    )

    industry_trend["latest_year_share"] = industry_trend["industry_share_of_tn_filings"]

    industry_trend["data_basis"] = "FinCEN SAR Stats Exhibit 2 Tennessee industry-level rows"
    industry_trend["methodology_note"] = (
        "Industry trend measures Tennessee SAR filing activity by filing industry. "
        "It does not measure confirmed financial crime."
    )

    industry_trend.to_csv(INDUSTRY_TREND_FILE, index=False)
    print(f"Industry trend table saved to: {INDUSTRY_TREND_FILE}")
    print(f"Industry trend shape: {industry_trend.shape}")

    return industry_trend


def get_first_valid_value(df: pd.DataFrame, column: str):
    """
    Return the first valid value in a dataframe column.
    """

    if column not in df.columns:
        return np.nan

    values = df[column].dropna()

    if values.empty:
        return np.nan

    return values.iloc[0]


def build_tn_vs_us_trend_table(extracted: pd.DataFrame) -> pd.DataFrame:
    """
    Build annual Tennessee vs U.S. trend table using clean industry-level rows.
    """

    if extracted.empty:
        return pd.DataFrame()

    grouped = (
        extracted.groupby(["geo_label", "year"], as_index=False)["sar_filings"]
        .sum()
        .sort_values(["geo_label", "year"])
    )

    pivot = grouped.pivot_table(
        index="year",
        columns="geo_label",
        values="sar_filings",
        aggfunc="sum",
    ).reset_index()

    pivot = pivot.sort_values("year").copy()

    if "Tennessee" in pivot.columns:
        pivot["tn_yoy_growth"] = pivot["Tennessee"].pct_change()

    if "United States / Total" in pivot.columns:
        pivot["us_yoy_growth"] = pivot["United States / Total"].pct_change()

    if "Tennessee" in pivot.columns and "United States / Total" in pivot.columns:
        pivot["tn_share_of_total"] = np.where(
            pivot["United States / Total"] > 0,
            pivot["Tennessee"] / pivot["United States / Total"],
            np.nan,
        )

        base_tn = get_first_valid_value(pivot, "Tennessee")
        base_us = get_first_valid_value(pivot, "United States / Total")

        if not pd.isna(base_tn) and base_tn > 0:
            pivot["tn_index_2014_100"] = pivot["Tennessee"] / base_tn * 100
        else:
            pivot["tn_index_2014_100"] = np.nan

        if not pd.isna(base_us) and base_us > 0:
            pivot["us_index_2014_100"] = pivot["United States / Total"] / base_us * 100
        else:
            pivot["us_index_2014_100"] = np.nan

        pivot["tn_minus_us_index_gap"] = (
            pivot["tn_index_2014_100"] - pivot["us_index_2014_100"]
        )

    pivot["data_basis"] = (
        "FinCEN SAR Stats Exhibit 1 U.S. total rows and Exhibit 2 Tennessee state rows"
    )
    pivot["methodology_note"] = (
        "Tennessee and U.S. totals are aggregated across extracted filing-industry workbooks. "
        "Indexed trend uses the first available study year as the base."
    )

    pivot.to_csv(TN_VS_US_TREND_FILE, index=False)
    print(f"Tennessee vs U.S. trend table saved to: {TN_VS_US_TREND_FILE}")
    print(f"Tennessee vs U.S. trend shape: {pivot.shape}")

    return pivot


def run_sar_processing_pipeline() -> dict:
    """
    Run the SAR processing pipeline.
    """

    extracted = extract_sar_rows_from_workbooks()

    if extracted.empty:
        return {
            "extracted": extracted,
            "industry_trend": pd.DataFrame(),
            "tn_vs_us_trend": pd.DataFrame(),
        }

    industry_trend = build_industry_trend_table(extracted)
    tn_vs_us_trend = build_tn_vs_us_trend_table(extracted)

    return {
        "extracted": extracted,
        "industry_trend": industry_trend,
        "tn_vs_us_trend": tn_vs_us_trend,
    }