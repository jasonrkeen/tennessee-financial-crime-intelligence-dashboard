import numpy as np
import pandas as pd

from src.config import TABLES_DIR


SCENARIO_ASSUMPTIONS_FILE = TABLES_DIR / "sar_scenario_assumptions.csv"
SCENARIO_PROJECTIONS_FILE = TABLES_DIR / "sar_scenario_projections.csv"
SCENARIO_SUMMARY_FILE = TABLES_DIR / "sar_scenario_summary.csv"


def clamp_growth_rate(
    value: float,
    lower: float = -0.10,
    upper: float = 0.25,
) -> float:
    """
    Clamp scenario growth rates to a reasonable range.

    This prevents one unusual year from producing unrealistic projections.
    """

    if pd.isna(value):
        return np.nan

    return max(lower, min(upper, value))


def safe_cagr(start_value: float, end_value: float, periods: int) -> float:
    """
    Calculate CAGR safely.
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


def calculate_recent_growth(tn_vs_us: pd.DataFrame, lookback_years: int = 3) -> float:
    """
    Calculate average recent Tennessee SAR growth over a lookback window.
    """

    if tn_vs_us.empty or "Tennessee" not in tn_vs_us.columns:
        return np.nan

    df = tn_vs_us.sort_values("year").copy()

    if len(df) < 2:
        return np.nan

    recent = df.tail(lookback_years + 1).copy()
    recent["growth"] = recent["Tennessee"].pct_change()

    return recent["growth"].dropna().mean()


def calculate_long_run_growth(tn_vs_us: pd.DataFrame) -> float:
    """
    Calculate long-run Tennessee SAR CAGR.
    """

    if tn_vs_us.empty or "Tennessee" not in tn_vs_us.columns:
        return np.nan

    df = tn_vs_us.sort_values("year").copy()

    if df.empty:
        return np.nan

    start_row = df.iloc[0]
    end_row = df.iloc[-1]

    periods = int(end_row["year"] - start_row["year"])

    return safe_cagr(
        start_value=start_row["Tennessee"],
        end_value=end_row["Tennessee"],
        periods=periods,
    )


def calculate_us_recent_growth(tn_vs_us: pd.DataFrame, lookback_years: int = 3) -> float:
    """
    Calculate average recent U.S. SAR growth over a lookback window.
    """

    if tn_vs_us.empty or "United States / Total" not in tn_vs_us.columns:
        return np.nan

    df = tn_vs_us.sort_values("year").copy()

    if len(df) < 2:
        return np.nan

    recent = df.tail(lookback_years + 1).copy()
    recent["growth"] = recent["United States / Total"].pct_change()

    return recent["growth"].dropna().mean()


def build_scenario_assumptions(tn_vs_us: pd.DataFrame) -> pd.DataFrame:
    """
    Build scenario assumptions from historical Tennessee and U.S. SAR trends.

    Scenarios:
    - Baseline Continuation: Tennessee long-run CAGR
    - Recent Momentum: Tennessee recent average growth
    - National Convergence: U.S. recent average growth
    - Fraud / Digital Payments Acceleration: recent Tennessee growth plus acceleration
    - Lower-Growth Monitoring Case: lower but positive growth

    Note:
    TBI, FBI, elder exploitation, TBI CID, Comptroller, and OFAC context layers
    are not used to set projection rates. They support interpretation only.
    """

    long_run_growth = calculate_long_run_growth(tn_vs_us)
    recent_growth = calculate_recent_growth(tn_vs_us, lookback_years=3)
    us_recent_growth = calculate_us_recent_growth(tn_vs_us, lookback_years=3)

    if pd.isna(long_run_growth):
        long_run_growth = 0.04

    if pd.isna(recent_growth):
        recent_growth = long_run_growth

    if pd.isna(us_recent_growth):
        us_recent_growth = long_run_growth

    long_run_growth = clamp_growth_rate(long_run_growth)
    recent_growth = clamp_growth_rate(recent_growth)
    us_recent_growth = clamp_growth_rate(us_recent_growth)

    assumptions = pd.DataFrame(
        [
            {
                "scenario": "Baseline Continuation",
                "annual_growth_rate": long_run_growth,
                "scenario_family": "Historical Trend",
                "scenario_type": "Base Case",
                "pressure_direction": "Continuation",
                "risk_theme": "SAR filing trend continuation",
                "data_basis": "FinCEN SAR Stats Tennessee long-run SAR trend",
                "rationale": (
                    "Projects Tennessee SAR filings forward using the long-run "
                    "historical CAGR from the study period."
                ),
                "methodology_note": (
                    "Uses the full Tennessee SAR trend from the first available study year "
                    "through the latest available year."
                ),
            },
            {
                "scenario": "Recent Momentum",
                "annual_growth_rate": recent_growth,
                "scenario_family": "Historical Trend",
                "scenario_type": "Recent Trend Case",
                "pressure_direction": "Recent Trend",
                "risk_theme": "Near-term SAR filing momentum",
                "data_basis": "FinCEN SAR Stats Tennessee recent YoY SAR trend",
                "rationale": (
                    "Uses Tennessee's average recent SAR growth rate to reflect "
                    "near-term filing momentum."
                ),
                "methodology_note": (
                    "Uses the average Tennessee year-over-year growth rate over the most recent "
                    "three-year lookback window where data is available."
                ),
            },
            {
                "scenario": "National Convergence",
                "annual_growth_rate": us_recent_growth,
                "scenario_family": "Benchmark Trend",
                "scenario_type": "Benchmark Case",
                "pressure_direction": "Convergence",
                "risk_theme": "Tennessee convergence toward national SAR momentum",
                "data_basis": "FinCEN SAR Stats recent U.S. SAR filing trend",
                "rationale": (
                    "Assumes Tennessee SAR growth begins to move closer to recent "
                    "national SAR filing growth."
                ),
                "methodology_note": (
                    "Uses recent U.S. SAR filing growth as a benchmark growth path. "
                    "This is a benchmark scenario, not a prediction."
                ),
            },
            {
                "scenario": "Fraud / Digital Payments Acceleration",
                "annual_growth_rate": clamp_growth_rate(
                    recent_growth + 0.05,
                    lower=-0.05,
                    upper=0.25,
                ),
                "scenario_family": "Upside Pressure",
                "scenario_type": "Upside Pressure Case",
                "pressure_direction": "Higher Pressure",
                "risk_theme": "Fraud, wire/EFT activity, identity theft, elder exploitation, and digital payments",
                "data_basis": (
                    "FinCEN SAR Stats recent Tennessee momentum plus transparent acceleration assumption"
                ),
                "rationale": (
                    "Assumes higher filing pressure from fraud, wire/EFT activity, "
                    "identity theft, elder exploitation, and digital-payment related monitoring."
                ),
                "methodology_note": (
                    "Adds a five-percentage-point acceleration factor to recent Tennessee momentum, "
                    "with an upper cap to avoid unrealistic growth assumptions. Supporting TBI, FBI, "
                    "elder exploitation, and other context layers inform the narrative but do not set the rate."
                ),
            },
            {
                "scenario": "Lower-Growth Monitoring Case",
                "annual_growth_rate": clamp_growth_rate(
                    max(long_run_growth - 0.03, 0.00),
                    lower=0.00,
                    upper=0.15,
                ),
                "scenario_family": "Downside / Monitoring",
                "scenario_type": "Lower Pressure Case",
                "pressure_direction": "Lower Pressure",
                "risk_theme": "Slower filing-growth environment",
                "data_basis": "FinCEN SAR Stats Tennessee long-run SAR trend with downside adjustment",
                "rationale": (
                    "Assumes Tennessee SAR filings continue to grow, but at a slower "
                    "rate than the long-run historical trend."
                ),
                "methodology_note": (
                    "Reduces the long-run Tennessee SAR CAGR by three percentage points, "
                    "floored at zero growth."
                ),
            },
        ]
    )

    assumptions = assumptions.sort_values(
        ["annual_growth_rate", "scenario"],
        ascending=[False, True],
    ).reset_index(drop=True)

    assumptions["growth_rank"] = assumptions["annual_growth_rate"].rank(
        ascending=False,
        method="dense",
    ).astype(int)

    assumptions["included_context_layers"] = (
        "FinCEN SAR Stats trend data only for rate-setting"
    )

    assumptions["excluded_from_rate_setting"] = (
        "TBI/TIBRS offense context; FBI/NIBRS offense context; elder financial exploitation "
        "policy context; TBI Criminal Investigation Division capability context; Comptroller "
        "public-sector fraud/audit context; OFAC sanctions geography context"
    )

    assumptions.to_csv(SCENARIO_ASSUMPTIONS_FILE, index=False)
    print(f"SAR scenario assumptions saved to: {SCENARIO_ASSUMPTIONS_FILE}")

    return assumptions


def project_sar_filings(
    latest_year: int,
    latest_filings: float,
    annual_growth_rate: float,
    projection_years: list[int],
) -> list[dict]:
    """
    Project SAR filings forward for one scenario.
    """

    rows = []

    for year in projection_years:
        years_forward = year - latest_year
        projected_value = latest_filings * ((1 + annual_growth_rate) ** years_forward)

        rows.append(
            {
                "year": int(year),
                "years_forward": int(years_forward),
                "projected_sar_filings": projected_value,
            }
        )

    return rows


def build_scenario_projections(
    tn_vs_us: pd.DataFrame,
    projection_horizon: int = 3,
) -> pd.DataFrame:
    """
    Build Tennessee SAR scenario projections.
    """

    if tn_vs_us.empty or "Tennessee" not in tn_vs_us.columns:
        return pd.DataFrame()

    df = tn_vs_us.sort_values("year").copy()
    latest_row = df.iloc[-1]

    latest_year = int(latest_row["year"])
    latest_filings = latest_row["Tennessee"]

    if pd.isna(latest_filings) or latest_filings <= 0:
        return pd.DataFrame()

    projection_years = list(
        range(latest_year + 1, latest_year + projection_horizon + 1)
    )

    assumptions = build_scenario_assumptions(tn_vs_us)

    rows = []

    for _, scenario_row in assumptions.iterrows():
        scenario = scenario_row["scenario"]
        annual_growth_rate = scenario_row["annual_growth_rate"]

        projected_rows = project_sar_filings(
            latest_year=latest_year,
            latest_filings=latest_filings,
            annual_growth_rate=annual_growth_rate,
            projection_years=projection_years,
        )

        for projected in projected_rows:
            rows.append(
                {
                    "scenario": scenario,
                    "scenario_family": scenario_row["scenario_family"],
                    "scenario_type": scenario_row["scenario_type"],
                    "pressure_direction": scenario_row["pressure_direction"],
                    "risk_theme": scenario_row["risk_theme"],
                    "growth_rank": scenario_row["growth_rank"],
                    "rationale": scenario_row["rationale"],
                    "methodology_note": scenario_row["methodology_note"],
                    "data_basis": scenario_row["data_basis"],
                    "included_context_layers": scenario_row["included_context_layers"],
                    "excluded_from_rate_setting": scenario_row["excluded_from_rate_setting"],
                    "base_year": latest_year,
                    "base_year_filings": latest_filings,
                    "annual_growth_rate": annual_growth_rate,
                    "year": projected["year"],
                    "years_forward": projected["years_forward"],
                    "projected_sar_filings": projected["projected_sar_filings"],
                    "projected_change_from_base": (
                        projected["projected_sar_filings"] - latest_filings
                    ),
                    "projected_pct_change_from_base": (
                        projected["projected_sar_filings"] / latest_filings - 1
                        if latest_filings > 0
                        else np.nan
                    ),
                }
            )

    projections = pd.DataFrame(rows)

    if not projections.empty:
        projections = projections.sort_values(
            ["year", "growth_rank", "scenario"],
            ascending=[True, True, True],
        )

    projections.to_csv(SCENARIO_PROJECTIONS_FILE, index=False)
    print(f"SAR scenario projections saved to: {SCENARIO_PROJECTIONS_FILE}")

    return projections


def summarize_scenarios(projections: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize final-year projected SAR filings by scenario.
    """

    if projections.empty:
        return pd.DataFrame()

    final_year = int(projections["year"].max())

    summary = (
        projections[projections["year"].eq(final_year)]
        .copy()
        .sort_values("projected_sar_filings", ascending=False)
    )

    summary = summary[
        [
            "scenario",
            "scenario_family",
            "scenario_type",
            "pressure_direction",
            "risk_theme",
            "growth_rank",
            "base_year",
            "base_year_filings",
            "year",
            "annual_growth_rate",
            "projected_sar_filings",
            "projected_change_from_base",
            "projected_pct_change_from_base",
            "rationale",
            "methodology_note",
            "data_basis",
            "included_context_layers",
            "excluded_from_rate_setting",
        ]
    ].rename(
        columns={
            "year": "projection_year",
            "projected_sar_filings": "final_projected_sar_filings",
            "projected_change_from_base": "final_projected_change_from_base",
            "projected_pct_change_from_base": "final_projected_pct_change_from_base",
        }
    )

    summary.to_csv(SCENARIO_SUMMARY_FILE, index=False)
    print(f"SAR scenario summary saved to: {SCENARIO_SUMMARY_FILE}")

    return summary


def run_scenario_analysis(
    tn_vs_us: pd.DataFrame,
    projection_horizon: int = 3,
) -> dict:
    """
    Run Tennessee SAR scenario analysis.
    """

    projections = build_scenario_projections(
        tn_vs_us=tn_vs_us,
        projection_horizon=projection_horizon,
    )

    summary = summarize_scenarios(projections)

    return {
        "scenario_projections": projections,
        "scenario_summary": summary,
    }