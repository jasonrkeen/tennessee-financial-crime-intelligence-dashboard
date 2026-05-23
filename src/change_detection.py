import numpy as np
import pandas as pd

from src.config import END_YEAR, TABLES_DIR


CHANGE_DETECTION_FLAGS_FILE = TABLES_DIR / "change_detection_flags.csv"
CHANGE_DETECTION_SUMMARY_FILE = TABLES_DIR / "change_detection_summary.csv"


def format_pct(value: float) -> str:
    """
    Format decimal percentages.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value) * 100:,.1f}%"
    except Exception:
        return str(value)


def format_number(value: float) -> str:
    """
    Format numeric values.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.0f}"
    except Exception:
        return str(value)


def format_year(value) -> str:
    """
    Format year-like values safely.
    """

    if pd.isna(value):
        return "the latest year"

    try:
        return str(int(value))
    except Exception:
        return str(value)


def classify_severity(score: int) -> str:
    """
    Convert numeric severity score to label.
    """

    if score >= 4:
        return "High"
    if score >= 3:
        return "Moderate"
    if score >= 2:
        return "Low"
    return "Informational"


def add_flag(
    flags: list,
    flag_type: str,
    description: str,
    severity_score: int,
    metric: str,
    latest_value=None,
    comparison_value=None,
    source_layer: str = "SAR Trend Layer",
    methodology_scope: str = "SAR-based signal",
):
    """
    Append a standardized change-detection flag.
    """

    flags.append(
        {
            "source_layer": source_layer,
            "flag_type": flag_type,
            "severity": classify_severity(severity_score),
            "severity_score": severity_score,
            "metric": metric,
            "latest_value": latest_value,
            "comparison_value": comparison_value,
            "methodology_scope": methodology_scope,
            "description": description,
        }
    )


def detect_trend_changes(tn_vs_us: pd.DataFrame) -> list[dict]:
    """
    Detect major Tennessee vs U.S. SAR trend changes.
    """

    flags = []

    if tn_vs_us.empty or "Tennessee" not in tn_vs_us.columns:
        return flags

    df = tn_vs_us.sort_values("year").copy()

    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) >= 2 else None

    latest_year = int(latest["year"])
    latest_tn = latest["Tennessee"]
    peak_tn = df["Tennessee"].max()
    peak_year = int(df.loc[df["Tennessee"].idxmax(), "year"])

    if latest_tn == peak_tn:
        add_flag(
            flags=flags,
            flag_type="New High",
            description=(
                f"Tennessee SAR filings reached a study-period high in {latest_year} "
                f"with {format_number(latest_tn)} filings."
            ),
            severity_score=3,
            metric="Tennessee SAR filings",
            latest_value=latest_tn,
            comparison_value=peak_tn,
            source_layer="SAR Trend Layer",
            methodology_scope="SAR-based signal",
        )
    else:
        add_flag(
            flags=flags,
            flag_type="Below Peak",
            description=(
                f"Tennessee SAR filings in {latest_year} were below the study-period "
                f"peak of {format_number(peak_tn)} reached in {peak_year}."
            ),
            severity_score=1,
            metric="Tennessee SAR filings",
            latest_value=latest_tn,
            comparison_value=peak_tn,
            source_layer="SAR Trend Layer",
            methodology_scope="SAR-based signal",
        )

    if previous is not None:
        prior_tn = previous["Tennessee"]

        if pd.isna(prior_tn) or prior_tn <= 0:
            latest_growth = np.nan
        else:
            latest_growth = latest_tn / prior_tn - 1

        if not pd.isna(latest_growth):
            if latest_growth >= 0.10:
                severity = 4
                direction = "increased sharply"
            elif latest_growth > 0:
                severity = 2
                direction = "increased"
            elif latest_growth <= -0.10:
                severity = 3
                direction = "declined sharply"
            else:
                severity = 1
                direction = "declined slightly"

            add_flag(
                flags=flags,
                flag_type="Latest YoY Change",
                description=(
                    f"Tennessee SAR filings {direction} from {format_number(prior_tn)} "
                    f"in {int(previous['year'])} to {format_number(latest_tn)} in {latest_year}, "
                    f"a latest-year change of {format_pct(latest_growth)}."
                ),
                severity_score=severity,
                metric="Tennessee latest YoY growth",
                latest_value=latest_growth,
                comparison_value=0,
                source_layer="SAR Trend Layer",
                methodology_scope="SAR-based signal",
            )

    if "tn_minus_us_index_gap" in df.columns:
        latest_gap = latest["tn_minus_us_index_gap"]

        if pd.isna(latest_gap):
            return flags

        if latest_gap <= -40:
            severity = 3
            gap_description = "materially below"
        elif latest_gap < 0:
            severity = 2
            gap_description = "below"
        elif latest_gap >= 40:
            severity = 4
            gap_description = "materially above"
        else:
            severity = 2
            gap_description = "near"

        add_flag(
            flags=flags,
            flag_type="Tennessee vs U.S. Divergence",
            description=(
                f"Tennessee's indexed SAR trend was {gap_description} the U.S. trend "
                f"in {latest_year}, with an index gap of {latest_gap:,.1f} points."
            ),
            severity_score=severity,
            metric="TN minus U.S. SAR index gap",
            latest_value=latest_gap,
            comparison_value=0,
            source_layer="SAR Trend Layer",
            methodology_scope="SAR-based signal",
        )

    return flags


