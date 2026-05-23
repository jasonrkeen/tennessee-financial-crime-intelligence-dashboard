import numpy as np
import pandas as pd

from src.config import PROJECT_TITLE, TABLES_DIR


TREND_SUMMARY_FILE = TABLES_DIR / "trend_summary.csv"
INDUSTRY_SUMMARY_FILE = TABLES_DIR / "industry_summary.csv"
KEY_FINDINGS_FILE = TABLES_DIR / "key_findings.txt"


def safe_pct_change(start_value: float, end_value: float) -> float:
    """
    Calculate percentage change safely.
    """

    if pd.isna(start_value) or pd.isna(end_value) or start_value == 0:
        return np.nan

    return (end_value - start_value) / start_value


def safe_cagr(start_value: float, end_value: float, periods: int) -> float:
    """
    Calculate compound annual growth rate safely.
    """

    if (
        pd.isna(start_value)
        or pd.isna(end_value)
        or start_value <= 0
        or end_value <= 0
        or periods <= 0
    ):
        return np.nan

    return (end_value / start_value) ** (1 / periods) - 1


def format_pct(value: float) -> str:
    """
    Format decimals as percentages.
    """

    if pd.isna(value):
        return "N/A"

    return f"{value * 100:,.1f}%"


def format_number(value: float) -> str:
    """
    Format numeric values.
    """

    if pd.isna(value):
        return "N/A"

    return f"{float(value):,.0f}"


def format_index_gap(value: float) -> str:
    """
    Format index gap values.
    """

    if pd.isna(value):
        return "N/A"

    direction = "above" if value > 0 else "below" if value < 0 else "equal to"
    return f"{abs(value):,.1f} points {direction}"


def summarize_trend(tn_vs_us: pd.DataFrame) -> pd.DataFrame:
    """
    Create a high-level Tennessee vs U.S. trend summary.
    """

    if tn_vs_us.empty:
        summary = pd.DataFrame()
        summary.to_csv(TREND_SUMMARY_FILE, index=False)
        return summary

    df = tn_vs_us.sort_values("year").copy()

    start_year = int(df["year"].min())
    end_year = int(df["year"].max())
    periods = end_year - start_year

    start_row = df[df["year"].eq(start_year)].iloc[0]
    end_row = df[df["year"].eq(end_year)].iloc[0]

    rows = []

    if "Tennessee" in df.columns:
        tn_start = start_row["Tennessee"]
        tn_end = end_row["Tennessee"]

        latest_yoy = (
            end_row.get("tn_yoy_growth", np.nan)
            if "tn_yoy_growth" in df.columns
            else np.nan
        )

        latest_share = (
            end_row.get("tn_share_of_total", np.nan)
            if "tn_share_of_total" in df.columns
            else np.nan
        )

        rows.append(
            {
                "metric": "Tennessee SAR filings",
                "start_year": start_year,
                "end_year": end_year,
                "start_value": tn_start,
                "end_value": tn_end,
                "absolute_change": tn_end - tn_start,
                "total_growth_pct": safe_pct_change(tn_start, tn_end),
                "cagr": safe_cagr(tn_start, tn_end, periods),
                "latest_yoy_growth": latest_yoy,
                "latest_share_of_us_total": latest_share,
                "peak_year": int(df.loc[df["Tennessee"].idxmax(), "year"]),
                "peak_value": df["Tennessee"].max(),
                "data_basis": "FinCEN SAR Stats Exhibit 2 Tennessee annual state rows",
                "source_scope": "Tennessee state-level SAR filing trend",
                "methodology_note": (
                    "Tennessee trend is based on extracted state-level SAR filing rows "
                    "from public FinCEN SAR Stats industry workbooks. SAR filing counts "
                    "measure reporting activity, not confirmed financial crime."
                ),
            }
        )

    if "United States / Total" in df.columns:
        us_start = start_row["United States / Total"]
        us_end = end_row["United States / Total"]

        latest_yoy = (
            end_row.get("us_yoy_growth", np.nan)
            if "us_yoy_growth" in df.columns
            else np.nan
        )

        rows.append(
            {
                "metric": "United States SAR filings",
                "start_year": start_year,
                "end_year": end_year,
                "start_value": us_start,
                "end_value": us_end,
                "absolute_change": us_end - us_start,
                "total_growth_pct": safe_pct_change(us_start, us_end),
                "cagr": safe_cagr(us_start, us_end, periods),
                "latest_yoy_growth": latest_yoy,
                "latest_share_of_us_total": np.nan,
                "peak_year": int(df.loc[df["United States / Total"].idxmax(), "year"]),
                "peak_value": df["United States / Total"].max(),
                "data_basis": "FinCEN SAR Stats Exhibit 1 U.S. / industry total rows",
                "source_scope": "U.S. total SAR filing trend",
                "methodology_note": (
                    "U.S. trend is based on extracted total SAR filing rows from "
                    "public FinCEN SAR Stats industry workbooks. SAR filing counts "
                    "measure reporting activity, not confirmed financial crime."
                ),
            }
        )

    if "tn_minus_us_index_gap" in df.columns:
        latest_gap = end_row["tn_minus_us_index_gap"]

        rows.append(
            {
                "metric": "Tennessee minus U.S. SAR index gap",
                "start_year": start_year,
                "end_year": end_year,
                "start_value": 0,
                "end_value": latest_gap,
                "absolute_change": latest_gap,
                "total_growth_pct": np.nan,
                "cagr": np.nan,
                "latest_yoy_growth": np.nan,
                "latest_share_of_us_total": np.nan,
                "peak_year": int(df.loc[df["tn_minus_us_index_gap"].idxmax(), "year"]),
                "peak_value": df["tn_minus_us_index_gap"].max(),
                "data_basis": "Indexed Tennessee and U.S. SAR trend comparison",
                "source_scope": "Tennessee-vs-U.S. indexed SAR trend comparison",
                "methodology_note": (
                    "Index gap compares Tennessee indexed SAR growth against U.S. indexed SAR growth, "
                    "using the first available study year as the common base. A negative gap means "
                    "Tennessee grew more slowly than the U.S. indexed trend."
                ),
            }
        )

    summary = pd.DataFrame(rows)
    summary.to_csv(TREND_SUMMARY_FILE, index=False)

    print(f"Trend summary saved to: {TREND_SUMMARY_FILE}")
    return summary


