from pathlib import Path

# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
TABLES_DIR = OUTPUTS_DIR / "tables"
REPORTS_DIR = OUTPUTS_DIR / "reports"

for path in [
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    OUTPUTS_DIR,
    CHARTS_DIR,
    TABLES_DIR,
    REPORTS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Study settings
# ------------------------------------------------------------

PROJECT_TITLE = "Tennessee Financial Crime Intelligence Dashboard"
STATE_NAME = "Tennessee"
STATE_ABBR = "TN"

START_YEAR = 2014
END_YEAR = 2024
YEARS = list(range(START_YEAR, END_YEAR + 1))


# ------------------------------------------------------------
# FinCEN SAR Stats workbook URLs
#
# Source page:
# https://www.fincen.gov/resources/reports/sar-stats/sar-filings-industry
# ------------------------------------------------------------

FINCEN_SAR_WORKBOOKS = {
    "casino_card_club": {
        "industry_name": "Casino/Card Club",
        "filename": "casino_card_club_sars.xlsx",
        "url": "https://www.fincen.gov/system/files/shared/Section%201%20-%20Casino%20and%20Card%20Club%20SARs.xlsx",
    },
    "depository_institution": {
        "industry_name": "Depository Institution",
        "filename": "depository_institution_sars.xlsx",
        "url": "https://www.fincen.gov/system/files/shared/Section%202%20-%20Depository%20Institution%20SARs.xlsx",
    },
    "insurance_company": {
        "industry_name": "Insurance Company",
        "filename": "insurance_company_sars.xlsx",
        "url": "https://www.fincen.gov/system/files/shared/Section%203%20-%20Insurance%20company%20SARs.xlsx",
    },
    "money_services_business": {
        "industry_name": "Money Services Business",
        "filename": "money_services_business_sars.xlsx",
        "url": "https://www.fincen.gov/system/files/shared/Section%204%20-%20Money%20Services%20Business%20SARs.xlsx",
    },
    "securities_futures": {
        "industry_name": "Securities/Futures",
        "filename": "securities_futures_sars.xlsx",
        "url": "https://www.fincen.gov/system/files/shared/Section%205%20-%20Securities%20and%20Futures%20SARs.xlsx",
    },
    "other": {
        "industry_name": "Other",
        "filename": "other_sars.xlsx",
        "url": "https://www.fincen.gov/system/files/shared/Section%206%20-%20Other%20SARs.xlsx",
    },
    "loan_or_finance_company": {
        "industry_name": "Loan or Finance Company",
        "filename": "loan_or_finance_company_sars.xlsx",
        "url": "https://www.fincen.gov/system/files/shared/Section%207%20-%20Loan%20or%20Finance%20company%20SARs.xlsx",
    },
    "housing_gse": {
        "industry_name": "Housing Government Sponsored Enterprise",
        "filename": "housing_gse_sars.xlsx",
        "url": "https://www.fincen.gov/system/files/shared/Section%208%20-%20Housing%20GSE%20SARs.xlsx",
    },
}


# ------------------------------------------------------------
# Output data files
# ------------------------------------------------------------

WORKBOOK_INVENTORY_FILE = PROCESSED_DATA_DIR / "fincen_workbook_inventory.csv"
RAW_EXTRACT_FILE = PROCESSED_DATA_DIR / "raw_extracted_sar_rows.csv"
TN_VS_US_TREND_FILE = PROCESSED_DATA_DIR / "tn_vs_us_sar_trends.csv"
INDUSTRY_TREND_FILE = PROCESSED_DATA_DIR / "industry_sar_trends.csv"


# ------------------------------------------------------------
# TBI CrimeInsight / TIBRS context files
# ------------------------------------------------------------

TBI_EXPORTS_DIR = RAW_DATA_DIR / "tbi_exports"
TBI_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

TBI_CONTEXT_FILE = RAW_DATA_DIR / "tbi_financial_crime_context.csv"
TBI_CONTEXT_DETAIL_FILE = TABLES_DIR / "tbi_financial_crime_context_detail.csv"
TBI_CONTEXT_SUMMARY_FILE = TABLES_DIR / "tbi_financial_crime_context_summary.csv"
TBI_CONTEXT_FLAGS_FILE = TABLES_DIR / "tbi_financial_crime_context_flags.csv"

TBI_STATEWIDE_2024_CONTEXT_FILE = RAW_DATA_DIR / "tbi_statewide_2024_financial_crime_context.csv"
TBI_STATEWIDE_2024_SUMMARY_FILE = TABLES_DIR / "tbi_statewide_2024_financial_crime_summary.csv"


# ------------------------------------------------------------
# TBI Criminal Investigation Division capability context files
# ------------------------------------------------------------

TBI_CID_CONTEXT_FILE = TABLES_DIR / "tbi_criminal_investigation_division_context.csv"
TBI_CID_FLAGS_FILE = TABLES_DIR / "tbi_criminal_investigation_division_flags.csv"


# ------------------------------------------------------------
# FBI Crime Data API / CDE context files
# ------------------------------------------------------------

FBI_API_BASE_URL = "https://api.usa.gov/crime/fbi/cde"
FBI_API_KEY = "DEMO_KEY"

FBI_CONTEXT_RAW_FILE = TABLES_DIR / "fbi_financial_crime_context_raw.csv"
FBI_CONTEXT_SUMMARY_FILE = TABLES_DIR / "fbi_financial_crime_context_summary.csv"
FBI_CONTEXT_FLAGS_FILE = TABLES_DIR / "fbi_financial_crime_context_flags.csv"

FBI_EXPORTS_DIR = RAW_DATA_DIR / "fbi_exports"
FBI_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Elder financial exploitation context files
# ------------------------------------------------------------

ELDER_CONTEXT_SUMMARY_FILE = TABLES_DIR / "elder_financial_exploitation_context.csv"
ELDER_CONTEXT_FLAGS_FILE = TABLES_DIR / "elder_financial_exploitation_flags.csv"
ELDER_CONTEXT_CHART = CHARTS_DIR / "elder_financial_exploitation_context.png"


# ------------------------------------------------------------
# Comptroller public-sector fraud / audit context files
# ------------------------------------------------------------

COMPTROLLER_CONTEXT_FILE = TABLES_DIR / "comptroller_public_sector_fraud_context.csv"
COMPTROLLER_FLAGS_FILE = TABLES_DIR / "comptroller_public_sector_fraud_flags.csv"
COMPTROLLER_CHART = CHARTS_DIR / "comptroller_public_sector_fraud_context.png"


# ------------------------------------------------------------
# Looking-forward / current indicators context files
# ------------------------------------------------------------

CURRENT_INDICATORS_CONTEXT_FILE = TABLES_DIR / "current_indicators_context.csv"
CURRENT_INDICATORS_FLAGS_FILE = TABLES_DIR / "current_indicators_flags.csv"
CURRENT_INDICATORS_CHART = CHARTS_DIR / "current_indicators_context.png"


# ------------------------------------------------------------
# Methodology matrix and intelligence scorecard files
# ------------------------------------------------------------

METHODOLOGY_MATRIX_FILE = TABLES_DIR / "methodology_matrix.csv"
FINANCIAL_CRIME_SCORECARD_FILE = TABLES_DIR / "financial_crime_intelligence_scorecard.csv"


# ------------------------------------------------------------
# OFAC sanctions geography context files
# ------------------------------------------------------------

OFAC_DOWNLOAD_DIR = RAW_DATA_DIR / "ofac"
OFAC_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

OFAC_SDN_PRIMARY_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
OFAC_SDN_ADDRESS_URL = "https://www.treasury.gov/ofac/downloads/add.csv"
OFAC_CONSOLIDATED_PRIMARY_URL = "https://www.treasury.gov/ofac/downloads/consolidated/cons_prim.csv"
OFAC_CONSOLIDATED_ADDRESS_URL = "https://www.treasury.gov/ofac/downloads/consolidated/cons_add.csv"

OFAC_TENNESSEE_MATCHES_FILE = TABLES_DIR / "ofac_tennessee_address_matches.csv"
OFAC_CONTEXT_SUMMARY_FILE = TABLES_DIR / "ofac_tennessee_context_summary.csv"
OFAC_CONTEXT_FLAGS_FILE = TABLES_DIR / "ofac_tennessee_context_flags.csv"
OFAC_CONTEXT_CHART = CHARTS_DIR / "ofac_tennessee_programs.png"


# ------------------------------------------------------------
# Output chart files
# ------------------------------------------------------------

TN_TREND_CHART = CHARTS_DIR / "tennessee_sar_trend.png"
TN_VS_US_INDEX_CHART = CHARTS_DIR / "tennessee_vs_us_sar_index.png"
TN_INDUSTRY_CHART = CHARTS_DIR / "tennessee_sar_by_industry.png"

TOP_CATEGORY_CHART = CHARTS_DIR / "top_suspicious_activity_categories.png"
HIGH_RISK_CATEGORY_CHART = CHARTS_DIR / "high_risk_suspicious_activity_categories.png"
SCENARIO_PROJECTION_CHART = CHARTS_DIR / "tennessee_sar_scenario_projection.png"
SENSITIVITY_CHART = CHARTS_DIR / "sar_pressure_sensitivity.png"

TBI_CONTEXT_CHART = CHARTS_DIR / "tbi_financial_crime_context.png"
FBI_CONTEXT_CHART = CHARTS_DIR / "fbi_financial_crime_context.png"


# ------------------------------------------------------------
# Output report files
# ------------------------------------------------------------

REPORT_FILE = REPORTS_DIR / "tennessee_financial_crime_intelligence_report.pdf"