import pandas as pd

from src.config import (
    CURRENT_INDICATORS_CONTEXT_FILE,
    CURRENT_INDICATORS_FLAGS_FILE,
)


CURRENT_INDICATOR_ROWS = [
    {
        "indicator_theme": "Study Period Boundary",
        "indicator_name": "Core SAR trend study period",
        "indicator_value": "2014-2024",
        "indicator_period": "Core study period",
        "data_type": "Methodology boundary",
        "source": "Project methodology",
        "data_basis": (
            "The core SAR trend model uses comparable FinCEN SAR Stats annual data "
            "through 2024."
        ),
        "interpretation": (
            "The SAR Pressure Index, Tennessee-vs-U.S. trend comparison, and industry "
            "concentration analysis remain anchored to the 2014-2024 study period."
        ),
        "report_use": (
            "Use to clearly separate the core model from newer current-indicator context."
        ),
        "methodology_note": "This is a methodology boundary, not a data signal.",
    },
    {
        "indicator_theme": "TBI Current Context",
        "indicator_name": "TBI Criminal Investigation Division activity",
        "indicator_value": "2025",
        "indicator_period": "2025",
        "data_type": "Investigative capability context",
        "source": "TBI Criminal Investigation Division 2025 material",
        "data_basis": (
            "TBI Criminal Investigation Division reporting on major cases, investigative "
            "assists, intelligence reports, arrests, public corruption, large-scale financial "
            "crime, and human trafficking investigative support."
        ),
        "interpretation": (
            "TBI 2025 material provides current investigative-capability context for complex "
            "financial crime, public corruption, exploitation, and multi-agency intelligence work."
        ),
        "report_use": (
            "Use in a Looking Forward section as current investigative-capability context, "
            "not as a SAR trend extension."
        ),
        "methodology_note": (
            "This is not SAR filing data and is not included in the SAR Pressure Index."
        ),
    },
    {
        "indicator_theme": "Comptroller Current Context",
        "indicator_name": "Fraud, Waste & Abuse Hotline notifications",
        "indicator_value": 1074,
        "indicator_period": "FY2025",
        "data_type": "Public-sector fraud reporting context",
        "source": "Tennessee Comptroller Department of Audit 2025 Annual Report",
        "data_basis": (
            "Comptroller annual report disclosure on Fraud, Waste & Abuse Hotline activity."
        ),
        "interpretation": (
            "The Comptroller reported 1,074 Fraud, Waste & Abuse Hotline notifications "
            "during FY2025, providing a current public-sector fraud reporting indicator."
        ),
        "report_use": "Use as current public-sector fraud and internal-control context.",
        "methodology_note": (
            "This is allegation/reporting context, not SAR data, confirmed fraud, charges, "
            "or convictions."
        ),
    },
    {
        "indicator_theme": "Comptroller Current Context",
        "indicator_name": "Substantive allegations",
        "indicator_value": 1000,
        "indicator_period": "FY2025",
        "data_type": "Public-sector fraud reporting context",
        "source": "Tennessee Comptroller Department of Audit 2025 Annual Report",
        "data_basis": (
            "Comptroller annual report disclosure on substantive allegations received."
        ),
        "interpretation": (
            "The Comptroller reported 1,000 substantive allegations during FY2025, supporting "
            "public-sector fraud as a current Tennessee financial-intelligence context theme."
        ),
        "report_use": (
            "Use in the Looking Forward section as public-sector fraud reporting context."
        ),
        "methodology_note": (
            "These allegations are not equivalent to SAR filings, confirmed crimes, charges, "
            "or convictions."
        ),
    },
    {
        "indicator_theme": "OFAC Current Context",
        "indicator_name": "Current OFAC sanctions geography screening",
        "indicator_value": "Current downloaded OFAC files",
        "indicator_period": "Current list date at runtime",
        "data_type": "Sanctions-screening current indicator",
        "source": "OFAC SDN and Consolidated Non-SDN public address files",
        "data_basis": (
            "OFAC sanctions-list address files downloaded during the project runtime and screened "
            "for accepted Tennessee-related address indicators."
        ),
        "interpretation": (
            "OFAC screening provides a current sanctions-geography context layer. Accepted matches "
            "require explicit Tennessee, TN with clear U.S. country support, or U.S.-anchored "
            "city/county validation."
        ),
        "report_use": "Use as current sanctions-screening geography context.",
        "methodology_note": (
            "OFAC address matches do not indicate Tennessee SAR activity, confirmed local criminal "
            "activity, or enforcement action."
        ),
    },
    {
        "indicator_theme": "FinCEN Current Data Availability",
        "indicator_name": "Future SAR Stats extension check",
        "indicator_value": "Pending comparable 2025/2026 FinCEN SAR Stats release",
        "indicator_period": "2025-2026",
        "data_type": "SAR comparable data availability",
        "source": "FinCEN SAR Stats publication structure",
        "data_basis": (
            "The core SAR trend model should only be extended when comparable annual state/industry "
            "FinCEN SAR Stats data is available."
        ),
        "interpretation": (
            "If FinCEN releases comparable 2025 or 2026 state/industry SAR Stats workbooks, the core "
            "trend model can be extended. Until then, 2025-2026 items should remain current indicators."
        ),
        "report_use": (
            "Use to explain why newer non-SAR sources are included separately from the core SAR model."
        ),
        "methodology_note": (
            "Do not blend non-comparable current indicators into the SAR Pressure Index."
        ),
    },
]