def detect_industry_changes(industry_trend: pd.DataFrame) -> list[dict]:
    """
    Detect industry concentration and latest-year industry movement.
    """

    flags = []

    if industry_trend.empty:
        return flags

    df = industry_trend.sort_values(["industry_name", "year"]).copy()

    latest_year = int(df["year"].max())
    prior_year = latest_year - 1

    latest = df[df["year"].eq(latest_year)].copy()
    prior = df[df["year"].eq(prior_year)].copy()

    if latest.empty:
        return flags

    latest_total = latest["sar_filings"].sum()

    if latest_total > 0:
        if "industry_share_of_tn_filings" in latest.columns:
            latest["share"] = latest["industry_share_of_tn_filings"]
        elif "latest_year_share" in latest.columns:
            latest["share"] = latest["latest_year_share"]
        else:
            latest["share"] = latest["sar_filings"] / latest_total

        top_row = latest.sort_values("share", ascending=False).iloc[0]
        top_share = top_row["share"]

        if top_share >= 0.60:
            severity = 4
            concentration_description = "highly concentrated"
        elif top_share >= 0.40:
            severity = 3
            concentration_description = "moderately concentrated"
        else:
            severity = 2
            concentration_description = "diversified"

        add_flag(
            flags=flags,
            flag_type="Industry Concentration",
            description=(
                f"Tennessee SAR filings were {concentration_description} in {latest_year}; "
                f"{top_row['industry_name']} accounted for {format_pct(top_share)} "
                f"of extracted Tennessee filings."
            ),
            severity_score=severity,
            metric="Top industry share",
            latest_value=top_share,
            comparison_value=0.50,
            source_layer="SAR Industry Layer",
            methodology_scope="SAR-based signal",
        )

    if prior.empty:
        return flags

    merged = latest.merge(
        prior[["industry_name", "sar_filings"]],
        on="industry_name",
        how="left",
        suffixes=("_latest", "_prior"),
    )

    merged["absolute_change"] = (
        merged["sar_filings_latest"] - merged["sar_filings_prior"]
    )

    merged["yoy_growth"] = np.where(
        merged["sar_filings_prior"] > 0,
        merged["absolute_change"] / merged["sar_filings_prior"],
        np.nan,
    )

    largest_increase = merged.sort_values("absolute_change", ascending=False).iloc[0]
    largest_decrease = merged.sort_values("absolute_change", ascending=True).iloc[0]

    if largest_increase["absolute_change"] > 0:
        add_flag(
            flags=flags,
            flag_type="Largest Industry Increase",
            description=(
                f"The largest latest-year industry increase came from "
                f"{largest_increase['industry_name']}, rising by "
                f"{format_number(largest_increase['absolute_change'])} filings "
                f"from {prior_year} to {latest_year}."
            ),
            severity_score=3,
            metric="Largest industry absolute increase",
            latest_value=largest_increase["absolute_change"],
            comparison_value=0,
            source_layer="SAR Industry Layer",
            methodology_scope="SAR-based signal",
        )

    if largest_decrease["absolute_change"] < 0:
        add_flag(
            flags=flags,
            flag_type="Largest Industry Decrease",
            description=(
                f"The largest latest-year industry decrease came from "
                f"{largest_decrease['industry_name']}, falling by "
                f"{format_number(abs(largest_decrease['absolute_change']))} filings "
                f"from {prior_year} to {latest_year}."
            ),
            severity_score=2,
            metric="Largest industry absolute decrease",
            latest_value=largest_decrease["absolute_change"],
            comparison_value=0,
            source_layer="SAR Industry Layer",
            methodology_scope="SAR-based signal",
        )

    return flags


