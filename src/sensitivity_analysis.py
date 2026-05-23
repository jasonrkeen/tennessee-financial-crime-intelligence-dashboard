import numpy as np
import pandas as pd

from src.config import TABLES_DIR


SENSITIVITY_RESULTS_FILE = TABLES_DIR / "sar_pressure_sensitivity.csv"


WEIGHT_SCENARIOS = {
    "Base Weighting": {
        "weights": {
            "Tennessee SAR Growth Pressure": 0.30,
            "Recent SAR Momentum": 0.20,
            "Tennessee vs U.S. Divergence": 0.20,
            "Industry Concentration": 0.15,
            "High-Risk Category Context": 0.15,
        },
        "scenario_type": "Base Case",
        "sensitivity_family": "Primary Methodology",
        "rationale": "Uses the primary SAR Pressure Index weighting scheme.",
    },
    "Growth-Heavy Weighting": {
        "weights": {
            "Tennessee SAR Growth Pressure": 0.45,
            "Recent SAR Momentum": 0.25,
            "Tennessee vs U.S. Divergence": 0.10,
            "Industry Concentration": 0.10,
            "High-Risk Category Context": 0.10,
        },
        "scenario_type": "Growth Sensitivity",
        "sensitivity_family": "Trend Pressure",
        "rationale": (
            "Places more emphasis on long-run Tennessee SAR growth and recent SAR momentum."
        ),
    },
    "Recent-Momentum Heavy Weighting": {
        "weights": {
            "Tennessee SAR Growth Pressure": 0.20,
            "Recent SAR Momentum": 0.40,
            "Tennessee vs U.S. Divergence": 0.15,
            "Industry Concentration": 0.10,
            "High-Risk Category Context": 0.15,
        },
        "scenario_type": "Momentum Sensitivity",
        "sensitivity_family": "Trend Pressure",
        "rationale": (
            "Tests whether the index changes materially when recent SAR filing momentum receives more weight."
        ),
    },
    "National-Divergence Heavy Weighting": {
        "weights": {
            "Tennessee SAR Growth Pressure": 0.20,
            "Recent SAR Momentum": 0.15,
            "Tennessee vs U.S. Divergence": 0.40,
            "Industry Concentration": 0.10,
            "High-Risk Category Context": 0.15,
        },
        "scenario_type": "Benchmark Sensitivity",
        "sensitivity_family": "National Benchmark",
        "rationale": (
            "Tests whether Tennessee's indexed divergence from the U.S. SAR trend drives the overall signal."
        ),
    },
    "Industry-Concentration Heavy Weighting": {
        "weights": {
            "Tennessee SAR Growth Pressure": 0.20,
            "Recent SAR Momentum": 0.15,
            "Tennessee vs U.S. Divergence": 0.15,
            "Industry Concentration": 0.35,
            "High-Risk Category Context": 0.15,
        },
        "scenario_type": "Concentration Sensitivity",
        "sensitivity_family": "Filing Channel Concentration",
        "rationale": (
            "Tests whether industry concentration materially changes the SAR Pressure Index signal."
        ),
    },
    "Category-Risk Heavy Weighting": {
        "weights": {
            "Tennessee SAR Growth Pressure": 0.20,
            "Recent SAR Momentum": 0.15,
            "Tennessee vs U.S. Divergence": 0.15,
            "Industry Concentration": 0.10,
            "High-Risk Category Context": 0.40,
        },
        "scenario_type": "Category Context Sensitivity",
        "sensitivity_family": "SAR Theme Context",
        "rationale": (
            "Tests whether high-risk suspicious activity category context materially changes the index. "
            "Category data remains contextual and is not treated as Tennessee-specific category counts."
        ),
    },
}


EXCLUDED_CONTEXT_LAYERS = (
    "TBI/TIBRS offense context; FBI/NIBRS offense context; elder financial exploitation "
    "policy context; TBI Criminal Investigation Division capability context; Comptroller "
    "public-sector fraud/audit context; OFAC sanctions geography context; current indicators"
)