def summarize_industries(industry_trend: pd.DataFrame) -> pd.DataFrame:
    """
    Create an industry-level SAR trend summary for Tennessee.
    """

    if industry_trend.empty:
        summary = pd.DataFrame()
        summary.to_csv(INDUSTRY_SUMMARY_FILE, index=False)
        return summary

    df = industry_trend.sort_values(["industry_name", "year"]).copy()

    start_year = int(df["year"].min())
    end_year = int(df["year"].max())
    periods = end_year - start_year

    rows = []

    latest_total = df[df["year"].eq(end_year)]["sar_filings"].sum()

    for industry, group in df.groupby("industry_name"):
        group = group.sort_values("year")

        start_candidates = group[group["year"].eq(start_year)]
        end_candidates = group[group["year"].eq(end_year)]

        if start_candidates.empty or end_candidates.empty:
            continue

        start_value = start_candidates["sar_filings"].iloc[0]
        end_value = end_candidates["sar_filings"].iloc[0]

        latest_yoy = (
            end_candidates["yoy_growth"].iloc[0]
            if "yoy_growth" in end_candidates.columns
            else np.nan
        )

        if "industry_share_of_tn_filings" in end_candidates.columns:
            latest_share = end_candidates["industry_share_of_tn_filings"].iloc[0]
        elif "latest_year_share" in end_candidates.columns:
            latest_share = end_candidates["latest_year_share"].iloc[0]
        elif latest_total and latest_total > 0:
            latest_share = end_value / latest_total
        else:
            latest_share = np.nan

        rows.append(
            {
                "industry_name": industry,
                "start_year": start_year,
                "end_year": end_year,
                "start_filings": start_value,
                "end_filings": end_value,
                "absolute_change": end_value - start_value,
                "total_growth_pct": safe_pct_change(start_value, end_value),
                "cagr": safe_cagr(start_value, end_value, periods),
                "latest_yoy_growth": latest_yoy,
                "peak_year": int(group.loc[group["sar_filings"].idxmax(), "year"]),
                "peak_filings": group["sar_filings"].max(),
                "latest_year_share": latest_share,
                "industry_share_of_tn_filings": latest_share,
                "data_basis": "FinCEN SAR Stats Exhibit 2 Tennessee industry-level rows",
                "source_scope": "Tennessee SAR filing industry trend",
                "methodology_note": (
                    "Industry summary uses extracted Tennessee rows by SAR filing industry. "
                    "These rows measure SAR filing activity and reporting-channel concentration, "
                    "not confirmed financial crime."
                ),
            }
        )

    summary = pd.DataFrame(rows)

    if not summary.empty:
        summary = summary.sort_values(
            ["end_filings", "absolute_change"],
            ascending=[False, False],
        )

    summary.to_csv(INDUSTRY_SUMMARY_FILE, index=False)

    print(f"Industry summary saved to: {INDUSTRY_SUMMARY_FILE}")
    return summary


