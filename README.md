# Tennessee Financial Crime Intelligence Dashboard

## Project Overview

This project analyzes public FinCEN Suspicious Activity Report (SAR) Stats data to study Tennessee SAR filing trends, Tennessee-vs-U.S. SAR growth dynamics, filing-industry concentration, suspicious activity category themes, and broader financial-crime context.

The project has expanded into a multi-source financial crime intelligence dashboard. The **core analytical model** remains based on public FinCEN SAR Stats data, while additional public sources provide **supporting context** around law-enforcement offense data, elder financial exploitation, OFAC sanctions geography, public-sector fraud reporting, current indicators, methodology documentation, and intelligence scoring.

The project is designed as a Python-based financial intelligence, AML analytics, fraud-risk, sanctions-screening context, public-sector fraud, and open-source intelligence research case study.

## Project Title

**Tennessee Financial Crime Intelligence Dashboard**

**Subtitle:** SAR Trends, Law-Enforcement Context, Sanctions Geography, Public-Sector Fraud Indicators, and Current Monitoring Signals

## Key Features

- End-to-end Python pipeline for public FinCEN SAR Stats analysis
- Tennessee vs U.S. SAR trend comparison from 2014 through 2024
- Tennessee filing-industry concentration analysis
- Suspicious activity category intelligence
- SAR Pressure Index with component-level scoring
- Scenario analysis for projected Tennessee SAR filings
- Sensitivity analysis for alternative SAR Pressure Index weighting assumptions
- Integrated change detection across SAR and context layers
- TBI/TIBRS and FBI/NIBRS law-enforcement context
- Elder financial exploitation context
- Tennessee Comptroller public-sector fraud and audit context
- OFAC sanctions geography screening context
- 2025-2026 current indicators / looking-forward section
- Methodology Matrix documenting source-layer boundaries
- Financial Crime Intelligence Scorecard
- Final PDF intelligence report with source appendix
- Streamlit dashboard for interactive exploration and downloads

## Research Questions

1. How have Tennessee SAR filings changed from 2014 through 2024?
2. How does Tennessee SAR growth compare with broader U.S. SAR growth?
3. Which filing industries appear to drive Tennessee SAR activity?
4. Which suspicious activity categories provide useful financial-crime context?
5. What does the SAR Pressure Index suggest about Tennessee reporting pressure?
6. How stable is the SAR Pressure Index under alternative weighting assumptions?
7. How do scenario assumptions affect projected Tennessee SAR filings?
8. How do TBI/TIBRS and FBI/NIBRS data support broader financial-crime context?
9. How do elder exploitation, public-sector fraud, and OFAC sanctions geography expand the intelligence picture?
10. Which 2025-2026 current indicators should be monitored separately from the core SAR model?
11. How can methodology boundaries be documented so that SAR data, law-enforcement data, sanctions geography, and public-sector fraud context are not blended incorrectly?

## Methodology Summary

The project separates the **core SAR model** from **supporting context layers**.

### Core SAR Model

The main model uses public FinCEN SAR Stats data from 2014 through 2024. It includes:

- Tennessee SAR filing trends
- U.S. SAR filing trends
- Tennessee-vs-U.S. indexed growth comparison
- Tennessee industry-level SAR filing concentration
- Suspicious activity category context
- SAR Pressure Index
- Scenario analysis
- Sensitivity analysis
- Change detection
- Financial Crime Intelligence Scorecard
- Methodology Matrix documentation

### Supporting Context Layers

The following layers are included for interpretation only and are **not** included in the SAR Pressure Index:

- TBI/TIBRS financial-crime-adjacent offense context
- FBI Crime Data Explorer / NIBRS context
- Elder financial exploitation context
- TBI Criminal Investigation Division capability context
- Tennessee Comptroller public-sector fraud and audit context
- OFAC sanctions geography context
- 2025-2026 current indicators / looking-forward context

This separation is important because SAR filings, law-enforcement offense counts, sanctions-list addresses, public-sector fraud allegations, and investigative-capability indicators measure different things.

## Data Sources

### FinCEN SAR Stats

Primary SAR filing trend source:

https://www.fincen.gov/resources/reports/sar-stats/sar-filings-industry

FinCEN SAR Stats data is public, aggregated, and organized by filing industry, state/territory rankings, and suspicious activity categories. The project uses this data to build the core SAR trend model.

### TBI / TIBRS Context

The project includes manually encoded 2024 statewide financial-crime-adjacent offense context from Tennessee's Crime in Tennessee / TIBRS statewide reporting.

Useful source references:

- https://www.tn.gov/tbi/divisions/cjis-division/tncrimeonline.html
- https://www.tn.gov/tbi/divisions/cjis-division/recent-publications.html

This layer is used as law-enforcement context only. It is not SAR filing data.

### FBI Crime Data Explorer / NIBRS Context

The project supports local FBI Crime Data Explorer / NIBRS flat-file exports and uses the FBI API as a fallback when local files are not available.