def detect_pressure_index_changes(sar_pressure_index: pd.DataFrame) -> list[dict]:
    """
    Add flags based on the SAR Pressure Index.
    """

    flags = []

    if sar_pressure_index.empty:
        return flags

    row = sar_pressure_index.iloc[0]
    score = row.get("sar_pressure_index", np.nan)
    signal = row.get("signal", "Unknown")
    latest_year = row.get("latest_year", np.nan)

    if pd.isna(score):
        return flags

    if score >= 75:
        severity = 4
    elif score >= 50:
        severity = 3
    elif score >= 25:
        severity = 2
    else:
        severity = 1

    add_flag(
        flags=flags,
        flag_type="SAR Pressure Index Signal",
        description=(
            f"The Tennessee SAR Pressure Index was {float(score):,.2f}/100 in "
            f"{format_year(latest_year)}, classified as {signal}."
        ),
        severity_score=severity,
        metric="SAR Pressure Index",
        latest_value=score,
        comparison_value=50,
        source_layer="SAR Pressure Index",
        methodology_scope="SAR-based composite signal",
    )

    return flags


def detect_tbi_context_changes(tbi_summary: pd.DataFrame) -> list[dict]:
    """
    Add context flags from the TBI / TIBRS layer.
    """

    flags = []

    if tbi_summary is None or tbi_summary.empty:
        return flags

    if "crime_category" not in tbi_summary.columns:
        return flags

    if "latest_reported_count" not in tbi_summary.columns:
        return flags

    summary = tbi_summary.copy()

    if "latest_year" in summary.columns:
        max_year = pd.to_numeric(summary["latest_year"], errors="coerce").max()

        if not pd.isna(max_year) and int(max_year) > END_YEAR:
            add_flag(
                flags=flags,
                flag_type="TBI Year Validation",
                description=(
                    f"TBI context includes a latest_year value of {int(max_year)}, which is beyond "
                    f"the project study end year of {END_YEAR}. Review source-year parsing."
                ),
                severity_score=3,
                metric="TBI latest year validation",
                latest_value=max_year,
                comparison_value=END_YEAR,
                source_layer="TBI / TIBRS Context",
                methodology_scope="Supporting context data-quality flag",
            )

    top_row = summary.sort_values("latest_reported_count", ascending=False).iloc[0]

    add_flag(
        flags=flags,
        flag_type="TBI Financial-Crime Context",
        description=(
            f"The largest TBI financial-crime-adjacent context category was "
            f"{top_row.get('crime_category')} with "
            f"{format_number(top_row.get('latest_reported_count'))} reported "
            f"{top_row.get('count_type', 'records')} in "
            f"{format_year(top_row.get('latest_year', np.nan))}."
        ),
        severity_score=2,
        metric="Top TBI context category",
        latest_value=top_row.get("latest_reported_count"),
        comparison_value=None,
        source_layer="TBI / TIBRS Context",
        methodology_scope="Supporting law-enforcement context",
    )

    identity_rows = summary[
        summary["crime_category"]
        .astype(str)
        .str.lower()
        .str.contains("identity theft", na=False)
    ]

    if not identity_rows.empty:
        row = identity_rows.sort_values("latest_reported_count", ascending=False).iloc[0]

        add_flag(
            flags=flags,
            flag_type="Identity Theft Context",
            description=(
                f"TBI context includes {format_number(row.get('latest_reported_count'))} "
                f"latest-year identity-theft-related reported records, supporting the SAR identity theft "
                f"and elder exploitation theme."
            ),
            severity_score=3,
            metric="TBI identity theft context",
            latest_value=row.get("latest_reported_count"),
            comparison_value=None,
            source_layer="TBI / TIBRS Context",
            methodology_scope="Supporting law-enforcement context",
        )

    fraud_aggregate_rows = summary[
        summary["crime_category"]
        .astype(str)
        .str.lower()
        .eq("fraud offenses")
    ]

    if not fraud_aggregate_rows.empty:
        row = fraud_aggregate_rows.sort_values(
            "latest_reported_count",
            ascending=False,
        ).iloc[0]

        fraud_total = row.get("latest_reported_count")

        add_flag(
            flags=flags,
            flag_type="Fraud Context",
            description=(
                f"TBI context includes {format_number(fraud_total)} latest-year reported "
                "Fraud Offenses. This uses the TBI aggregate Fraud Offenses row to avoid "
                "double counting fraud subcategories."
            ),
            severity_score=2,
            metric="TBI fraud-related context",
            latest_value=fraud_total,
            comparison_value=None,
            source_layer="TBI / TIBRS Context",
            methodology_scope="Supporting law-enforcement context",
        )

    else:
        fraud_rows = summary[
            summary["crime_category"]
            .astype(str)
            .str.lower()
            .str.contains("fraud", na=False)
        ]

        if not fraud_rows.empty:
            fraud_total = fraud_rows["latest_reported_count"].sum()

            add_flag(
                flags=flags,
                flag_type="Fraud Context",
                description=(
                    f"TBI context includes {format_number(fraud_total)} latest-year fraud-related "
                    "reported records across extracted financial-crime-adjacent categories."
                ),
                severity_score=2,
                metric="TBI fraud-related context",
                latest_value=fraud_total,
                comparison_value=None,
                source_layer="TBI / TIBRS Context",
                methodology_scope="Supporting law-enforcement context",
            )

    return flags


