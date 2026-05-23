import numpy as np
import pandas as pd

from src.config import TABLES_DIR


SAR_PRESSURE_INDEX_FILE = TABLES_DIR / "sar_pressure_index.csv"
SAR_PRESSURE_COMPONENTS_FILE = TABLES_DIR / "sar_pressure_components.csv"


def clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    """
    Clamp a numeric value between lower and upper bounds.
    """

    if pd.isna(value):
        return np.nan

    return max(lower, min(upper, value))


def score_growth(total_growth_pct: float) -> float:
    """
    Score SAR growth pressure.

    Interpretation:
    - 0% growth maps to 0
    - 100% growth maps to about 66.7
    - 150%+ growth maps to 100
    """

    if pd.isna(total_growth_pct):
        return np.nan

    return clamp((total_growth_pct / 1.5) * 100)


def score_national_divergence(latest_index_gap: float) -> float:
    """
    Score Tennessee vs U.S. divergence.

    Positive gap means Tennessee SAR growth is outpacing the U.S.
    Negative gap means Tennessee is growing slower than the U.S.

    For intelligence pressure, slower-than-national growth is not zero risk,
    but it receives a lower score.
    """

    if pd.isna(latest_index_gap):
        return np.nan

    return clamp(50 + latest_index_gap)


def score_industry_concentration(latest_top_industry_share: float) -> float:
    """
    Score industry concentration risk.

    Higher concentration in one industry suggests SAR pressure is concentrated
    and may require focused monitoring.
    """

    if pd.isna(latest_top_industry_share):
        return np.nan

    return clamp(latest_top_industry_share * 100)


def score_high_risk_category_context(category_summary: pd.DataFrame) -> float:
    """
    Score suspicious activity risk-theme context.

    Because category data is not Tennessee-specific in this project phase,
    this score is a contextual SAR theme signal based on the presence and scale
    of high-risk suspicious activity categories in FinCEN industry exhibits.

    If risk_tier exists, Elevated Context and High-Risk Context categories are used.
    Otherwise, high_risk_flag is used for backward compatibility.
    """

    if category_summary.empty or "end_filings" not in category_summary.columns:
        return np.nan

    category_summary = category_summary.copy()

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
        return np.nan

    if high_risk.empty:
        return 0.0

    total_latest = category_summary["end_filings"].sum()
    high_risk_latest = high_risk["end_filings"].sum()

    if total_latest <= 0:
        return np.nan

    high_risk_share = high_risk_latest / total_latest

    return clamp(high_risk_share * 100)


def score_recent_momentum(tn_vs_us: pd.DataFrame) -> float:
    """
    Score recent Tennessee SAR momentum using the latest YoY growth value.

    - Negative growth maps below 50
    - Flat growth maps to 50
    - 20%+ latest YoY growth maps near 100
    """

    if tn_vs_us.empty or "tn_yoy_growth" not in tn_vs_us.columns:
        return np.nan

    latest = tn_vs_us.sort_values("year").iloc[-1]
    latest_growth = latest["tn_yoy_growth"]

    if pd.isna(latest_growth):
        return np.nan

    return clamp(50 + latest_growth * 250)


def classify_sar_pressure_signal(score: float) -> str:
    """
    Convert SAR Pressure Index score into an intelligence signal.
    """

    if pd.isna(score):
        return "Insufficient Data"

    if score >= 75:
        return "Elevated SAR Pressure"

    if score >= 50:
        return "Moderate SAR Pressure"

    if score >= 25:
        return "Watchlist / Lower Relative Pressure"

    return "Low Relative SAR Pressure"


def build_component_row(
    component: str,
    score: float,
    weight: float,
    raw_value,
    interpretation: str,
    data_basis: str,
    methodology_note: str,
    included_in_index: bool = True,
) -> dict:
    """
    Build a standardized SAR Pressure Index component row.
    """

    weighted_score = score * weight if not pd.isna(score) else np.nan

    return {
        "component": component,
        "score": score,
        "weight": weight,
        "weighted_score": weighted_score,
        "raw_value": raw_value,
        "data_basis": data_basis,
        "interpretation": interpretation,
        "methodology_note": methodology_note,
        "included_in_index": included_in_index,
    }