Useful source references:

- https://cde.ucr.cjis.gov/
- https://github.com/fbi-cde/crime-data-api

This layer provides broader law-enforcement offense context and is not included in the SAR Pressure Index.

### Elder Financial Exploitation Context

The project includes elder financial exploitation as a policy and victim-risk context layer. It connects SAR category themes with fraud, identity theft, exploitation, and law-enforcement context.

This layer is interpretive context only and should not be treated as a Tennessee-specific elder SAR count unless source data explicitly supports that interpretation.

### Tennessee Comptroller Context

The project includes Tennessee Comptroller public-sector fraud, waste, abuse, hotline, allegation, and audit context for FY2025.

Useful source reference:

https://comptroller.tn.gov/office-functions/investigations/fraud-waste-and-abuse.html

This is public-sector oversight context only and is not equivalent to SAR filings, confirmed crimes, charges, or convictions.

### OFAC Sanctions Geography Context

The project screens public OFAC SDN and Consolidated Non-SDN address files for Tennessee-related geography indicators.

Useful source references:

- https://ofac.treasury.gov/sanctions-list-service
- https://sanctionslist.ofac.treas.gov/Home/SdnList
- https://sanctionslist.ofac.treas.gov/Home/ConsolidatedList

OFAC address matches are sanctions-screening geography context only. They do not indicate Tennessee SAR activity, local criminal activity, or enforcement action.

### Current Indicators / Looking Forward

The project includes a separate 2025-2026 current-indicators section. These indicators are used to keep the report current, but they are not direct extensions of the 2014-2024 SAR trend model.

Comparable 2025 or 2026 FinCEN state/industry SAR Stats data would be required before extending the core SAR model beyond 2024.

## Project Structure