def detect_fbi_context_changes(fbi_summary: pd.DataFrame) -> list[dict]:
    """
    Add context flags from the FBI / NIBRS layer.
    """

    flags = []

    if fbi_summary is None or fbi_summary.empty:
        return flags

    if "crime_category" not in fbi_summary.columns:
        return flags

    if "latest_reported_count" not in fbi_summary.columns:
        return flags

    top_row = fbi_summary.sort_values("latest_reported_count", ascending=False).iloc[0]

    add_flag(
        flags=flags,
        flag_type="FBI / NIBRS Context",
        description=(
            f"The largest FBI/NIBRS financial-crime-adjacent category was "
            f"{top_row.get('crime_category')} with "
            f"{format_number(top_row.get('latest_reported_count'))} reported "
            f"{top_row.get('count_type', 'records')} in "
            f"{format_year(top_row.get('latest_year', np.nan))}."
        ),
        severity_score=2,
        metric="Top FBI/NIBRS context category",
        latest_value=top_row.get("latest_reported_count"),
        comparison_value=None,
        source_layer="FBI Crime Data Explorer / NIBRS Context",
        methodology_scope="Supporting law-enforcement context",
    )

    trafficking_rows = fbi_summary[
        fbi_summary["crime_category"]
        .astype(str)
        .str.lower()
        .str.contains("human trafficking", na=False)
    ]

    if not trafficking_rows.empty:
        latest_total = trafficking_rows["latest_reported_count"].sum()

        add_flag(
            flags=flags,
            flag_type="Human Trafficking Context",
            description=(
                f"FBI/NIBRS context includes {format_number(latest_total)} latest-year "
                f"human-trafficking-related records for Tennessee. This supports broader exploitation "
                f"and illicit-finance context, but is not a direct SAR measure."
            ),
            severity_score=2,
            metric="FBI/NIBRS human trafficking context",
            latest_value=latest_total,
            comparison_value=None,
            source_layer="FBI Crime Data Explorer / NIBRS Context",
            methodology_scope="Supporting law-enforcement context",
        )

    return flags


def detect_elder_context_changes(elder_context_summary: pd.DataFrame) -> list[dict]:
    """
    Add context flags from the elder financial exploitation layer.
    """

    flags = []

    if elder_context_summary is None or elder_context_summary.empty:
        return flags

    add_flag(
        flags=flags,
        flag_type="Elder Exploitation Context",
        description=(
            "Elder financial exploitation context is available and links SAR category intelligence "
            "with TBI/FBI law-enforcement context and Tennessee policy/victim-risk framing."
        ),
        severity_score=3,
        metric="Elder exploitation context availability",
        latest_value=len(elder_context_summary),
        comparison_value=None,
        source_layer="Elder Financial Exploitation Context",
        methodology_scope="Supporting policy and victim-risk context",
    )

    if "evidence_type" in elder_context_summary.columns:
        sar_rows = elder_context_summary[
            elder_context_summary["evidence_type"]
            .astype(str)
            .str.contains("SAR Category", na=False)
        ]

        if not sar_rows.empty:
            row = sar_rows.iloc[0]

            add_flag(
                flags=flags,
                flag_type="SAR Elder Exploitation Theme",
                description=(
                    "Elder Financial Exploitation appears in the SAR category context and is supported "
                    "by the elder exploitation narrative layer."
                ),
                severity_score=3,
                metric="SAR elder exploitation theme",
                latest_value=row.get("metric_value", np.nan),
                comparison_value=None,
                source_layer="Elder Financial Exploitation Context",
                methodology_scope="Supporting policy and victim-risk context",
            )

    return flags