def generate_key_findings(
    trend_summary: pd.DataFrame,
    industry_summary: pd.DataFrame,
    tn_vs_us: pd.DataFrame,
) -> list[str]:
    """
    Generate plain-English intelligence findings.
    """

    findings = []

    if not trend_summary.empty:
        tn_row = trend_summary[
            trend_summary["metric"].eq("Tennessee SAR filings")
        ]

        us_row = trend_summary[
            trend_summary["metric"].eq("United States SAR filings")
        ]

        gap_row = trend_summary[
            trend_summary["metric"].eq("Tennessee minus U.S. SAR index gap")
        ]

        if not tn_row.empty:
            row = tn_row.iloc[0]

            findings.append(
                "Tennessee SAR filings increased from "
                f"{format_number(row['start_value'])} in {int(row['start_year'])} "
                f"to {format_number(row['end_value'])} in {int(row['end_year'])}, "
                f"a total increase of {format_pct(row['total_growth_pct'])}. "
                "This reflects SAR filing activity, not confirmed financial crime."
            )

            findings.append(
                "Tennessee's latest year-over-year SAR filing change was "
                f"{format_pct(row.get('latest_yoy_growth', np.nan))}, with a study-period peak of "
                f"{format_number(row.get('peak_value', np.nan))} filings in "
                f"{int(row.get('peak_year')) if not pd.isna(row.get('peak_year')) else 'N/A'}."
            )

            if not pd.isna(row.get("latest_share_of_us_total", np.nan)):
                findings.append(
                    "Tennessee accounted for "
                    f"{format_pct(row.get('latest_share_of_us_total'))} of extracted U.S. total SAR filings "
                    f"in {int(row['end_year'])}."
                )

        if not us_row.empty:
            row = us_row.iloc[0]

            findings.append(
                "U.S. SAR filings increased from "
                f"{format_number(row['start_value'])} in {int(row['start_year'])} "
                f"to {format_number(row['end_value'])} in {int(row['end_year'])}, "
                f"a total increase of {format_pct(row['total_growth_pct'])}."
            )

        if not gap_row.empty:
            row = gap_row.iloc[0]
            gap_value = row.get("end_value", np.nan)

            findings.append(
                f"By {int(row['end_year'])}, Tennessee's indexed SAR trend was "
                f"{format_index_gap(gap_value)} the U.S. indexed trend."
            )

    if not tn_vs_us.empty and "tn_minus_us_index_gap" in tn_vs_us.columns:
        latest = tn_vs_us.sort_values("year").iloc[-1]

        if latest["tn_minus_us_index_gap"] < 0:
            findings.append(
                "The latest index comparison suggests national SAR filing growth has outpaced "
                "Tennessee over the indexed study period."
            )
        elif latest["tn_minus_us_index_gap"] > 0:
            findings.append(
                "The latest index comparison suggests Tennessee SAR filing growth has outpaced "
                "national SAR filing growth over the indexed study period."
            )
        else:
            findings.append(
                "The latest index comparison shows Tennessee and national SAR filing growth aligned "
                "closely over the indexed study period."
            )

    if not industry_summary.empty:
        top_industry = industry_summary.iloc[0]

        findings.append(
            "The largest Tennessee SAR filing industry in the latest year was "
            f"{top_industry['industry_name']}, with "
            f"{format_number(top_industry['end_filings'])} filings and "
            f"{format_pct(top_industry['latest_year_share'])} of extracted Tennessee filings."
        )

        growth_leaders = industry_summary.sort_values(
            "absolute_change",
            ascending=False,
        )

        if not growth_leaders.empty:
            growth_row = growth_leaders.iloc[0]
            findings.append(
                "The largest absolute increase by industry came from "
                f"{growth_row['industry_name']}, which changed by "
                f"{format_number(growth_row['absolute_change'])} filings over the study period."
            )

        latest_yoy_leaders = industry_summary.dropna(
            subset=["latest_yoy_growth"]
        ).sort_values("latest_yoy_growth", ascending=False)

        if not latest_yoy_leaders.empty:
            yoy_row = latest_yoy_leaders.iloc[0]

            findings.append(
                "The strongest latest-year industry growth rate came from "
                f"{yoy_row['industry_name']}, with latest YoY growth of "
                f"{format_pct(yoy_row['latest_yoy_growth'])}."
            )

    findings.append(
        "TBI, FBI/NIBRS, elder exploitation, TBI Criminal Investigation Division, "
        "Comptroller, OFAC, and current-indicator layers are treated as supporting "
        "context only and are not included in the SAR trend calculations."
    )

    return findings


def save_key_findings(findings: list[str]) -> None:
    """
    Save key findings to a text file.
    """

    with open(KEY_FINDINGS_FILE, "w", encoding="utf-8") as file:
        file.write(f"{PROJECT_TITLE}\n")
        file.write("Key Findings\n")
        file.write("=" * 60)
        file.write("\n\n")

        for idx, finding in enumerate(findings, start=1):
            file.write(f"{idx}. {finding}\n")

    print(f"Key findings saved to: {KEY_FINDINGS_FILE}")


def run_trend_analysis(
    tn_vs_us: pd.DataFrame,
    industry_trend: pd.DataFrame,
) -> dict:
    """
    Run trend and industry summary analysis.
    """

    trend_summary = summarize_trend(tn_vs_us)
    industry_summary = summarize_industries(industry_trend)

    findings = generate_key_findings(
        trend_summary=trend_summary,
        industry_summary=industry_summary,
        tn_vs_us=tn_vs_us,
    )

    save_key_findings(findings)

    return {
        "trend_summary": trend_summary,
        "industry_summary": industry_summary,
        "key_findings": findings,
    }