def build_sar_pressure_index(
    tn_vs_us: pd.DataFrame,
    industry_summary: pd.DataFrame,
    category_summary: pd.DataFrame,
) -> dict:
    """
    Build the Tennessee SAR Pressure Index.

    Components:
    - Tennessee SAR growth
    - Recent Tennessee SAR momentum
    - Tennessee vs U.S. indexed divergence
    - Industry concentration
    - High-risk suspicious activity category context

    Important:
    TBI, FBI, elder financial exploitation, TBI CID, Comptroller, and OFAC datasets
    are intentionally excluded from this index. They are supporting context layers
    because they measure law-enforcement reported offenses, investigative capability,
    public-sector oversight, policy/victim-risk context, and sanctions-list address
    indicators rather than SAR filing pressure.
    """

    if tn_vs_us.empty:
        return {
            "components": pd.DataFrame(),
            "index": pd.DataFrame(),
        }

    trend_df = tn_vs_us.sort_values("year").copy()

    if "Tennessee" not in trend_df.columns:
        return {
            "components": pd.DataFrame(),
            "index": pd.DataFrame(),
        }

    start_row = trend_df.iloc[0]
    latest_row = trend_df.iloc[-1]

    tn_growth = (
        (latest_row["Tennessee"] - start_row["Tennessee"]) / start_row["Tennessee"]
        if start_row["Tennessee"] > 0
        else np.nan
    )

    latest_index_gap = latest_row.get("tn_minus_us_index_gap", np.nan)

    if not industry_summary.empty and "latest_year_share" in industry_summary.columns:
        top_industry_share = industry_summary["latest_year_share"].max()
    else:
        top_industry_share = np.nan

    category_score = score_high_risk_category_context(category_summary)

    components = [
        build_component_row(
            component="Tennessee SAR Growth Pressure",
            score=score_growth(tn_growth),
            weight=0.30,
            raw_value=tn_growth,
            interpretation="Long-run increase in Tennessee SAR filings.",
            data_basis="FinCEN SAR Stats Tennessee annual filing trend",
            methodology_note=(
                "Measures SAR filing growth from the first study year to the latest year."
            ),
        ),
        build_component_row(
            component="Recent SAR Momentum",
            score=score_recent_momentum(tn_vs_us),
            weight=0.20,
            raw_value=latest_row.get("tn_yoy_growth", np.nan),
            interpretation="Latest year-over-year Tennessee SAR filing growth.",
            data_basis="FinCEN SAR Stats Tennessee latest YoY growth",
            methodology_note=(
                "Captures whether the latest year shows accelerating or slowing SAR filing pressure."
            ),
        ),
        build_component_row(
            component="Tennessee vs U.S. Divergence",
            score=score_national_divergence(latest_index_gap),
            weight=0.20,
            raw_value=latest_index_gap,
            interpretation="Indexed Tennessee SAR growth relative to the U.S. trend.",
            data_basis="FinCEN SAR Stats Tennessee and U.S. indexed SAR trend",
            methodology_note=(
                "Compares Tennessee's indexed growth path against the national indexed growth path."
            ),
        ),
        build_component_row(
            component="Industry Concentration",
            score=score_industry_concentration(top_industry_share),
            weight=0.15,
            raw_value=top_industry_share,
            interpretation="Share of latest Tennessee SAR filings from the largest filing industry.",
            data_basis="FinCEN SAR Stats Tennessee industry-level filing trend",
            methodology_note=(
                "Higher concentration indicates that SAR pressure is more dependent on one filing-industry channel."
            ),
        ),
        build_component_row(
            component="High-Risk Category Context",
            score=category_score,
            weight=0.15,
            raw_value=np.nan,
            interpretation=(
                "Contextual signal from elevated and high-risk suspicious activity themes "
                "in FinCEN category exhibits."
            ),
            data_basis="FinCEN SAR Stats suspicious activity category exhibits",
            methodology_note=(
                "Category exhibits are treated as SAR-theme context, not Tennessee-specific category counts. "
                "If available, category risk tiers are used to identify elevated and high-risk context themes."
            ),
        ),
    ]

    components_df = pd.DataFrame(components)

    valid_components = components_df.dropna(subset=["weighted_score", "weight"]).copy()

    if valid_components.empty:
        overall_score = np.nan
    else:
        overall_score = (
            valid_components["weighted_score"].sum()
            / valid_components["weight"].sum()
        )

    signal = classify_sar_pressure_signal(overall_score)

    index_df = pd.DataFrame(
        [
            {
                "state": "Tennessee",
                "latest_year": int(latest_row["year"]),
                "sar_pressure_index": overall_score,
                "signal": signal,
                "methodology_scope": (
                    "SAR-based index only. TBI, FBI, elder exploitation, TBI CID, "
                    "Comptroller, and OFAC layers are supporting context and are not "
                    "included in the score."
                ),
                "excluded_context_layers": (
                    "TBI/TIBRS offense context; FBI/NIBRS offense context; elder financial "
                    "exploitation policy context; TBI Criminal Investigation Division capability "
                    "context; Comptroller public-sector fraud/audit context; OFAC sanctions geography context."
                ),
            }
        ]
    )

    components_df.to_csv(SAR_PRESSURE_COMPONENTS_FILE, index=False)
    index_df.to_csv(SAR_PRESSURE_INDEX_FILE, index=False)

    print(f"SAR Pressure Index saved to: {SAR_PRESSURE_INDEX_FILE}")
    print(f"SAR Pressure components saved to: {SAR_PRESSURE_COMPONENTS_FILE}")

    return {
        "components": components_df,
        "index": index_df,
    }