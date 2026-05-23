import pandas as pd

from src.config import (
    COMPTROLLER_CONTEXT_FILE,
    COMPTROLLER_FLAGS_FILE,
)


COMPTROLLER_CONTEXT_ROWS = [
    {
        "context_theme": "Public-Sector Fraud Reporting",
        "metric": "Fraud, Waste & Abuse Hotline notifications",
        "value": 1074,
        "period": "FY2025",
        "source": "Tennessee Comptroller Department of Audit 2025 Annual Report",
        "data_basis": "Annual report disclosure on Fraud, Waste & Abuse Hotline activity.",
        "interpretation": (
            "The Comptroller reported 1,074 total Fraud, Waste & Abuse Hotline "
            "notifications during FY2025, indicating an active public-sector fraud "
            "reporting channel in Tennessee."
        ),
        "report_use": "Use as public-sector fraud and internal-control context, not as SAR data.",
        "methodology_note": (
            "This is a public-sector oversight and fraud-reporting context layer. "
            "It is not included in the SAR Pressure Index."
        ),
    },
    {
        "context_theme": "Public-Sector Fraud Reporting",
        "metric": "Substantive allegations",
        "value": 1000,
        "period": "FY2025",
        "source": "Tennessee Comptroller Department of Audit 2025 Annual Report",
        "data_basis": "Annual report disclosure on substantive allegations received.",
        "interpretation": (
            "The Comptroller reported 1,000 substantive allegations during FY2025, "
            "supporting the inclusion of public-sector fraud as a Tennessee financial "
            "intelligence context theme."
        ),
        "report_use": "Use to support a short public-sector fraud / audit context section.",
        "methodology_note": (
            "These allegations are not equivalent to confirmed fraud, SAR filings, "
            "criminal charges, or convictions."
        ),
    },
    {
        "context_theme": "Hotline Intake Channel",
        "metric": "Telephone hotline submissions",
        "value": 443,
        "period": "FY2025",
        "source": "Tennessee Comptroller Department of Audit 2025 Annual Report",
        "data_basis": "Annual report disclosure on hotline telephone submissions.",
        "interpretation": (
            "Telephone submissions represented one channel through which suspected "
            "fraud, waste, and abuse allegations reached the Comptroller."
        ),
        "report_use": "Use as supporting evidence for reporting-channel diversity.",
        "methodology_note": (
            "This is reporting-channel context only and is not a measure of SAR activity."
        ),
    },
    {
        "context_theme": "Hotline Intake Channel",
        "metric": "Online submissions",
        "value": 631,
        "period": "FY2025",
        "source": "Tennessee Comptroller Department of Audit 2025 Annual Report",
        "data_basis": "Annual report disclosure on online Fraud, Waste & Abuse submissions.",
        "interpretation": (
            "Online submissions were the larger hotline intake channel in FY2025, "
            "showing the importance of digital reporting pathways for public-sector "
            "fraud, waste, and abuse allegations."
        ),
        "report_use": "Use as public-sector fraud reporting-channel context.",
        "methodology_note": (
            "This context should remain separate from SAR trend calculations."
        ),
    },
    {
        "context_theme": "Investigative Referral Pathways",
        "metric": "Qualitative",
        "value": None,
        "period": "FY2025",
        "source": "Tennessee Comptroller Department of Audit 2025 Annual Report",
        "data_basis": (
            "Annual report discussion of investigation sources, including hotline reports, "
            "fraud reporting forms, audit findings, citizens, officials, CPAs, state agencies, "
            "district attorneys, the Tennessee Attorney General, FBI, and other law-enforcement agencies."
        ),
        "interpretation": (
            "The Comptroller investigation pipeline can receive allegations and referrals "
            "from multiple public, audit, prosecutorial, and law-enforcement channels."
        ),
        "report_use": (
            "Use as narrative context linking public-sector fraud oversight to broader "
            "financial intelligence and investigative ecosystems."
        ),
        "methodology_note": (
            "This is qualitative institutional context and is not included in the SAR Pressure Index."
        ),
    },
    {
        "context_theme": "Public Funds Oversight",
        "metric": "Qualitative",
        "value": None,
        "period": "FY2025",
        "source": "Tennessee Comptroller Department of Audit 2025 Annual Report",
        "data_basis": (
            "Annual report description of the Division of Investigations investigating "
            "allegations of fraud, waste, and abuse of public funds."
        ),
        "interpretation": (
            "The Comptroller layer adds public-funds oversight context to the project, "
            "which complements SAR, fraud, TBI, FBI, and elder exploitation themes."
        ),
        "report_use": (
            "Use in the report as a short public-sector fraud and internal-control context section."
        ),
        "methodology_note": (
            "This layer supports interpretation only and should not be treated as criminal-offense "
            "or SAR filing data."
        ),
    },
]


