import numpy as np
import pandas as pd

from src.config import FINANCIAL_CRIME_SCORECARD_FILE


def format_number(value) -> str:
    """
    Format numeric values for scorecard display.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.0f}"
    except Exception:
        return str(value)


def format_float(value, decimals: int = 2) -> str:
    """
    Format float values for scorecard display.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return str(value)


def format_pct(value) -> str:
    """
    Format decimal values as percentages.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value) * 100:,.1f}%"
    except Exception:
        return str(value)


def get_first_value(df: pd.DataFrame, column: str, default=np.nan):
    """
    Safely get the first value from a dataframe column.
    """

    if df is None or df.empty or column not in df.columns:
        return default

    values = df[column].dropna()

    if values.empty:
        return default

    return values.iloc[0]


def get_component_score(components: pd.DataFrame, component_name: str):
    """
    Pull a SAR Pressure Index component score by component name.
    """

    if components is None or components.empty:
        return np.nan

    if "component" not in components.columns or "score" not in components.columns:
        return np.nan

    rows = components[
        components["component"]
        .astype(str)
        .str.lower()
        .eq(component_name.lower())
    ]

    if rows.empty:
        return np.nan

    return rows.iloc[0].get("score", np.nan)


def get_summary_metric_value(summary: pd.DataFrame, metric_name: str):
    """
    Pull a numeric value from a two-column summary table with metric/value fields.
    """

    if summary is None or summary.empty:
        return np.nan

    if "metric" not in summary.columns or "value" not in summary.columns:
        return np.nan

    rows = summary[
        summary["metric"]
        .astype(str)
        .str.lower()
        .eq(metric_name.lower())
    ]

    if rows.empty:
        return np.nan

    return pd.to_numeric(rows.iloc[0].get("value"), errors="coerce")


def classify_index_score(score) -> str:
    """
    Classify a 0-100 score for scorecard display.
    """

    if pd.isna(score):
        return "Not Available"

    score = float(score)

    if score >= 75:
        return "Elevated"
    if score >= 50:
        return "Moderate"
    if score >= 25:
        return "Watchlist"
    return "Lower Relative"


def classify_share_concentration(share) -> str:
    """
    Classify industry concentration.
    """

    if pd.isna(share):
        return "Not Available"

    share = float(share)

    if share >= 0.60:
        return "High"
    if share >= 0.40:
        return "Moderate"
    return "Diversified"


def build_financial_crime_scorecard(
    sar_pressure_index: pd.DataFrame,
    sar_pressure_components: pd.DataFrame,
    trend_summary: pd.DataFrame,
    industry_summary: pd.DataFrame,
    tbi_summary: pd.DataFrame | None = None,
    fbi_summary: pd.DataFrame | None = None,
    comptroller_context: pd.DataFrame | None = None,
    ofac_summary: pd.DataFrame | None = None,
    current_indicators_context: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Build a front-of-report Financial Crime Intelligence Scorecard.

    The scorecard summarizes the major signals from the project without changing
    the SAR Pressure Index methodology. It is a presentation and interpretation
    layer only.
    """

    rows = []

    # ------------------------------------------------------------
    # SAR Pressure Index
    # ------------------------------------------------------------

    sar_score = get_first_value(sar_pressure_index, "sar_pressure_index")
    sar_signal = get_first_value(sar_pressure_index, "signal", "Not Available")
    latest_year = get_first_value(sar_pressure_index, "latest_year", "N/A")

    rows.append(
        {
            "dimension": "Overall SAR Pressure",
            "signal": sar_signal,
            "score_or_status": f"{format_float(sar_score)} / 100",
            "evidence": f"SAR Pressure Index, {latest_year}",
            "interpretation": (
                "Composite SAR-based signal summarizing Tennessee SAR growth, recent momentum, "
                "national divergence, industry concentration, and high-risk category context."
            ),
            "included_in_sar_pressure_index": "Yes",
            "methodology_note": "This is the core SAR-based composite signal.",
        }
    )

    # ------------------------------------------------------------
    # Tennessee SAR trend pressure
    # ------------------------------------------------------------

    growth_score = get_component_score(
        sar_pressure_components,
        "Tennessee SAR Growth Pressure",
    )

    tn_trend_rows = pd.DataFrame()

    if trend_summary is not None and not trend_summary.empty and "metric" in trend_summary.columns:
        tn_trend_rows = trend_summary[
            trend_summary["metric"]
            .astype(str)
            .str.lower()
            .eq("tennessee sar filings")
        ]

    if not tn_trend_rows.empty:
        tn_row = tn_trend_rows.iloc[0]
        start_year = tn_row.get("start_year", "N/A")
        end_year = tn_row.get("end_year", "N/A")
        start_value = tn_row.get("start_value", np.nan)
        end_value = tn_row.get("end_value", np.nan)
        total_growth = tn_row.get("total_growth_pct", np.nan)

        evidence = (
            f"{format_number(start_value)} filings in {start_year} to "
            f"{format_number(end_value)} filings in {end_year}; "
            f"{format_pct(total_growth)} total growth"
        )
    else:
        evidence = "Tennessee SAR trend summary unavailable"

    rows.append(
        {
            "dimension": "Tennessee SAR Trend Pressure",
            "signal": classify_index_score(growth_score),
            "score_or_status": f"{format_float(growth_score)} / 100",
            "evidence": evidence,
            "interpretation": (
                "Measures long-run Tennessee SAR filing growth. SAR filings reflect reporting "
                "activity and monitoring behavior, not confirmed financial crime."
            ),
            "included_in_sar_pressure_index": "Yes",
            "methodology_note": "Derived from FinCEN SAR Stats Tennessee annual filing trends.",
        }
    )

    # ------------------------------------------------------------
    # Tennessee vs U.S. divergence
    # ------------------------------------------------------------

    divergence_score = get_component_score(
        sar_pressure_components,
        "Tennessee vs U.S. Divergence",
    )

    gap_rows = pd.DataFrame()

    if trend_summary is not None and not trend_summary.empty and "metric" in trend_summary.columns:
        gap_rows = trend_summary[
            trend_summary["metric"]
            .astype(str)
            .str.lower()
            .eq("tennessee minus u.s. sar index gap")
        ]

    if not gap_rows.empty:
        gap_row = gap_rows.iloc[0]
        gap_value = gap_row.get("end_value", np.nan)
        evidence = f"Tennessee index gap: {format_float(gap_value, 1)} points"
    else:
        evidence = "Tennessee-vs-U.S. indexed comparison unavailable"

    rows.append(
        {
            "dimension": "National Divergence",
            "signal": classify_index_score(divergence_score),
            "score_or_status": f"{format_float(divergence_score)} / 100",
            "evidence": evidence,
            "interpretation": (
                "Compares Tennessee indexed SAR growth against the broader U.S. indexed SAR trend. "
                "A lower score indicates Tennessee has grown more slowly than the U.S. benchmark."
            ),
            "included_in_sar_pressure_index": "Yes",
            "methodology_note": "Derived from FinCEN SAR Stats Exhibit 1 and Exhibit 2 trend comparison.",
        }
    )

    # ------------------------------------------------------------
    # Industry concentration
    # ------------------------------------------------------------

    concentration_score = get_component_score(
        sar_pressure_components,
        "Industry Concentration",
    )

    if industry_summary is not None and not industry_summary.empty:
        top_industry = industry_summary.iloc[0]
        top_share = top_industry.get("latest_year_share", np.nan)
        evidence = (
            f"{top_industry.get('industry_name', 'Top industry')} accounted for "
            f"{format_pct(top_share)} of extracted Tennessee filings"
        )
        concentration_signal = classify_share_concentration(top_share)
    else:
        evidence = "Industry summary unavailable"
        concentration_signal = classify_index_score(concentration_score)

    rows.append(
        {
            "dimension": "Industry Concentration",
            "signal": concentration_signal,
            "score_or_status": f"{format_float(concentration_score)} / 100",
            "evidence": evidence,
            "interpretation": (
                "Measures whether Tennessee SAR filings are concentrated in one filing industry. "
                "Higher concentration can indicate dependence on one reporting channel."
            ),
            "included_in_sar_pressure_index": "Yes",
            "methodology_note": "Derived from Tennessee industry-level FinCEN SAR Stats rows.",
        }
    )

    # ------------------------------------------------------------
    # High-risk category context
    # ------------------------------------------------------------

    category_score = get_component_score(
        sar_pressure_components,
        "High-Risk Category Context",
    )

    rows.append(
        {
            "dimension": "High-Risk Category Context",
            "signal": classify_index_score(category_score),
            "score_or_status": f"{format_float(category_score)} / 100",
            "evidence": "High-risk and elevated suspicious activity category themes",
            "interpretation": (
                "Summarizes elevated SAR-theme context such as source-of-funds concerns, no apparent "
                "lawful purpose, suspicious EFT/wire transfers, identity theft, elder exploitation, "
                "terrorist-financing-related categories, sanctions, corruption, and bribery."
            ),
            "included_in_sar_pressure_index": "Yes",
            "methodology_note": (
                "Category exhibits are treated as SAR-theme context and should not be interpreted "
                "as Tennessee-specific category counts unless supported by source data."
            ),
        }
    )

    # ------------------------------------------------------------
    # TBI / FBI law-enforcement context
    # ------------------------------------------------------------

    tbi_available = tbi_summary is not None and not tbi_summary.empty
    fbi_available = fbi_summary is not None and not fbi_summary.empty

    if tbi_available:
        tbi_top = tbi_summary.sort_values(
            "latest_reported_count",
            ascending=False,
        ).iloc[0]
        tbi_evidence = (
            f"TBI top category: {tbi_top.get('crime_category')} "
            f"({format_number(tbi_top.get('latest_reported_count'))})"
        )
    else:
        tbi_evidence = "TBI context unavailable"

    if fbi_available:
        fbi_top = fbi_summary.sort_values(
            "latest_reported_count",
            ascending=False,
        ).iloc[0]
        fbi_evidence = (
            f"FBI/NIBRS top category: {fbi_top.get('crime_category')} "
            f"({format_number(fbi_top.get('latest_reported_count'))})"
        )
    else:
        fbi_evidence = "FBI/NIBRS context unavailable"

    rows.append(
        {
            "dimension": "Law-Enforcement Context",
            "signal": "Available" if tbi_available or fbi_available else "Not Available",
            "score_or_status": "Informational",
            "evidence": f"{tbi_evidence}; {fbi_evidence}",
            "interpretation": (
                "Provides supporting Tennessee and federal law-enforcement offense context for fraud, "
                "identity theft, exploitation, and financial-crime-adjacent themes."
            ),
            "included_in_sar_pressure_index": "No",
            "methodology_note": "TBI and FBI/NIBRS offense data are context only and are not SAR filings.",
        }
    )

    # ------------------------------------------------------------
    # Comptroller context
    # ------------------------------------------------------------

    comptroller_available = comptroller_context is not None and not comptroller_context.empty

    if comptroller_available:
        context = comptroller_context.copy()
        context["numeric_value"] = pd.to_numeric(context.get("value"), errors="coerce")

        hotline_rows = context[
            context["metric"]
            .astype(str)
            .str.lower()
            .str.contains("hotline notifications", na=False)
        ]

        allegation_rows = context[
            context["metric"]
            .astype(str)
            .str.lower()
            .str.contains("substantive allegations", na=False)
        ]

        hotline_value = (
            hotline_rows.iloc[0].get("numeric_value")
            if not hotline_rows.empty
            else np.nan
        )

        allegation_value = (
            allegation_rows.iloc[0].get("numeric_value")
            if not allegation_rows.empty
            else np.nan
        )

        comptroller_evidence = (
            f"{format_number(hotline_value)} hotline notifications; "
            f"{format_number(allegation_value)} substantive allegations"
        )
    else:
        comptroller_evidence = "Comptroller context unavailable"

    rows.append(
        {
            "dimension": "Public-Sector Fraud Context",
            "signal": "Available" if comptroller_available else "Not Available",
            "score_or_status": "Informational",
            "evidence": comptroller_evidence,
            "interpretation": (
                "Adds public-sector fraud, waste, abuse, allegation, audit, and internal-control "
                "context to the Tennessee financial crime intelligence picture."
            ),
            "included_in_sar_pressure_index": "No",
            "methodology_note": (
                "Comptroller data is allegation/reporting and oversight context, not SAR activity "
                "or confirmed fraud."
            ),
        }
    )

    # ------------------------------------------------------------
    # OFAC context
    # ------------------------------------------------------------

    ofac_matches = get_summary_metric_value(
        ofac_summary,
        "Tennessee OFAC address matches",
    )

    if pd.isna(ofac_matches):
        ofac_signal = "Not Available"
        ofac_status = "No summary available"
        ofac_evidence = "OFAC context unavailable"
    elif ofac_matches > 0:
        ofac_signal = "Accepted TN Matches"
        ofac_status = format_number(ofac_matches)
        ofac_evidence = f"{format_number(ofac_matches)} accepted Tennessee-related OFAC address matches"
    else:
        ofac_signal = "No Accepted TN Matches"
        ofac_status = "0"
        ofac_evidence = "No accepted Tennessee address matches after stricter geography validation"

    rows.append(
        {
            "dimension": "OFAC Context",
            "signal": ofac_signal,
            "score_or_status": ofac_status,
            "evidence": ofac_evidence,
            "interpretation": (
                "Screens current OFAC public address files for accepted Tennessee-related geography "
                "indicators while avoiding false positives from ambiguous TN/city terms."
            ),
            "included_in_sar_pressure_index": "No",
            "methodology_note": (
                "OFAC address matches are sanctions-screening geography context only and do not "
                "indicate SAR activity, local criminal activity, or enforcement action."
            ),
        }
    )

    # ------------------------------------------------------------
    # Current indicators
    # ------------------------------------------------------------

    current_available = (
        current_indicators_context is not None
        and not current_indicators_context.empty
    )

    rows.append(
        {
            "dimension": "Current Indicators",
            "signal": "Monitor" if current_available else "Not Available",
            "score_or_status": "2025-2026 Context" if current_available else "N/A",
            "evidence": (
                f"{len(current_indicators_context)} current-indicator rows"
                if current_available
                else "Current indicators unavailable"
            ),
            "interpretation": (
                "Keeps newer TBI, Comptroller, OFAC, and FinCEN release-monitoring context separate "
                "from the comparable 2014-2024 SAR trend model."
            ),
            "included_in_sar_pressure_index": "No",
            "methodology_note": (
                "Current indicators are forward-looking context only and are not blended into the "
                "SAR Pressure Index."
            ),
        }
    )

    scorecard = pd.DataFrame(rows)

    scorecard.to_csv(FINANCIAL_CRIME_SCORECARD_FILE, index=False)
    print(f"Financial crime intelligence scorecard saved to: {FINANCIAL_CRIME_SCORECARD_FILE}")

    return scorecard


def run_intelligence_scorecard_analysis(
    sar_pressure_index: pd.DataFrame,
    sar_pressure_components: pd.DataFrame,
    trend_summary: pd.DataFrame,
    industry_summary: pd.DataFrame,
    tbi_summary: pd.DataFrame | None = None,
    fbi_summary: pd.DataFrame | None = None,
    comptroller_context: pd.DataFrame | None = None,
    ofac_summary: pd.DataFrame | None = None,
    current_indicators_context: pd.DataFrame | None = None,
) -> dict:
    """
    Run the financial crime intelligence scorecard layer.
    """

    scorecard = build_financial_crime_scorecard(
        sar_pressure_index=sar_pressure_index,
        sar_pressure_components=sar_pressure_components,
        trend_summary=trend_summary,
        industry_summary=industry_summary,
        tbi_summary=tbi_summary,
        fbi_summary=fbi_summary,
        comptroller_context=comptroller_context,
        ofac_summary=ofac_summary,
        current_indicators_context=current_indicators_context,
    )

    return {
        "intelligence_scorecard": scorecard,
    }