def detect_comptroller_context_changes(comptroller_context: pd.DataFrame) -> list[dict]:
    """
    Add context flags from the Tennessee Comptroller public-sector fraud / audit layer.
    """

    flags = []

    if comptroller_context is None or comptroller_context.empty:
        return flags

    add_flag(
        flags=flags,
        flag_type="Comptroller Context Available",
        description=(
            "Tennessee Comptroller public-sector fraud, waste, abuse, and audit context "
            "is available as a supporting public-sector oversight layer."
        ),
        severity_score=1,
        metric="Comptroller context availability",
        latest_value=len(comptroller_context),
        comparison_value=None,
        source_layer="Comptroller Public-Sector Fraud Context",
        methodology_scope="Supporting public-sector fraud and audit context",
    )

    if "metric" not in comptroller_context.columns or "value" not in comptroller_context.columns:
        return flags

    context = comptroller_context.copy()
    context["numeric_value"] = pd.to_numeric(context["value"], errors="coerce")

    hotline_rows = context[
        context["metric"]
        .astype(str)
        .str.lower()
        .str.contains("hotline notifications", na=False)
    ]

    if not hotline_rows.empty:
        row = hotline_rows.iloc[0]
        add_flag(
            flags=flags,
            flag_type="Public-Sector Fraud Reporting",
            description=(
                f"Comptroller context includes {format_number(row.get('numeric_value'))} "
                f"Fraud, Waste & Abuse Hotline notifications in {row.get('period', 'FY2025')}. "
                "This supports public-sector fraud reporting context, not SAR activity."
            ),
            severity_score=2,
            metric="Comptroller hotline notifications",
            latest_value=row.get("numeric_value"),
            comparison_value=None,
            source_layer="Comptroller Public-Sector Fraud Context",
            methodology_scope="Supporting public-sector fraud and audit context",
        )

    allegation_rows = context[
        context["metric"]
        .astype(str)
        .str.lower()
        .str.contains("substantive allegations", na=False)
    ]

    if not allegation_rows.empty:
        row = allegation_rows.iloc[0]
        add_flag(
            flags=flags,
            flag_type="Substantive Allegation Context",
            description=(
                f"Comptroller context includes {format_number(row.get('numeric_value'))} "
                f"substantive allegations in {row.get('period', 'FY2025')}. "
                "These are public-sector oversight context and are not equivalent to SAR filings, "
                "confirmed fraud, charges, or convictions."
            ),
            severity_score=2,
            metric="Comptroller substantive allegations",
            latest_value=row.get("numeric_value"),
            comparison_value=None,
            source_layer="Comptroller Public-Sector Fraud Context",
            methodology_scope="Supporting public-sector fraud and audit context",
        )

    return flags


def get_ofac_summary_value(ofac_summary: pd.DataFrame, metric_name: str) -> float:
    """
    Pull a numeric metric value from OFAC summary.
    """

    if (
        ofac_summary.empty
        or "metric" not in ofac_summary.columns
        or "value" not in ofac_summary.columns
    ):
        return np.nan

    rows = ofac_summary[
        ofac_summary["metric"].astype(str).str.lower().eq(metric_name.lower())
    ]

    if rows.empty:
        return np.nan

    return pd.to_numeric(rows.iloc[0]["value"], errors="coerce")