def format_number(value) -> str:
    """
    Format numeric values safely.
    """

    numeric_value = pd.to_numeric(value, errors="coerce")

    if pd.isna(numeric_value):
        return "N/A"

    return f"{numeric_value:,.0f}"


def build_comptroller_context() -> pd.DataFrame:
    """
    Build Tennessee Comptroller public-sector fraud / audit context table.

    This layer is used as supporting context only. It is not included in the
    SAR Pressure Index.
    """

    context = pd.DataFrame(COMPTROLLER_CONTEXT_ROWS)

    context.to_csv(COMPTROLLER_CONTEXT_FILE, index=False)
    print(f"Comptroller public-sector fraud context saved to: {COMPTROLLER_CONTEXT_FILE}")

    return context


def build_comptroller_flags(context: pd.DataFrame) -> pd.DataFrame:
    """
    Build Comptroller context flags for the intelligence report.
    """

    flags = []

    if context.empty:
        flags.append(
            {
                "flag_type": "Comptroller Context Missing",
                "severity": "Informational",
                "description": "No Comptroller public-sector fraud context was created.",
                "methodology_scope": "Supporting public-sector fraud context",
            }
        )
    else:
        flags.append(
            {
                "flag_type": "Comptroller Context Available",
                "severity": "Informational",
                "description": (
                    "Tennessee Comptroller public-sector fraud, waste, abuse, and audit context "
                    "is included as a supporting public-sector oversight layer."
                ),
                "methodology_scope": "Supporting public-sector fraud context",
            }
        )

        hotline_rows = context[
            context["metric"]
            .astype(str)
            .str.lower()
            .str.contains("hotline notifications", na=False)
        ]

        if not hotline_rows.empty:
            row = hotline_rows.iloc[0]
            flags.append(
                {
                    "flag_type": "Public-Sector Fraud Reporting",
                    "severity": "Informational",
                    "description": (
                        f"The Comptroller context includes {format_number(row.get('value'))} "
                        f"Fraud, Waste & Abuse Hotline notifications in {row.get('period', 'FY2025')}, "
                        "supporting public-sector fraud reporting context."
                    ),
                    "methodology_scope": "Supporting public-sector fraud context",
                }
            )

        allegation_rows = context[
            context["metric"]
            .astype(str)
            .str.lower()
            .str.contains("substantive allegations", na=False)
        ]

        if not allegation_rows.empty:
            row = allegation_rows.iloc[0]
            flags.append(
                {
                    "flag_type": "Substantive Allegation Context",
                    "severity": "Informational",
                    "description": (
                        f"The Comptroller context includes {format_number(row.get('value'))} "
                        f"substantive allegations in {row.get('period', 'FY2025')}. "
                        "These allegations are public-sector oversight context and are not equivalent "
                        "to SAR filings or confirmed crimes."
                    ),
                    "methodology_scope": "Supporting public-sector fraud context",
                }
            )

        flags.append(
            {
                "flag_type": "Index Treatment",
                "severity": "Informational",
                "description": (
                    "Comptroller public-sector fraud and audit context is not added to the "
                    "SAR Pressure Index because it measures oversight and allegation-reporting activity, "
                    "not SAR filing pressure."
                ),
                "methodology_scope": "Index methodology limitation",
            }
        )

    flags_df = pd.DataFrame(flags)
    flags_df.to_csv(COMPTROLLER_FLAGS_FILE, index=False)

    print(f"Comptroller public-sector fraud flags saved to: {COMPTROLLER_FLAGS_FILE}")

    return flags_df


def run_comptroller_context_analysis() -> dict:
    """
    Run the Comptroller public-sector fraud / audit context layer.
    """

    context = build_comptroller_context()
    flags = build_comptroller_flags(context)

    return {
        "comptroller_context": context,
        "comptroller_flags": flags,
    }