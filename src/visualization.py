import matplotlib.pyplot as plt
import pandas as pd

from src.config import (
    ELDER_CONTEXT_CHART,
    FBI_CONTEXT_CHART,
    HIGH_RISK_CATEGORY_CHART,
    OFAC_CONTEXT_CHART,
    SCENARIO_PROJECTION_CHART,
    SENSITIVITY_CHART,
    TBI_CONTEXT_CHART,
    TN_INDUSTRY_CHART,
    TN_TREND_CHART,
    TN_VS_US_INDEX_CHART,
    TOP_CATEGORY_CHART,
    COMPTROLLER_CHART,
)


def save_tennessee_sar_trend_chart(tn_vs_us: pd.DataFrame):
    """
    Save Tennessee SAR filings trend chart.
    """

    if tn_vs_us.empty or "Tennessee" not in tn_vs_us.columns:
        print("Skipping Tennessee trend chart: Tennessee column not available.")
        return None

    chart_df = tn_vs_us.dropna(subset=["Tennessee"]).copy()

    if chart_df.empty:
        print("Skipping Tennessee trend chart: no Tennessee values available.")
        return None

    plt.figure(figsize=(10, 6))
    plt.plot(chart_df["year"], chart_df["Tennessee"], marker="o")
    plt.title("Tennessee SAR Filings Trend")
    plt.xlabel("Year")
    plt.ylabel("SAR Filings")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(TN_TREND_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {TN_TREND_CHART}")
    return TN_TREND_CHART


def save_tn_vs_us_index_chart(tn_vs_us: pd.DataFrame):
    """
    Save Tennessee vs U.S. indexed SAR growth chart.
    """

    required_cols = {"year", "tn_index_2014_100", "us_index_2014_100"}

    if tn_vs_us.empty or not required_cols.issubset(tn_vs_us.columns):
        print("Skipping Tennessee vs U.S. index chart: required columns unavailable.")
        return None

    chart_df = tn_vs_us.dropna(
        subset=["tn_index_2014_100", "us_index_2014_100"]
    ).copy()

    if chart_df.empty:
        print("Skipping Tennessee vs U.S. index chart: no index values available.")
        return None

    plt.figure(figsize=(10, 6))
    plt.plot(
        chart_df["year"],
        chart_df["tn_index_2014_100"],
        marker="o",
        label="Tennessee",
    )
    plt.plot(
        chart_df["year"],
        chart_df["us_index_2014_100"],
        marker="o",
        label="United States / Total",
    )
    plt.title("Tennessee vs U.S. SAR Growth Index")
    plt.xlabel("Year")
    plt.ylabel("Index, Base Year = 100")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(TN_VS_US_INDEX_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {TN_VS_US_INDEX_CHART}")
    return TN_VS_US_INDEX_CHART


def save_tennessee_industry_chart(industry_trend: pd.DataFrame):
    """
    Save Tennessee SAR filings by industry chart.
    """

    if industry_trend.empty:
        print("Skipping industry chart: industry trend table is empty.")
        return None

    latest_year = industry_trend["year"].max()
    latest = industry_trend[industry_trend["year"].eq(latest_year)].copy()

    if latest.empty:
        print("Skipping industry chart: no latest-year values available.")
        return None

    latest = latest.sort_values("sar_filings", ascending=True)

    plt.figure(figsize=(10, 6))
    plt.barh(latest["industry_name"], latest["sar_filings"])
    plt.title(f"Tennessee SAR Filings by Industry, {latest_year}")
    plt.xlabel("SAR Filings")
    plt.ylabel("Industry")
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(TN_INDUSTRY_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {TN_INDUSTRY_CHART}")
    return TN_INDUSTRY_CHART


def save_all_charts(tn_vs_us: pd.DataFrame, industry_trend: pd.DataFrame):
    """
    Save all core trend and industry charts.
    """

    chart_paths = []

    for chart_func, data in [
        (save_tennessee_sar_trend_chart, tn_vs_us),
        (save_tn_vs_us_index_chart, tn_vs_us),
        (save_tennessee_industry_chart, industry_trend),
    ]:
        path = chart_func(data)

        if path is not None:
            chart_paths.append(path)

    return chart_paths


def save_top_category_chart(category_summary: pd.DataFrame, top_n: int = 15):
    """
    Save chart of top suspicious activity categories by latest-year filings.

    Note:
    Category exhibits are treated as industry-level / national suspicious
    activity context, not Tennessee-specific category counts.
    """

    if category_summary.empty:
        print("Skipping category chart: category summary is empty.")
        return None

    chart_df = category_summary.sort_values("end_filings", ascending=False).head(top_n)
    chart_df = chart_df.sort_values("end_filings", ascending=True)

    plt.figure(figsize=(11, 7))
    plt.barh(chart_df["category"], chart_df["end_filings"])
    plt.title("Top Suspicious Activity Categories by Latest-Year Filings")
    plt.xlabel("SAR Filings")
    plt.ylabel("Suspicious Activity Category")
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(TOP_CATEGORY_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {TOP_CATEGORY_CHART}")
    return TOP_CATEGORY_CHART


def save_high_risk_category_chart(category_summary: pd.DataFrame, top_n: int = 15):
    """
    Save chart of elevated and high-risk suspicious activity categories.
    """

    if category_summary.empty:
        print("Skipping high-risk category chart: category summary is empty.")
        return None

    required_cols = {"category", "end_filings"}

    if not required_cols.issubset(category_summary.columns):
        print("Skipping high-risk category chart: required columns unavailable.")
        return None

    if "risk_tier" in category_summary.columns:
        chart_df = category_summary[
            category_summary["risk_tier"]
            .astype(str)
            .isin(["Elevated Context", "High-Risk Context"])
        ].copy()
    elif "high_risk_flag" in category_summary.columns:
        chart_df = category_summary[
            category_summary["high_risk_flag"].eq(True)
        ].copy()
    else:
        print("Skipping high-risk category chart: no risk tier or high-risk flag available.")
        return None

    if chart_df.empty:
        print("Skipping high-risk category chart: no elevated/high-risk categories found.")
        return None

    chart_df = chart_df.sort_values("end_filings", ascending=False).head(top_n)
    chart_df = chart_df.sort_values("end_filings", ascending=True)

    plt.figure(figsize=(11, 7))
    plt.barh(chart_df["category"], chart_df["end_filings"])
    plt.title("Elevated and High-Risk Suspicious Activity Categories")
    plt.xlabel("SAR Filings")
    plt.ylabel("Suspicious Activity Category")
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(HIGH_RISK_CATEGORY_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {HIGH_RISK_CATEGORY_CHART}")
    return HIGH_RISK_CATEGORY_CHART


def save_scenario_projection_chart(
    tn_vs_us: pd.DataFrame,
    scenario_projections: pd.DataFrame,
):
    """
    Save Tennessee SAR historical and scenario projection chart.
    """

    if tn_vs_us.empty or scenario_projections.empty:
        print("Skipping scenario projection chart: required data unavailable.")
        return None

    if "Tennessee" not in tn_vs_us.columns:
        print("Skipping scenario projection chart: Tennessee column unavailable.")
        return None

    historical = tn_vs_us[["year", "Tennessee"]].copy()
    historical = historical.rename(columns={"Tennessee": "sar_filings"})

    plt.figure(figsize=(11, 7))

    plt.plot(
        historical["year"],
        historical["sar_filings"],
        marker="o",
        linewidth=2,
        label="Historical Tennessee SAR Filings",
    )

    for scenario, group in scenario_projections.groupby("scenario"):
        group = group.sort_values("year")

        base_year = int(group["base_year"].iloc[0])
        base_value = group["base_year_filings"].iloc[0]

        scenario_years = [base_year] + group["year"].tolist()
        scenario_values = [base_value] + group["projected_sar_filings"].tolist()

        plt.plot(
            scenario_years,
            scenario_values,
            marker="o",
            linestyle="--",
            label=scenario,
        )

    plt.title("Tennessee SAR Filing Scenario Projections")
    plt.xlabel("Year")
    plt.ylabel("SAR Filings")
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(SCENARIO_PROJECTION_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {SCENARIO_PROJECTION_CHART}")
    return SCENARIO_PROJECTION_CHART


def save_sensitivity_chart(sensitivity_results: pd.DataFrame):
    """
    Save SAR Pressure Index sensitivity chart.
    """

    if sensitivity_results.empty:
        print("Skipping sensitivity chart: sensitivity results are empty.")
        return None

    required_cols = {"weighting_scenario", "sar_pressure_index"}

    if not required_cols.issubset(sensitivity_results.columns):
        print("Skipping sensitivity chart: required columns unavailable.")
        return None

    chart_df = sensitivity_results.sort_values(
        "sar_pressure_index",
        ascending=True,
    ).copy()

    plt.figure(figsize=(11, 7))
    plt.barh(chart_df["weighting_scenario"], chart_df["sar_pressure_index"])
    plt.axvline(50, linestyle="--", linewidth=1, label="Moderate Threshold")
    plt.axvline(75, linestyle="--", linewidth=1, label="Elevated Threshold")
    plt.title("SAR Pressure Index Sensitivity by Weighting Scenario")
    plt.xlabel("SAR Pressure Index")
    plt.ylabel("Weighting Scenario")
    plt.legend()
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(SENSITIVITY_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {SENSITIVITY_CHART}")
    return SENSITIVITY_CHART


def save_tbi_context_chart(tbi_summary: pd.DataFrame, top_n: int = 15):
    """
    Save chart of latest TBI financial-crime-adjacent context counts.
    """

    if tbi_summary.empty or "crime_category" not in tbi_summary.columns:
        print("Skipping TBI context chart: no numeric TBI summary available.")
        return None

    required_cols = {"crime_category", "latest_reported_count"}

    if not required_cols.issubset(tbi_summary.columns):
        print("Skipping TBI context chart: required columns unavailable.")
        return None

    chart_df = tbi_summary.dropna(subset=["latest_reported_count"]).copy()

    if chart_df.empty:
        print("Skipping TBI context chart: no numeric TBI counts available.")
        return None

    chart_df = chart_df.sort_values("latest_reported_count", ascending=False).head(top_n)
    chart_df = chart_df.sort_values("latest_reported_count", ascending=True)

    plt.figure(figsize=(11, 7))
    plt.barh(chart_df["crime_category"], chart_df["latest_reported_count"])
    plt.title("TBI Financial-Crime Context: Latest Reported Counts")
    plt.xlabel("Reported Count")
    plt.ylabel("Crime Category")
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(TBI_CONTEXT_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {TBI_CONTEXT_CHART}")
    return TBI_CONTEXT_CHART


def save_fbi_context_chart(fbi_summary: pd.DataFrame, top_n: int = 15):
    """
    Save chart of FBI financial-crime-adjacent context counts.
    """

    if fbi_summary.empty or "crime_category" not in fbi_summary.columns:
        print("Skipping FBI context chart: no numeric FBI summary available.")
        return None

    required_cols = {"crime_category", "latest_reported_count"}

    if not required_cols.issubset(fbi_summary.columns):
        print("Skipping FBI context chart: required columns unavailable.")
        return None

    chart_df = fbi_summary.dropna(subset=["latest_reported_count"]).copy()

    if chart_df.empty:
        print("Skipping FBI context chart: no numeric FBI counts available.")
        return None

    chart_df = chart_df.sort_values("latest_reported_count", ascending=False).head(top_n)
    chart_df = chart_df.sort_values("latest_reported_count", ascending=True)

    plt.figure(figsize=(11, 7))
    plt.barh(chart_df["crime_category"], chart_df["latest_reported_count"])
    plt.title("FBI Crime Data Explorer / NIBRS Context: Latest Tennessee Counts")
    plt.xlabel("Reported Count")
    plt.ylabel("Crime Category")
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FBI_CONTEXT_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {FBI_CONTEXT_CHART}")
    return FBI_CONTEXT_CHART


def save_comptroller_context_chart(comptroller_context: pd.DataFrame):
    """
    Save chart of numeric Comptroller public-sector fraud / audit context indicators.
    """

    if comptroller_context.empty:
        print("Skipping Comptroller context chart: context table is empty.")
        return None

    required_cols = {"metric", "value"}

    if not required_cols.issubset(comptroller_context.columns):
        print("Skipping Comptroller context chart: required columns unavailable.")
        return None

    chart_df = comptroller_context.copy()
    chart_df["numeric_value"] = pd.to_numeric(chart_df["value"], errors="coerce")
    chart_df = chart_df.dropna(subset=["numeric_value"])

    if chart_df.empty:
        print("Skipping Comptroller context chart: no numeric values available.")
        return None

    if "context_theme" in chart_df.columns:
        chart_df["label"] = (
            chart_df["context_theme"].astype(str)
            + ": "
            + chart_df["metric"].astype(str)
        )
    else:
        chart_df["label"] = chart_df["metric"].astype(str)

    chart_df = chart_df.sort_values("numeric_value", ascending=True)

    plt.figure(figsize=(11, 7))
    plt.barh(chart_df["label"], chart_df["numeric_value"])
    plt.title("Comptroller Public-Sector Fraud / Audit Context")
    plt.xlabel("Reported Count")
    plt.ylabel("Context Indicator")
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(COMPTROLLER_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {COMPTROLLER_CHART}")
    return COMPTROLLER_CHART


def save_elder_exploitation_chart(elder_context_summary: pd.DataFrame):
    """
    Save chart of numeric elder financial exploitation context indicators.
    """

    if elder_context_summary.empty:
        print("Skipping elder exploitation chart: summary is empty.")
        return None

    required_cols = {"topic", "metric_value"}

    if not required_cols.issubset(elder_context_summary.columns):
        print("Skipping elder exploitation chart: required columns unavailable.")
        return None

    chart_df = elder_context_summary.dropna(subset=["metric_value"]).copy()

    if chart_df.empty:
        print("Skipping elder exploitation chart: no numeric context values available.")
        return None

    chart_df["label"] = (
        chart_df["evidence_type"].astype(str)
        + ": "
        + chart_df["topic"].astype(str)
    )

    chart_df = chart_df.sort_values("metric_value", ascending=True)

    plt.figure(figsize=(11, 7))
    plt.barh(chart_df["label"], chart_df["metric_value"])
    plt.title("Elder Financial Exploitation Context Indicators")
    plt.xlabel("Reported Count / SAR Category Count")
    plt.ylabel("Context Indicator")
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(ELDER_CONTEXT_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {ELDER_CONTEXT_CHART}")
    return ELDER_CONTEXT_CHART


def save_ofac_context_chart(ofac_summary: pd.DataFrame):
    """
    Save chart of OFAC Tennessee sanctions geography context by program.
    """

    required_cols = {"metric", "value"}

    if ofac_summary.empty or not required_cols.issubset(ofac_summary.columns):
        print("Skipping OFAC context chart: summary unavailable or required columns missing.")
        return None

    chart_df = ofac_summary[
        ofac_summary["metric"].astype(str).str.startswith("Program:")
    ].copy()

    if chart_df.empty:
        print("Skipping OFAC context chart: no OFAC program rows available.")
        return None

    chart_df["program"] = chart_df["metric"].str.replace("Program: ", "", regex=False)
    chart_df = chart_df.sort_values("value", ascending=True)

    plt.figure(figsize=(11, 7))
    plt.barh(chart_df["program"], chart_df["value"])
    plt.title("OFAC Tennessee Address Matches by Sanctions Program")
    plt.xlabel("Address Match Count")
    plt.ylabel("OFAC Program")
    plt.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OFAC_CONTEXT_CHART, dpi=300)
    plt.close()

    print(f"Chart saved to: {OFAC_CONTEXT_CHART}")
    return OFAC_CONTEXT_CHART