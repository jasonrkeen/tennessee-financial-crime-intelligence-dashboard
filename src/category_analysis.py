import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.config import (
    FINCEN_SAR_WORKBOOKS,
    RAW_DATA_DIR,
    TABLES_DIR,
)
from src.sar_loader import normalize_text, read_sheet_raw
from src.sar_processing import clean_number, cell_is_year


CATEGORY_DETAIL_FILE = TABLES_DIR / "suspicious_activity_category_detail.csv"
CATEGORY_SUMMARY_FILE = TABLES_DIR / "suspicious_activity_category_summary.csv"
TOP_CATEGORIES_LATEST_FILE = TABLES_DIR / "top_suspicious_activity_categories_latest_year.csv"
HIGH_RISK_CATEGORIES_FILE = TABLES_DIR / "high_risk_suspicious_activity_categories.csv"


HIGH_RISK_KEYWORDS = [
    "fraud",
    "elder",
    "elder financial exploitation",
    "cyber",
    "money laundering",
    "structuring",
    "terrorist",
    "terrorism",
    "human trafficking",
    "human smuggling",
    "identity theft",
    "wire transfer",
    "wire",
    "check fraud",
    "credit card fraud",
    "debit card fraud",
    "source of funds",
    "no apparent",
    "money mule",
    "cash",
    "virtual currency",
    "cryptocurrency",
    "digital asset",
    "shell",
    "ctr threshold",
    "bribery",
    "corruption",
    "tax evasion",
    "account takeover",
    "sanctions",
    "ofac",
    "sanctioned",
    "proliferation",
    "foreign",
    "domestic corruption",
]


SUSPICIOUS_ACTIVITY_TERMS = [
    "fraud",
    "money laundering",
    "structuring",
    "terrorist",
    "terrorism",
    "cyber",
    "elder",
    "elder financial exploitation",
    "human trafficking",
    "human smuggling",
    "identity theft",
    "suspicion concerning",
    "source of funds",
    "no apparent",
    "suspicious eft",
    "wire transfer",
    "wire transfers",
    "transaction(s) below ctr threshold",
    "below ctr threshold",
    "bribery",
    "corruption",
    "money mule",
    "shell",
    "virtual currency",
    "cryptocurrency",
    "digital asset",
    "check fraud",
    "credit card fraud",
    "debit card fraud",
    "account takeover",
    "tax evasion",
    "sanctions",
    "ofac",
    "sanctioned",
    "proliferation",
]


# Exact labels to exclude. Avoid broad startswith logic for terms such as
# "credit card" or "check" because those can appear inside valid fraud categories.
EXCLUDE_EXACT_TERMS = [
    "subtotal",
    "total",
    "grand total",
    "customer",
    "u.s. currency",
    "us currency",
    "currency",
    "debit card",
    "credit card",
    "personal/business check",
    "personal check",
    "business check",
    "check",
    "funds transfer",
    "ach",
    "money order",
    "traveler",
    "cashier",
    "no relationship to institution",
    "relationship to institution",
    "comptroller of the currency",
    "federal reserve board",
    "federal deposit insurance corporation",
    "national credit union administration",
    "internal revenue service",
    "filing institution",
    "state",
    "territory",
    "rank",
    "unknown",
    "other",
]


EXCLUDE_PREFIX_TERMS = [
    "subtotal",
    "total by",
    "total for",
    "grand total",
    "rank",
]


CATEGORY_RENAME_MAP = {
    "Suspicion concerning the source of funds": "Source of Funds Concerns",
    "Transaction with no apparent economic, business, or lawful purpose": "No Apparent Economic, Business, or Lawful Purpose",
    "Transaction(s) below CTR threshold": "Transactions Below CTR Threshold",
    "Suspicious EFT/wire transfers": "Suspicious EFT / Wire Transfers",
    "Identity theft": "Identity Theft",
    "Elder financial exploitation": "Elder Financial Exploitation",
    "Cyber event": "Cyber Event",
    "Money laundering": "Money Laundering",
    "Structuring": "Structuring",
    "Bribery or gratuity": "Bribery or Gratuity",
    "Suspected public/private corruption (domestic)": "Suspected Public/Private Corruption (Domestic)",
    "Suspected public/private corruption (foreign)": "Suspected Public/Private Corruption (Foreign)",
    "Known or suspected terrorist/terrorist organization": "Known or Suspected Terrorist / Terrorist Organization",
    "Trade Based Money Laundering/Black Market Peso Exchange": "Trade-Based Money Laundering / Black Market Peso Exchange",
    "Suspicious EFT/wire transfers": "Suspicious EFT / Wire Transfers",
    "Credit card fraud": "Credit Card Fraud",
    "Debit card fraud": "Debit Card Fraud",
    "Check fraud": "Check Fraud",
}