def classify_signal(score: float) -> str:
    """
    Classify SAR Pressure Index score.
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


def normalize_weights(weights: dict) -> dict:
    """
    Normalize weights to sum to 1.
    """

    total_weight = sum(weights.values())

    if total_weight <= 0:
        return weights

    return {
        component: weight / total_weight
        for component, weight in weights.items()
    }


def calculate_weighted_score(
    components: pd.DataFrame,
    weights: dict,
) -> tuple[float, dict, dict]:
    """
    Calculate weighted SAR Pressure Index under a given weight scenario.

    Returns:
    - final score
    - contribution detail
    - normalized weights
    """

    if components.empty:
        return np.nan, {}, {}

    normalized_weights = normalize_weights(weights)

    score_rows = []
    weighted_sum = 0.0
    used_weight_sum = 0.0

    for component, weight in normalized_weights.items():
        match = components[components["component"].eq(component)]

        if match.empty:
            score_rows.append(
                {
                    "component": component,
                    "score": np.nan,
                    "weight": weight,
                    "weighted_score": np.nan,
                }
            )
            continue

        score = match["score"].iloc[0]

        if pd.isna(score):
            score_rows.append(
                {
                    "component": component,
                    "score": np.nan,
                    "weight": weight,
                    "weighted_score": np.nan,
                }
            )
            continue

        weighted_score = score * weight
        weighted_sum += weighted_score
        used_weight_sum += weight

        score_rows.append(
            {
                "component": component,
                "score": score,
                "weight": weight,
                "weighted_score": weighted_score,
            }
        )

    if used_weight_sum <= 0:
        final_score = np.nan
    else:
        final_score = weighted_sum / used_weight_sum

    contribution_detail = {
        row["component"]: row["weighted_score"]
        for row in score_rows
    }

    return final_score, contribution_detail, normalized_weights


def add_stability_metrics(results: pd.DataFrame) -> pd.DataFrame:
    """
    Add stability metrics across sensitivity scenarios.
    """

    if results.empty or "sar_pressure_index" not in results.columns:
        return results

    valid_scores = results["sar_pressure_index"].dropna()

    if valid_scores.empty:
        results["sensitivity_min_score"] = np.nan
        results["sensitivity_max_score"] = np.nan
        results["sensitivity_range"] = np.nan
        results["sensitivity_mean_score"] = np.nan
        results["sensitivity_std_score"] = np.nan
        results["signal_stability_note"] = "Insufficient Data"
        return results

    min_score = valid_scores.min()
    max_score = valid_scores.max()
    mean_score = valid_scores.mean()
    std_score = valid_scores.std(ddof=0)
    score_range = max_score - min_score

    unique_signals = sorted(set(results["signal"].dropna()))

    if len(unique_signals) == 1:
        stability_note = (
            f"Stable signal across tested weighting scenarios: {unique_signals[0]}"
        )
    else:
        stability_note = (
            "Signal varies across tested weighting scenarios: "
            + "; ".join(unique_signals)
        )

    results["sensitivity_min_score"] = min_score
    results["sensitivity_max_score"] = max_score
    results["sensitivity_range"] = score_range
    results["sensitivity_mean_score"] = mean_score
    results["sensitivity_std_score"] = std_score
    results["signal_stability_note"] = stability_note

    return results


def run_sensitivity_analysis(components: pd.DataFrame) -> pd.DataFrame:
    """
    Run SAR Pressure Index sensitivity analysis.

    This function tests whether the SAR Pressure Index signal is stable under
    alternative component weighting assumptions.

    It intentionally uses only SAR Pressure Index components. TBI, FBI, elder
    exploitation, TBI CID, Comptroller, and OFAC layers remain supporting context.
    """

    rows = []

    if components.empty:
        results = pd.DataFrame()
        results.to_csv(SENSITIVITY_RESULTS_FILE, index=False)
        print(f"SAR Pressure sensitivity results saved to: {SENSITIVITY_RESULTS_FILE}")
        return results

    base_score = np.nan

    for scenario_name, scenario_config in WEIGHT_SCENARIOS.items():
        weights = scenario_config["weights"]

        score, contribution_detail, normalized_weights = calculate_weighted_score(
            components=components,
            weights=weights,
        )

        if scenario_name == "Base Weighting":
            base_score = score

        rows.append(
            {
                "weighting_scenario": scenario_name,
                "scenario_type": scenario_config["scenario_type"],
                "sensitivity_family": scenario_config["sensitivity_family"],
                "sar_pressure_index": score,
                "signal": classify_signal(score),
                "difference_from_base": (
                    score - base_score
                    if not pd.isna(score) and not pd.isna(base_score)
                    else np.nan
                ),
                "growth_weight": normalized_weights.get(
                    "Tennessee SAR Growth Pressure",
                    np.nan,
                ),
                "recent_momentum_weight": normalized_weights.get(
                    "Recent SAR Momentum",
                    np.nan,
                ),
                "national_divergence_weight": normalized_weights.get(
                    "Tennessee vs U.S. Divergence",
                    np.nan,
                ),
                "industry_concentration_weight": normalized_weights.get(
                    "Industry Concentration",
                    np.nan,
                ),
                "category_context_weight": normalized_weights.get(
                    "High-Risk Category Context",
                    np.nan,
                ),
                "growth_pressure_contribution": contribution_detail.get(
                    "Tennessee SAR Growth Pressure",
                    np.nan,
                ),
                "recent_momentum_contribution": contribution_detail.get(
                    "Recent SAR Momentum",
                    np.nan,
                ),
                "national_divergence_contribution": contribution_detail.get(
                    "Tennessee vs U.S. Divergence",
                    np.nan,
                ),
                "industry_concentration_contribution": contribution_detail.get(
                    "Industry Concentration",
                    np.nan,
                ),
                "category_context_contribution": contribution_detail.get(
                    "High-Risk Category Context",
                    np.nan,
                ),
                "rationale": scenario_config["rationale"],
                "data_basis": "SAR Pressure Index component table",
                "included_context_layers": "FinCEN SAR Stats trend, industry, and category-context components only",
                "excluded_context_layers": EXCLUDED_CONTEXT_LAYERS,
                "methodology_note": (
                    "Sensitivity analysis reweights SAR Pressure Index components only. "
                    "Supporting TBI, FBI, elder exploitation, TBI CID, Comptroller, and OFAC "
                    "layers are excluded from the sensitivity score."
                ),
            }
        )

    results = pd.DataFrame(rows)
    results = add_stability_metrics(results)

    results.to_csv(SENSITIVITY_RESULTS_FILE, index=False)
    print(f"SAR Pressure sensitivity results saved to: {SENSITIVITY_RESULTS_FILE}")

    return results