```text
tennessee_financial_crime_intelligence_dashboard/
|
├── data/
│   ├── raw/
│   │   ├── fbi_exports/
│   │   ├── ofac/
│   │   └── tbi_exports/
│   └── processed/
|
├── outputs/
│   ├── charts/
│   ├── tables/
│   └── reports/
|
├── src/
│   ├── __init__.py
│   ├── category_analysis.py
│   ├── change_detection.py
│   ├── comptroller_context.py
│   ├── config.py
│   ├── current_indicators.py
│   ├── elder_financial_exploitation.py
│   ├── fbi_crime_data.py
│   ├── intelligence_scorecard.py
│   ├── methodology_matrix.py
│   ├── ofac_context.py
│   ├── report_generator.py
│   ├── risk_scoring.py
│   ├── sar_loader.py
│   ├── sar_processing.py
│   ├── scenario_analysis.py
│   ├── sensitivity_analysis.py
│   ├── tbi_context.py
│   ├── trend_analysis.py
│   └── visualization.py
|
├── app.py
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Main Outputs

### Tables

The pipeline creates CSV outputs under:

```text
outputs/tables/
```

Key outputs include:

- `trend_summary.csv`
- `industry_summary.csv`
- `sar_pressure_index.csv`
- `sar_pressure_components.csv`
- `sar_scenario_assumptions.csv`
- `sar_scenario_projections.csv`
- `sar_scenario_summary.csv`
- `sar_pressure_sensitivity.csv`
- `change_detection_flags.csv`
- `change_detection_summary.csv`
- `suspicious_activity_category_detail.csv`
- `suspicious_activity_category_summary.csv`
- `top_suspicious_activity_categories_latest_year.csv`
- `high_risk_suspicious_activity_categories.csv`
- `tbi_financial_crime_context_detail.csv`
- `tbi_financial_crime_context_summary.csv`
- `tbi_financial_crime_context_flags.csv`
- `fbi_financial_crime_context_raw.csv`
- `fbi_financial_crime_context_summary.csv`
- `fbi_financial_crime_context_flags.csv`
- `elder_financial_exploitation_context.csv`
- `elder_financial_exploitation_flags.csv`
- `comptroller_public_sector_fraud_context.csv`
- `comptroller_public_sector_fraud_flags.csv`
- `ofac_tennessee_address_matches.csv`
- `ofac_tennessee_context_summary.csv`
- `ofac_tennessee_context_flags.csv`
- `current_indicators_context.csv`
- `current_indicators_flags.csv`
- `methodology_matrix.csv`
- `financial_crime_intelligence_scorecard.csv`

### Charts

Charts are saved under:

```text
outputs/charts/
```

Key charts include:

- Tennessee SAR filings trend
- Tennessee vs U.S. SAR growth index
- Tennessee SAR filings by industry
- Top suspicious activity categories
- Elevated and high-risk suspicious activity categories
- SAR scenario projections
- SAR Pressure Index sensitivity
- TBI financial-crime context
- FBI/NIBRS financial-crime context
- Elder financial exploitation context
- Comptroller public-sector fraud context
- OFAC sanctions program context, when accepted Tennessee-related OFAC program rows are available

### PDF Report

The final PDF report is saved under:

```text
outputs/reports/
```

Recommended report filename:

```text
tennessee_financial_crime_intelligence_report.pdf
```

The report includes:

- Executive summary
- Key findings
- Financial Crime Intelligence Scorecard
- Methodology Matrix
- Tennessee vs U.S. SAR trend analysis
- Tennessee SAR industry concentration
- Suspicious activity category intelligence
- Tennessee SAR Pressure Index
- Change detection
- Scenario analysis
- Sensitivity analysis
- TBI and FBI/NIBRS law-enforcement context
- Elder financial exploitation context
- Comptroller public-sector fraud and audit context
- Looking-forward current indicators
- OFAC sanctions geography context
- Limitations and conclusion
- Source Appendix

### Streamlit Dashboard

The Streamlit app provides an interactive companion dashboard for the generated outputs.

Dashboard sections include:

- Overview
- Financial Crime Intelligence Scorecard
- Methodology Matrix
- SAR Trends
- Industry Concentration
- Category Intelligence
- SAR Pressure Index
- Change Detection
- Scenario & Sensitivity Analysis
- Law-Enforcement Context
- Elder Exploitation Context
- Comptroller Context
- OFAC Context
- Current Indicators
- Source Appendix
- Downloads

The dashboard reads from:

```text
outputs/tables/
outputs/charts/
outputs/reports/
```

It does not recalculate the model. Run `python main.py` first to generate the required output files.

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Requirements

```text
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
openpyxl>=3.1.0
requests>=2.31.0
reportlab>=4.0.0
streamlit>=1.35.0
```

## How to Run the Full Pipeline

From the project root:

```powershell
python main.py
```

The pipeline will:

1. Download or validate FinCEN SAR Stats workbooks.
2. Inspect workbook sheets.
3. Process SAR data.
4. Build trend and industry summaries.
5. Run suspicious activity category analysis.
6. Build the SAR Pressure Index.
7. Run scenario analysis.
8. Run sensitivity analysis.
9. Run TBI/TIBRS context analysis.
10. Run FBI/NIBRS context analysis.
11. Run elder financial exploitation context analysis.
12. Run Comptroller public-sector fraud context analysis.
13. Run OFAC sanctions geography screening.
14. Run current indicators / looking-forward context analysis.
15. Build the methodology matrix.
16. Build the financial crime intelligence scorecard.
17. Run integrated change detection.
18. Save charts.
19. Generate the PDF report.

## How to Run the Streamlit Dashboard

After running the main pipeline, launch the interactive dashboard:

```powershell
streamlit run app.py
```

The dashboard opens locally in your browser and provides interactive access to the generated tables, charts, source references, and downloadable PDF report.

## Suggested GitHub Workflow

Before committing, make sure `.gitignore` excludes local environments, raw data, processed data, generated charts, generated tables, and generated reports.

Suggested first commit:

```powershell
git init
git add .
git status
git commit -m "Initial commit for Tennessee financial crime intelligence dashboard"
```

Suggested repository name:

```text
tennessee-financial-crime-intelligence-dashboard
```

## Methodology Notes

SAR filing counts measure reporting activity and monitoring behavior. They are not direct measures of confirmed financial crime.

Suspicious activity category exhibits are treated as SAR-theme context. They should not be interpreted as Tennessee-specific category counts unless the source data explicitly supports that breakdown.

TBI and FBI/NIBRS data are law-enforcement reported offense context. They are not SAR data.

OFAC address matches are sanctions-screening geography context only and do not imply local criminal activity or enforcement action.

Comptroller public-sector fraud and audit indicators are oversight and allegation-reporting context. They are not equivalent to SAR filings or confirmed crimes.

Current indicators are forward-looking context only and should not be blended into the 2014-2024 SAR Pressure Index.

The methodology matrix documents each layer, what it measures, whether it is included in the SAR Pressure Index, and the main limitation.

The intelligence scorecard summarizes the project's major analytical signals, but it does not alter the SAR Pressure Index methodology.

## Limitations

- The project uses public aggregated data only.
- The project does not use raw SAR narratives or transaction-level records.
- The project does not identify individual institutions, subjects, transactions, or investigations.
- The SAR Pressure Index is an analytical signal, not a prediction of criminal activity.
- Supporting context layers are intentionally separated from the core SAR score.
- OFAC geography matching is conservative but still requires careful interpretation.
- Current indicators are used for looking-forward context only.
- Comparable FinCEN state/industry SAR Stats releases would be required to extend the SAR model beyond 2024.

## Suggested Citation

Tennessee Financial Crime Intelligence Dashboard, prepared by Jason Keen, using public FinCEN SAR Stats, TBI/TIBRS, FBI/NIBRS, Tennessee Comptroller, OFAC, and related public-source context materials.

## Author

Prepared by Jason Keen  
[LinkedIn](https://www.linkedin.com/in/jason-keen-1887b4218)
