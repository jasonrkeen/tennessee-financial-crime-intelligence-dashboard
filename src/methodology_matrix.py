import pandas as pd

from src.config import METHODOLOGY_MATRIX_FILE


METHODOLOGY_ROWS = [
    {
        "layer": "FinCEN SAR Stats",
        "source": "FinCEN SAR Stats public filing-industry workbooks",
        "what_it_measures": (
            "Aggregated SAR filing activity by year, filing industry, state ranking, "
            "and suspicious activity category exhibits."
        ),
        "project_use": (
            "Core model layer for Tennessee SAR trends, Tennessee-vs-U.S. comparison, "
            "industry concentration, category context, SAR Pressure Index, scenario analysis, "
            "sensitivity analysis, and change detection."
        ),
        "included_in_sar_pressure_index": "Yes",
        "primary_outputs": (
            "trend_summary.csv; industry_summary.csv; sar_pressure_index.csv; "
            "sar_pressure_components.csv; sar_scenario_summary.csv"
        ),
        "key_limitation": (
            "SAR filings measure reporting activity and monitoring behavior, not confirmed "
            "financial crime. Category exhibits are contextual and should not be treated as "
            "Tennessee-specific category counts unless explicitly supported by the source."
        ),
    },
    {
        "layer": "TBI / TIBRS Context",
        "source": "Tennessee Bureau of Investigation / TIBRS statewide 2024 context",
        "what_it_measures": (
            "Law-enforcement reported offense counts for financial-crime-adjacent categories "
            "such as fraud, identity theft, wire fraud, extortion, embezzlement, bribery, "
            "and human trafficking."
        ),
        "project_use": (
            "Supporting law-enforcement context for interpreting SAR themes and Tennessee "
            "financial-crime-adjacent risk indicators."
        ),
        "included_in_sar_pressure_index": "No",
        "primary_outputs": (
            "tbi_financial_crime_context_summary.csv; "
            "tbi_financial_crime_context_flags.csv"
        ),
        "key_limitation": (
            "TBI/TIBRS offense counts are not SAR filings and should not be blended into "
            "the SAR Pressure Index."
        ),
    },
    {
        "layer": "FBI Crime Data Explorer / NIBRS Context",
        "source": "FBI Crime Data Explorer / NIBRS flat-file exports and human trafficking data",
        "what_it_measures": (
            "Federal NIBRS offense context for Tennessee financial-crime-adjacent categories "
            "and human trafficking indicators."
        ),
        "project_use": (
            "Supporting federal law-enforcement context to compare with TBI/TIBRS themes "
            "and broaden the exploitation and fraud-risk discussion."
        ),
        "included_in_sar_pressure_index": "No",
        "primary_outputs": (
            "fbi_financial_crime_context_summary.csv; "
            "fbi_financial_crime_context_flags.csv"
        ),
        "key_limitation": (
            "FBI/NIBRS data measures reported offenses, not SAR filings, confirmed convictions, "
            "or transaction-level illicit finance."
        ),
    },
    {
        "layer": "Elder Financial Exploitation Context",
        "source": "FinCEN category context, TBI/FBI context, and elder-exploitation policy framing",
        "what_it_measures": (
            "Victim-risk and policy context around elder exploitation, identity theft, fraud, "
            "account takeover, coercion, and exploitation-related financial crime."
        ),
        "project_use": (
            "Supporting narrative and risk-context layer that connects SAR category intelligence "
            "with TBI/FBI law-enforcement indicators."
        ),
        "included_in_sar_pressure_index": "No",
        "primary_outputs": (
            "elder_financial_exploitation_context.csv; "
            "elder_financial_exploitation_flags.csv"
        ),
        "key_limitation": (
            "This layer supports interpretation only. It is not a direct Tennessee SAR category "
            "count and is not a SAR Pressure Index input."
        ),
    },
    {
        "layer": "Tennessee Comptroller Context",
        "source": "Tennessee Comptroller Department of Audit FY2025 public-sector fraud materials",
        "what_it_measures": (
            "Public-sector fraud, waste, abuse hotline notifications, substantive allegations, "
            "intake channels, audit context, and oversight pathways."
        ),
        "project_use": (
            "Supporting public-sector fraud and internal-control context for Tennessee financial "
            "crime intelligence."
        ),
        "included_in_sar_pressure_index": "No",
        "primary_outputs": (
            "comptroller_public_sector_fraud_context.csv; "
            "comptroller_public_sector_fraud_flags.csv"
        ),
        "key_limitation": (
            "Comptroller indicators are allegation/reporting and oversight context. They are not "
            "SAR filings, confirmed fraud, charges, or convictions."
        ),
    },
    {
        "layer": "OFAC Sanctions Geography Context",
        "source": "OFAC SDN and Consolidated Non-SDN public address files",
        "what_it_measures": (
            "Current sanctions-list address records screened for accepted Tennessee-related "
            "geography indicators."
        ),
        "project_use": (
            "Supporting sanctions-screening geography context. Used to identify whether current "
            "OFAC public address files contain accepted Tennessee-related address indicators."
        ),
        "included_in_sar_pressure_index": "No",
        "primary_outputs": (
            "ofac_tennessee_address_matches.csv; "
            "ofac_tennessee_context_summary.csv; "
            "ofac_tennessee_context_flags.csv"
        ),
        "key_limitation": (
            "OFAC address matches do not indicate Tennessee SAR activity, local criminal activity, "
            "or enforcement action. TN-only matches require clear U.S. support to avoid false positives."
        ),
    },
    {
        "layer": "Current Indicators / Looking Forward",
        "source": "Current public indicators from TBI, Comptroller, OFAC, and FinCEN release monitoring",
        "what_it_measures": (
            "Forward-looking 2025-2026 context that is newer than the 2014-2024 core SAR model."
        ),
        "project_use": (
            "Keeps the report current while preserving the comparability of the core SAR trend model."
        ),
        "included_in_sar_pressure_index": "No",
        "primary_outputs": (
            "current_indicators_context.csv; current_indicators_flags.csv"
        ),
        "key_limitation": (
            "Current indicators are not directly comparable to the 2014-2024 SAR trend model and "
            "should not be blended into the SAR Pressure Index."
        ),
    },
]


def build_methodology_matrix() -> pd.DataFrame:
    """
    Build the project methodology matrix.

    The matrix documents each source layer, what it measures, how it is used,
    whether it enters the SAR Pressure Index, and its key limitation.
    """

    matrix = pd.DataFrame(METHODOLOGY_ROWS)

    matrix.to_csv(METHODOLOGY_MATRIX_FILE, index=False)
    print(f"Methodology matrix saved to: {METHODOLOGY_MATRIX_FILE}")

    return matrix


def run_methodology_matrix_analysis() -> dict:
    """
    Run methodology matrix creation.
    """

    matrix = build_methodology_matrix()

    return {
        "methodology_matrix": matrix,
    }