def row_text(row: pd.Series) -> str:
    """
    Normalize a full spreadsheet row into searchable text.
    """

    return " | ".join(normalize_text(value) for value in row.tolist())


def find_year_header_row_and_columns(df: pd.DataFrame) -> tuple[Optional[int], Dict[int, int]]:
    """
    Find the row and columns that contain annual year headers.
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


def find_label_column(df: pd.DataFrame, header_row: int, year_columns: Dict[int, int]) -> int:
    """
    Infer the label column.

    Usually this is the populated text column immediately before the first year column.
    """

    first_year_col = min(year_columns.keys())
    candidate_cols = list(range(max(0, first_year_col - 5), first_year_col))

    best_col = 0
    best_score = -1

    for col_idx in candidate_cols:
        score = 0

        for row_idx in range(header_row + 1, min(df.shape[0], header_row + 50)):
            value = normalize_text(df.iat[row_idx, col_idx])

            if value:
                score += 1

        if score > best_score:
            best_score = score
            best_col = col_idx

    return best_col


def clean_category_label(value) -> str:
    """
    Clean and standardize category labels.
    """

    if pd.isna(value):
        return ""

    text = str(value).strip()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip(":- ")

    return CATEGORY_RENAME_MAP.get(text, text)


def contains_any(text: str, terms: list[str]) -> bool:
    """
    Return True when text contains any term.
    """

    lowered = text.lower()
    return any(term in lowered for term in terms)


def is_excluded_label(label: str) -> bool:
    """
    Exclude rows that are totals, payment instruments, metadata, or non-category labels.

    Important:
    This function avoids excluding valid fraud categories such as Credit Card Fraud
    or Check Fraud simply because they start with payment-instrument words.
    """

    lowered = label.lower().strip()

    if not lowered:
        return True

    if len(lowered) <= 2:
        return True

    if re.fullmatch(r"\d+", lowered):
        return True

    if lowered in EXCLUDE_EXACT_TERMS:
        return True

    if any(lowered.startswith(term) for term in EXCLUDE_PREFIX_TERMS):
        return True

    return False


def is_probable_suspicious_activity_category(label: str) -> bool:
    """
    Keep only labels that look like suspicious activity / financial crime categories.
    """

    if is_excluded_label(label):
        return False

    return contains_any(label, SUSPICIOUS_ACTIVITY_TERMS)


def classify_high_risk_category(category: str) -> bool:
    """
    Classify a category as high-risk based on AML, fraud, sanctions,
    corruption, terrorist-financing, exploitation, and cyber-related terms.
    """

    return contains_any(category, HIGH_RISK_KEYWORDS)


def classify_category_theme(category: str) -> str:
    """
    Classify suspicious activity category into a broader intelligence theme.
    """

    lowered = str(category).lower()

    if any(term in lowered for term in ["terrorist", "terrorism"]):
        return "Terrorist Financing / National Security"

    if any(term in lowered for term in ["sanctions", "ofac", "sanctioned", "proliferation"]):
        return "Sanctions / Proliferation Finance"

    if any(term in lowered for term in ["bribery", "corruption"]):
        return "Corruption / Bribery"

    if any(term in lowered for term in ["human trafficking", "human smuggling"]):
        return "Human Trafficking / Exploitation"

    if any(term in lowered for term in ["elder"]):
        return "Elder Financial Exploitation"

    if any(term in lowered for term in ["identity theft", "account takeover"]):
        return "Identity Theft / Account Takeover"

    if any(term in lowered for term in ["cyber", "virtual currency", "cryptocurrency", "digital asset"]):
        return "Cyber / Digital Assets"

    if any(term in lowered for term in ["wire", "eft", "funds transfer"]):
        return "Payments / Wire Activity"

    if any(term in lowered for term in ["money laundering", "structuring", "ctr threshold", "source of funds", "no apparent"]):
        return "AML / Source-of-Funds / Structuring"

    if "fraud" in lowered:
        return "Fraud"

    return "Other Suspicious Activity Context"


def classify_category_risk_tier(category: str, high_risk_flag: bool) -> str:
    """
    Assign a broad risk tier for report readability.
    """

    theme = classify_category_theme(category)

    elevated_themes = {
        "Terrorist Financing / National Security",
        "Sanctions / Proliferation Finance",
        "Human Trafficking / Exploitation",
        "Corruption / Bribery",
        "Elder Financial Exploitation",
        "Identity Theft / Account Takeover",
    }

    if theme in elevated_themes:
        return "Elevated Context"

    if high_risk_flag:
        return "High-Risk Context"

    return "General Context"


def extract_category_rows_from_sheet(
    df: pd.DataFrame,
    workbook_key: str,
    industry_name: str,
    sheet_name: str,
) -> List[dict]:
    """
    Extract suspicious activity category rows from one exhibit.
    """

    rows = []

    header_row, year_columns = find_year_header_row_and_columns(df)

    if header_row is None or not year_columns:
        return rows

    label_col = find_label_column(df, header_row, year_columns)

    for row_idx in range(header_row + 1, df.shape[0]):
        row = df.iloc[row_idx]
        category = clean_category_label(row.iloc[label_col])

        if not is_probable_suspicious_activity_category(category):
            continue

        annual_values = {}

        for col_idx, year in year_columns.items():
            if col_idx < len(row):
                value = clean_number(row.iloc[col_idx])

                if not pd.isna(value):
                    annual_values[year] = value

        if len(annual_values) < 3:
            continue

        high_risk_flag = classify_high_risk_category(category)
        category_theme = classify_category_theme(category)
        risk_tier = classify_category_risk_tier(category, high_risk_flag)

        for year, value in annual_values.items():
            rows.append(
                {
                    "workbook_key": workbook_key,
                    "industry_name": industry_name,
                    "sheet_name": sheet_name,
                    "row_index": row_idx,
                    "category": category,
                    "category_theme": category_theme,
                    "risk_tier": risk_tier,
                    "year": int(year),
                    "sar_filings": float(value),
                    "high_risk_flag": high_risk_flag,
                    "source_scope": "FinCEN SAR Stats industry/category exhibit",
                    "methodology_note": (
                        "Suspicious activity category exhibits are treated as industry-level / national "
                        "SAR context unless the source workbook explicitly provides a Tennessee-specific "
                        "category breakdown."
                    ),
                }
            )

    return rows


def extract_category_detail() -> pd.DataFrame:
    """
    Extract suspicious activity category details from category-oriented exhibits.

    Note:
    These category exhibits are treated as industry-level / national context,
    not Tennessee-specific category counts.
    """

    all_rows = []

    for workbook_key, meta in FINCEN_SAR_WORKBOOKS.items():
        workbook_path = RAW_DATA_DIR / meta["filename"]

        if not workbook_path.exists():
            print(f"Missing workbook, skipping category extraction: {workbook_path}")
            continue

        print(f"Extracting suspicious activity categories from: {meta['industry_name']}")

        try:
            excel_file = pd.ExcelFile(workbook_path, engine="openpyxl")
        except Exception as exc:
            print(f"Could not open workbook {workbook_path}: {exc}")
            continue

        for sheet_name in excel_file.sheet_names:
            if sheet_name in {"Exhibit 1", "Exhibit 2"}:
                continue

            try:
                df = read_sheet_raw(workbook_path, sheet_name)

                rows = extract_category_rows_from_sheet(
                    df=df,
                    workbook_key=workbook_key,
                    industry_name=meta["industry_name"],
                    sheet_name=sheet_name,
                )

                all_rows.extend(rows)

            except Exception as exc:
                print(
                    f"Could not process category sheet "
                    f"{meta['industry_name']} / {sheet_name}: {exc}"
                )

    detail = pd.DataFrame(all_rows)

    if detail.empty:
        print("No suspicious activity category rows extracted.")
        return detail

    detail = detail.sort_values(
        ["industry_name", "sheet_name", "category", "year"]
    )

    detail.to_csv(CATEGORY_DETAIL_FILE, index=False)
    print(f"Suspicious activity category detail saved to: {CATEGORY_DETAIL_FILE}")

    return detail


def summarize_categories(category_detail: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize suspicious activity categories across industries and years.
    """

    if category_detail.empty:
        return pd.DataFrame()

    grouped = (
        category_detail.groupby(
            ["category", "category_theme", "risk_tier", "year"],
            as_index=False,
        )
        .agg(
            sar_filings=("sar_filings", "sum"),
            high_risk_flag=("high_risk_flag", "max"),
            industries=("industry_name", lambda x: ", ".join(sorted(set(x)))),
            source_sheets=("sheet_name", lambda x: ", ".join(sorted(set(x)))),
        )
        .sort_values(["category", "year"])
    )

    start_year = int(grouped["year"].min())
    end_year = int(grouped["year"].max())
    periods = end_year - start_year

    rows = []

    for category, group in grouped.groupby("category"):
        group = group.sort_values("year")

        start_candidates = group[group["year"].eq(start_year)]
        end_candidates = group[group["year"].eq(end_year)]

        if start_candidates.empty or end_candidates.empty:
            continue

        start_value = start_candidates["sar_filings"].iloc[0]
        end_value = end_candidates["sar_filings"].iloc[0]

        if start_value > 0 and end_value > 0 and periods > 0:
            cagr = (end_value / start_value) ** (1 / periods) - 1
            total_growth_pct = (end_value - start_value) / start_value
        else:
            cagr = np.nan
            total_growth_pct = np.nan

        category_theme = group["category_theme"].iloc[-1]
        high_risk_flag = bool(group["high_risk_flag"].max())
        risk_tier = classify_category_risk_tier(category, high_risk_flag)

        rows.append(
            {
                "category": category,
                "category_theme": category_theme,
                "risk_tier": risk_tier,
                "start_year": start_year,
                "end_year": end_year,
                "start_filings": start_value,
                "end_filings": end_value,
                "absolute_change": end_value - start_value,
                "total_growth_pct": total_growth_pct,
                "cagr": cagr,
                "peak_year": int(group.loc[group["sar_filings"].idxmax(), "year"]),
                "peak_filings": group["sar_filings"].max(),
                "high_risk_flag": high_risk_flag,
                "industries": group["industries"].iloc[-1],
                "source_sheets": group["source_sheets"].iloc[-1],
                "source_scope": "FinCEN SAR Stats industry/category exhibit",
                "methodology_note": (
                    "Category counts are used as SAR-theme intelligence context. "
                    "They should not be interpreted as Tennessee-specific category counts "
                    "unless explicitly supported by the source data."
                ),
            }
        )

    summary = pd.DataFrame(rows)

    if not summary.empty:
        summary = summary.sort_values(
            ["end_filings", "absolute_change"],
            ascending=[False, False],
        )

    summary.to_csv(CATEGORY_SUMMARY_FILE, index=False)
    print(f"Suspicious activity category summary saved to: {CATEGORY_SUMMARY_FILE}")

    return summary