def format_number(value) -> str:
    """
    Format numeric values safely.
    """

    numeric_value = pd.to_numeric(value, errors="coerce")

    if pd.isna(numeric_value):
        return str(value)

    return f"{numeric_value:,.0f}"


def build_current_indicators_context() -> pd.DataFrame:
    """
    Build the Looking Forward / Current Indicators context table.

    This layer keeps newer 2025-2026 context separate from the core
    2014-2024 SAR trend model.
    """

    context = pd.DataFrame(CURRENT_INDICATOR_ROWS)

    context.to_csv(CURRENT_INDICATORS_CONTEXT_FILE, index=False)
    print(f"Current indicators context saved to: {CURRENT_INDICATORS_CONTEXT_FILE}")

    return context


def build_current_indicators_flags(context: pd.DataFrame) -> pd.DataFrame:
    """
    Build flags for the Looking Forward / Current Indicators section.
    """

    flags = []

    if context.empty:
        flags.append(
            {
                "flag_type": "Current Indicators Missing",
                "severity": "Informational",
                "description": "No current indicators context was created.",
                "methodology_scope": "Looking-forward context data-quality flag",
            }
        )
    else:
        flags.append(
            {
                "flag_type": "Current Indicators Available",
                "severity": "Informational",
                "description": (
                    "Looking-forward 2025-2026 current indicators are included as a separate "
                    "context section, not as part of the core SAR trend model."
                ),
                "methodology_scope": "Looking-forward context",
            }
        )

        flags.append(
            {
                "flag_type": "Core Model Boundary",
                "severity": "Informational",
                "description": (
                    "The core SAR trend model remains anchored to 2014-2024 FinCEN SAR Stats data. "
                    "Current indicators are used only to provide forward-looking context."
                ),
                "methodology_scope": "Model boundary",
            }
        )

        flags.append(
            {
                "flag_type": "Comparable SAR Data Requirement",
                "severity": "Informational",
                "description": (
                    "The core SAR model should only be extended beyond 2024 if comparable "
                    "FinCEN state/industry SAR Stats data is available."
                ),
                "methodology_scope": "SAR model limitation",
            }
        )

    flags_df = pd.DataFrame(flags)
    flags_df.to_csv(CURRENT_INDICATORS_FLAGS_FILE, index=False)

    print(f"Current indicators flags saved to: {CURRENT_INDICATORS_FLAGS_FILE}")

    return flags_df


def run_current_indicators_analysis() -> dict:
    """
    Run the Looking Forward / Current Indicators layer.
    """

    context = build_current_indicators_context()
    flags = build_current_indicators_flags(context)

    return {
        "current_indicators_context": context,
        "current_indicators_flags": flags,
    }