def detect_ofac_context_changes(ofac_summary: pd.DataFrame) -> list[dict]:
    """
    Add context flags from the OFAC sanctions geography layer.
    """

    flags = []

    if ofac_summary is None or ofac_summary.empty:
        return flags

    if "metric" not in ofac_summary.columns or "value" not in ofac_summary.columns:
        return flags

    total_matches = get_ofac_summary_value(
        ofac_summary,
        "Tennessee OFAC address matches",
    )

    state_matches = get_ofac_summary_value(
        ofac_summary,
        "Match level: state",
    )

    city_county_matches = get_ofac_summary_value(
        ofac_summary,
        "Match level: city_or_county",
    )

    if pd.isna(total_matches):
        return flags

    if total_matches > 0:
        severity = 2
    else:
        severity = 1

    description = (
        f"OFAC sanctions-list address screening identified {format_number(total_matches)} "
        "accepted Tennessee-related address records. "
    )

    if not pd.isna(state_matches) or not pd.isna(city_county_matches):
        description += (
            f"Of these, {format_number(state_matches)} were explicit state-level matches and "
            f"{format_number(city_county_matches)} were U.S.-anchored city/county-level matches. "
        )

    description += (
        "This is sanctions-screening geography context only, not evidence of Tennessee SAR activity, "
        "local criminal activity, or enforcement action."
    )

    add_flag(
        flags=flags,
        flag_type="OFAC Tennessee Address Context",
        description=description,
        severity_score=severity,
        metric="OFAC Tennessee address matches",
        latest_value=total_matches,
        comparison_value=0,
        source_layer="OFAC Sanctions Geography Context",
        methodology_scope="Supporting sanctions-screening context",
    )

    if not pd.isna(city_county_matches) and not pd.isna(state_matches):
        if city_county_matches > state_matches * 5 and city_county_matches > 0:
            add_flag(
                flags=flags,
                flag_type="OFAC Geographic Match Review",
                description=(
                    "Most OFAC Tennessee address matches are city/county-level matches rather than explicit "
                    "TN/Tennessee matches. Review the OFAC matcher for false positives involving city names "
                    "that also appear outside Tennessee."
                ),
                severity_score=3,
                metric="OFAC city/county match concentration",
                latest_value=city_county_matches,
                comparison_value=state_matches,
                source_layer="OFAC Sanctions Geography Context",
                methodology_scope="Supporting sanctions-screening data-quality flag",
            )

    return flags


def build_change_detection_summary(flags_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize flags by source layer, severity, and flag type.
    """

    if flags_df.empty:
        return pd.DataFrame()

    summary = (
        flags_df.groupby(
            [
                "source_layer",
                "methodology_scope",
                "severity",
                "flag_type",
            ],
            as_index=False,
        )
        .agg(
            flag_count=("flag_type", "size"),
            max_severity_score=("severity_score", "max"),
        )
        .sort_values(
            ["max_severity_score", "source_layer", "flag_count"],
            ascending=[False, True, False],
        )
    )

    return summary


def run_change_detection(
    tn_vs_us: pd.DataFrame,
    industry_trend: pd.DataFrame,
    sar_pressure_index: pd.DataFrame,
    tbi_summary: pd.DataFrame | None = None,
    fbi_summary: pd.DataFrame | None = None,
    elder_context_summary: pd.DataFrame | None = None,
    ofac_summary: pd.DataFrame | None = None,
    comptroller_context: pd.DataFrame | None = None,
) -> dict:
    """
    Run change detection across SAR trend, industry, pressure-index,
    law-enforcement context, elder exploitation, OFAC context, and Comptroller context.

    The context-layer inputs are optional so existing main.py calls remain compatible.
    """

    flags = []

    flags.extend(detect_trend_changes(tn_vs_us))
    flags.extend(detect_industry_changes(industry_trend))
    flags.extend(detect_pressure_index_changes(sar_pressure_index))

    flags.extend(detect_tbi_context_changes(tbi_summary))
    flags.extend(detect_fbi_context_changes(fbi_summary))
    flags.extend(detect_elder_context_changes(elder_context_summary))
    flags.extend(detect_ofac_context_changes(ofac_summary))
    flags.extend(detect_comptroller_context_changes(comptroller_context))

    flags_df = pd.DataFrame(flags)

    if not flags_df.empty:
        flags_df = flags_df.sort_values(
            ["severity_score", "source_layer", "flag_type"],
            ascending=[False, True, True],
        )

    summary_df = build_change_detection_summary(flags_df)

    flags_df.to_csv(CHANGE_DETECTION_FLAGS_FILE, index=False)
    summary_df.to_csv(CHANGE_DETECTION_SUMMARY_FILE, index=False)

    print(f"Change detection flags saved to: {CHANGE_DETECTION_FLAGS_FILE}")
    print(f"Change detection summary saved to: {CHANGE_DETECTION_SUMMARY_FILE}")

    return {
        "flags": flags_df,
        "summary": summary_df,
    }