def save_top_categories_latest_year(
    category_summary: pd.DataFrame,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Save top suspicious activity categories by latest-year filings.
    """

    if category_summary.empty:
        return pd.DataFrame()

    latest = category_summary.sort_values("end_filings", ascending=False).head(top_n)
    latest.to_csv(TOP_CATEGORIES_LATEST_FILE, index=False)

    print(f"Top suspicious activity categories saved to: {TOP_CATEGORIES_LATEST_FILE}")

    return latest


def save_high_risk_categories(
    category_summary: pd.DataFrame,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Save elevated and high-risk suspicious activity categories.

    Supports both the newer risk_tier field and the older high_risk_flag field.
    """

    if category_summary.empty:
        return pd.DataFrame()

    if "risk_tier" in category_summary.columns:
        high_risk = category_summary[
            category_summary["risk_tier"]
            .astype(str)
            .isin(["Elevated Context", "High-Risk Context"])
        ].copy()
    elif "high_risk_flag" in category_summary.columns:
        high_risk = category_summary[
            category_summary["high_risk_flag"].eq(True)
        ].copy()
    else:
        return pd.DataFrame()

    high_risk = high_risk.sort_values(
        ["end_filings", "absolute_change"],
        ascending=[False, False],
    ).head(top_n)

    high_risk.to_csv(HIGH_RISK_CATEGORIES_FILE, index=False)
    print(f"High-risk suspicious activity categories saved to: {HIGH_RISK_CATEGORIES_FILE}")

    return high_risk


def run_category_analysis() -> dict:
    """
    Run full suspicious activity category analysis pipeline.
    """

    category_detail = extract_category_detail()
    category_summary = summarize_categories(category_detail)
    top_categories = save_top_categories_latest_year(category_summary)
    high_risk_categories = save_high_risk_categories(category_summary)

    return {
        "category_detail": category_detail,
        "category_summary": category_summary,
        "top_categories": top_categories,
        "high_risk_categories": high_risk_categories,
    }