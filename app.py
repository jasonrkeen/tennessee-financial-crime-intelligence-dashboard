from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
CHARTS_DIR = OUTPUTS_DIR / "charts"
REPORTS_DIR = OUTPUTS_DIR / "reports"

REPORT_FILE = REPORTS_DIR / "tennessee_financial_crime_intelligence_report.pdf"


# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------

st.set_page_config(
    page_title="Tennessee Financial Crime Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ------------------------------------------------------------
# Custom styling
# ------------------------------------------------------------

st.markdown(
    """
    <style>
        /* Main page layout */
        .stApp {
            background: #0B1220;
            color: #F9FAFB;
        }

        .block-container {
            padding-top: 2.4rem;
            padding-bottom: 2.5rem;
            max-width: 1320px;
        }

        /* Main title */
        .main-title {
            font-size: 2.25rem;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 0.35rem;
            color: #F9FAFB;
        }

        .main-subtitle {
            font-size: 1rem;
            color: #CBD5E1;
            margin-bottom: 1.1rem;
            max-width: 1100px;
        }

        /* Hero section */
        .hero-card {
            background: linear-gradient(135deg, #172033 0%, #1E293B 55%, #334155 100%);
            color: #FFFFFF;
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 1.35rem 1.45rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
        }

        .hero-card h2 {
            color: #FFFFFF;
            margin-bottom: 0.35rem;
            font-size: 1.75rem;
            font-weight: 800;
        }

        .hero-card p {
            color: #E5E7EB;
            margin-bottom: 0.25rem;
            font-size: 0.98rem;
        }

        /* Cards */
        .section-card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1.05rem 1.1rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.20);
        }

        .section-card p,
        .section-card div,
        .section-card span {
            color: #E5E7EB;
        }

        .mini-label {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #93C5FD !important;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }

        .muted-note {
            color: #CBD5E1 !important;
            font-size: 0.90rem;
            line-height: 1.5;
        }

        /* Pills */
        .status-pill {
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: #DBEAFE;
            color: #1E3A8A !important;
            font-size: 0.78rem;
            font-weight: 800;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }

        .warning-pill {
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: #FEF3C7;
            color: #92400E !important;
            font-size: 0.78rem;
            font-weight: 800;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }

        .success-pill {
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: #D1FAE5;
            color: #065F46 !important;
            font-size: 0.78rem;
            font-weight: 800;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }

        /* Custom KPI cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            margin: 1.1rem 0 1.4rem 0;
        }

        .kpi-card {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1rem 1.05rem;
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.20);
            min-height: 118px;
        }

        .kpi-label {
            color: #CBD5E1 !important;
            font-size: 0.86rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }

        .kpi-value {
            color: #F9FAFB !important;
            font-size: 1.65rem;
            line-height: 1.15;
            font-weight: 850;
            word-break: normal;
            overflow-wrap: anywhere;
        }

        .kpi-note {
            color: #94A3B8 !important;
            font-size: 0.78rem;
            margin-top: 0.45rem;
            line-height: 1.35;
        }

        @media (max-width: 1100px) {
            .kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 700px) {
            .kpi-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Streamlit metric fallback styling */
        div[data-testid="stMetric"] {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1rem 1rem;
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.20);
        }

        div[data-testid="stMetricLabel"] {
            color: #CBD5E1 !important;
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: #F9FAFB !important;
            font-weight: 800;
        }

        div[data-testid="stMetricDelta"] {
            color: #93C5FD !important;
        }

        /* Sidebar */
        div[data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid #334155;
        }

        div[data-testid="stSidebar"] * {
            color: #E5E7EB;
        }

        div[data-testid="stSidebar"] .stSelectbox label,
        div[data-testid="stSidebar"] .stRadio label {
            color: #F9FAFB !important;
            font-weight: 700;
        }

        /* Buttons */
        .stDownloadButton button {
            background: #1D4ED8;
            color: #FFFFFF;
            border: 1px solid #2563EB;
            border-radius: 10px;
            font-weight: 700;
        }

        .stDownloadButton button:hover {
            background: #2563EB;
            color: #FFFFFF;
            border: 1px solid #60A5FA;
        }

        /* Dataframes and tabs */
        div[data-testid="stDataFrame"] {
            border: 1px solid #334155;
            border-radius: 12px;
            overflow: hidden;
        }

        button[data-baseweb="tab"] {
            color: #CBD5E1;
            font-weight: 700;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #FFFFFF;
            border-bottom-color: #60A5FA;
        }

        /* Headings and text */
        h1, h2, h3, h4 {
            color: #F9FAFB !important;
        }

        p, li, label, span {
            color: #E5E7EB;
        }

        hr {
            margin-top: 1.2rem;
            margin-bottom: 1.2rem;
            border-color: #334155;
        }

        /* Info boxes */
        div[data-testid="stAlert"] {
            background: #172033;
            color: #E5E7EB;
            border: 1px solid #334155;
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

@st.cache_data
def read_csv_safe(path: Path) -> pd.DataFrame:
    """
    Safely read a CSV file.
    """

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def format_number(value) -> str:
    """
    Format numeric values.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.0f}"
    except Exception:
        return str(value)


def format_float(value, decimals: int = 2) -> str:
    """
    Format float values.
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


def section_intro(title: str, subtitle: str | None = None):
    """
    Render consistent section headers.
    """

    st.markdown(f"## {title}")

    if subtitle:
        st.markdown(f"<p class='muted-note'>{subtitle}</p>", unsafe_allow_html=True)


def render_hero():
    """
    Render landing-page hero.
    """

    st.markdown(
        """
        <div class="hero-card">
            <h2>Tennessee Financial Crime Intelligence Dashboard</h2>
            <p>
                A public-source AML, fraud-risk, SAR trend, sanctions-geography, and financial crime
                intelligence dashboard built from generated project outputs.
            </p>
            <div style="margin-top:0.75rem;">
                <span class="status-pill">SAR Pressure Index</span>
                <span class="status-pill">Methodology Matrix</span>
                <span class="status-pill">Financial Crime Scorecard</span>
                <span class="status-pill">Scenario & Sensitivity</span>
                <span class="status-pill">Source Appendix</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_how_to_read(text: str):
    """
    Render a polished interpretation note.
    """

    st.markdown(
        f"""
        <div class="section-card">
            <div class="mini-label">How to read this section</div>
            <div class="muted-note">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_methodology_boundary_card():
    """
    Render model boundary callout.
    """

    st.markdown(
        """
        <div class="section-card">
            <div class="mini-label">Model Boundary</div>
            <p class="muted-note">
                The core SAR model is based on public FinCEN SAR Stats data. TBI/TIBRS, FBI/NIBRS,
                elder exploitation, Tennessee Comptroller, OFAC, and current-indicator layers are
                supporting context only and are not included in the SAR Pressure Index.
            </p>
            <span class="success-pill">Included: FinCEN SAR Stats</span>
            <span class="warning-pill">Context only: TBI/FBI</span>
            <span class="warning-pill">Context only: Comptroller</span>
            <span class="warning-pill">Context only: OFAC</span>
            <span class="warning-pill">Context only: Current indicators</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_cards(cards: list[dict]):
    """
    Render custom HTML KPI cards without Markdown indentation issues.
    """

    card_html = ['<div class="kpi-grid">']

    for card in cards:
        label = escape(str(card.get("label", "")))
        value = escape(str(card.get("value", "N/A")))
        note = escape(str(card.get("note", "")))

        card_html.append(
            (
                '<div class="kpi-card">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div>'
                f'<div class="kpi-note">{note}</div>'
                '</div>'
            )
        )

    card_html.append("</div>")

    st.markdown("".join(card_html), unsafe_allow_html=True)


def show_dataframe(
    df: pd.DataFrame,
    title: str | None = None,
    height: int = 360,
):
    """
    Display dataframe with a consistent empty-state message.
    """

    if title:
        st.subheader(title)

    if df.empty:
        st.info("No data available. Run `python main.py` to generate the required output tables.")
        return

    st.dataframe(df, use_container_width=True, height=height)


def show_chart(path: Path, caption: str | None = None):
    """
    Display a saved chart if it exists.
    """

    if path.exists():
        st.image(str(path), use_container_width=True, caption=caption)
    else:
        st.info(f"Chart not found: `{path.name}`")


def chart_card(path: Path, title: str, caption: str | None = None):
    """
    Display a chart inside a clean card.
    """

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(title)
    show_chart(path, caption)
    st.markdown("</div>", unsafe_allow_html=True)


def table_card(df: pd.DataFrame, title: str, height: int = 360):
    """
    Display a table inside a clean card.
    """

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    show_dataframe(df, title, height)
    st.markdown("</div>", unsafe_allow_html=True)


def download_button_for_csv(df: pd.DataFrame, filename: str, label: str):
    """
    Add a CSV download button.
    """

    if df.empty:
        return

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def source_dataframe() -> pd.DataFrame:
    """
    Build source appendix dataframe for the app.
    """

    source_rows = [
        {
            "Source / Layer": "FinCEN SAR Stats",
            "Source Reference / URL": "https://www.fincen.gov/resources/reports/sar-stats/sar-filings-industry",
            "Primary Use": "Core SAR filing trend data for Tennessee-vs-U.S. trends, industry concentration, category context, SAR Pressure Index, scenario analysis, sensitivity analysis, and change detection.",
            "Limitation": "SAR filings measure reporting activity and monitoring behavior, not confirmed financial crime.",
        },
        {
            "Source / Layer": "FinCEN SAR Stats filing-industry workbooks",
            "Source Reference / URL": "https://www.fincen.gov/reports/sar-stats",
            "Primary Use": "Source workbooks by filing industry.",
            "Limitation": "Exhibit interpretation depends on workbook structure and available state-level detail.",
        },
        {
            "Source / Layer": "TBI / TIBRS CrimeInsight",
            "Source Reference / URL": "https://www.tn.gov/tbi/divisions/cjis-division/tncrimeonline.html",
            "Primary Use": "Tennessee law-enforcement offense context.",
            "Limitation": "Reported offenses are not SAR filings.",
        },
        {
            "Source / Layer": "TBI Crime in Tennessee publications",
            "Source Reference / URL": "https://www.tn.gov/tbi/divisions/cjis-division/recent-publications.html",
            "Primary Use": "Statewide crime-publication context and TIBRS background.",
            "Limitation": "Supporting context only.",
        },
        {
            "Source / Layer": "FBI Crime Data Explorer / NIBRS",
            "Source Reference / URL": "https://cde.ucr.cjis.gov/",
            "Primary Use": "Federal NIBRS context for Tennessee offense categories.",
            "Limitation": "Reported offense context, not confirmed convictions or SAR activity.",
        },
        {
            "Source / Layer": "FBI Crime Data API",
            "Source Reference / URL": "https://github.com/fbi-cde/crime-data-api",
            "Primary Use": "Fallback or supporting API reference for CDE/NIBRS data.",
            "Limitation": "Depends on available FBI-published data.",
        },
        {
            "Source / Layer": "Tennessee Comptroller fraud, waste, and abuse materials",
            "Source Reference / URL": "https://comptroller.tn.gov/office-functions/investigations/fraud-waste-and-abuse.html",
            "Primary Use": "Public-sector fraud, waste, abuse, hotline, allegation, audit, and internal-control context.",
            "Limitation": "Allegation/reporting and oversight context only.",
        },
        {
            "Source / Layer": "OFAC Sanctions List Service",
            "Source Reference / URL": "https://ofac.treasury.gov/sanctions-list-service",
            "Primary Use": "Sanctions-list address screening context.",
            "Limitation": "OFAC address matches do not indicate local criminal activity or SAR activity.",
        },
        {
            "Source / Layer": "OFAC SDN List",
            "Source Reference / URL": "https://sanctionslist.ofac.treas.gov/Home/SdnList",
            "Primary Use": "SDN list address screening.",
            "Limitation": "Sanctions geography context only.",
        },
        {
            "Source / Layer": "OFAC Consolidated Non-SDN List",
            "Source Reference / URL": "https://sanctionslist.ofac.treas.gov/Home/ConsolidatedList",
            "Primary Use": "Consolidated non-SDN list address screening.",
            "Limitation": "Ambiguous geography is not accepted without clear U.S./Tennessee support.",
        },
    ]

    return pd.DataFrame(source_rows)


def load_all_tables() -> dict:
    """
    Load all dashboard tables.
    """

    return {
        "trend_summary": read_csv_safe(TABLES_DIR / "trend_summary.csv"),
        "industry_summary": read_csv_safe(TABLES_DIR / "industry_summary.csv"),
        "sar_pressure_index": read_csv_safe(TABLES_DIR / "sar_pressure_index.csv"),
        "sar_pressure_components": read_csv_safe(TABLES_DIR / "sar_pressure_components.csv"),
        "intelligence_scorecard": read_csv_safe(TABLES_DIR / "financial_crime_intelligence_scorecard.csv"),
        "methodology_matrix": read_csv_safe(TABLES_DIR / "methodology_matrix.csv"),
        "change_detection_flags": read_csv_safe(TABLES_DIR / "change_detection_flags.csv"),
        "change_detection_summary": read_csv_safe(TABLES_DIR / "change_detection_summary.csv"),
        "scenario_summary": read_csv_safe(TABLES_DIR / "sar_scenario_summary.csv"),
        "scenario_projections": read_csv_safe(TABLES_DIR / "sar_scenario_projections.csv"),
        "sensitivity": read_csv_safe(TABLES_DIR / "sar_pressure_sensitivity.csv"),
        "category_summary": read_csv_safe(TABLES_DIR / "suspicious_activity_category_summary.csv"),
        "top_categories": read_csv_safe(TABLES_DIR / "top_suspicious_activity_categories_latest_year.csv"),
        "high_risk_categories": read_csv_safe(TABLES_DIR / "high_risk_suspicious_activity_categories.csv"),
        "tbi_summary": read_csv_safe(TABLES_DIR / "tbi_financial_crime_context_summary.csv"),
        "tbi_flags": read_csv_safe(TABLES_DIR / "tbi_financial_crime_context_flags.csv"),
        "fbi_summary": read_csv_safe(TABLES_DIR / "fbi_financial_crime_context_summary.csv"),
        "fbi_flags": read_csv_safe(TABLES_DIR / "fbi_financial_crime_context_flags.csv"),
        "elder_context": read_csv_safe(TABLES_DIR / "elder_financial_exploitation_context.csv"),
        "elder_flags": read_csv_safe(TABLES_DIR / "elder_financial_exploitation_flags.csv"),
        "comptroller_context": read_csv_safe(TABLES_DIR / "comptroller_public_sector_fraud_context.csv"),
        "comptroller_flags": read_csv_safe(TABLES_DIR / "comptroller_public_sector_fraud_flags.csv"),
        "ofac_summary": read_csv_safe(TABLES_DIR / "ofac_tennessee_context_summary.csv"),
        "ofac_flags": read_csv_safe(TABLES_DIR / "ofac_tennessee_context_flags.csv"),
        "ofac_matches": read_csv_safe(TABLES_DIR / "ofac_tennessee_address_matches.csv"),
        "current_indicators_context": read_csv_safe(TABLES_DIR / "current_indicators_context.csv"),
        "current_indicators_flags": read_csv_safe(TABLES_DIR / "current_indicators_flags.csv"),
    }


def metric_from_scorecard(scorecard: pd.DataFrame, dimension: str, column: str):
    """
    Pull a value from the scorecard by dimension.
    """

    if scorecard.empty:
        return "N/A"

    if "dimension" not in scorecard.columns or column not in scorecard.columns:
        return "N/A"

    rows = scorecard[
        scorecard["dimension"].astype(str).str.lower().eq(dimension.lower())
    ]

    if rows.empty:
        return "N/A"

    return rows.iloc[0].get(column, "N/A")


def get_pressure_row(pressure_index: pd.DataFrame) -> dict:
    """
    Pull the first SAR Pressure Index row as a dict.
    """

    if pressure_index.empty:
        return {}

    return pressure_index.iloc[0].to_dict()


def filter_by_search(df: pd.DataFrame, search_text: str) -> pd.DataFrame:
    """
    Search all columns in a dataframe.
    """

    if df.empty or not search_text:
        return df

    search_text = search_text.lower()

    mask = df.astype(str).apply(
        lambda row: row.str.lower().str.contains(search_text, na=False).any(),
        axis=1,
    )

    return df[mask]


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------

tables = load_all_tables()

trend_summary = tables["trend_summary"]
industry_summary = tables["industry_summary"]
sar_pressure_index = tables["sar_pressure_index"]
sar_pressure_components = tables["sar_pressure_components"]
scorecard = tables["intelligence_scorecard"]
methodology_matrix = tables["methodology_matrix"]
change_detection_flags = tables["change_detection_flags"]
change_detection_summary = tables["change_detection_summary"]
scenario_summary = tables["scenario_summary"]
scenario_projections = tables["scenario_projections"]
sensitivity = tables["sensitivity"]
category_summary = tables["category_summary"]
top_categories = tables["top_categories"]
high_risk_categories = tables["high_risk_categories"]
tbi_summary = tables["tbi_summary"]
fbi_summary = tables["fbi_summary"]
elder_context = tables["elder_context"]
comptroller_context = tables["comptroller_context"]
ofac_summary = tables["ofac_summary"]
ofac_matches = tables["ofac_matches"]
current_indicators_context = tables["current_indicators_context"]


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------

st.sidebar.markdown("## 📊 Dashboard Navigation")
st.sidebar.caption("Tennessee Financial Crime Intelligence Dashboard")

section_group = st.sidebar.selectbox(
    "Dashboard area",
    [
        "Executive Overview",
        "Core SAR Model",
        "Context Layers",
        "Appendix & Downloads",
    ],
)

if section_group == "Executive Overview":
    page_options = [
        "Overview",
        "Scorecard",
        "Methodology",
    ]
elif section_group == "Core SAR Model":
    page_options = [
        "SAR Trends",
        "Industry Concentration",
        "Category Intelligence",
        "SAR Pressure Index",
        "Change Detection",
        "Scenario & Sensitivity",
    ]
elif section_group == "Context Layers":
    page_options = [
        "Law-Enforcement Context",
        "Elder Exploitation",
        "Comptroller Context",
        "OFAC Context",
        "Current Indicators",
    ]
else:
    page_options = [
        "Source Appendix",
        "Downloads",
    ]

page = st.sidebar.radio("Select a section", page_options)

st.sidebar.markdown("---")

if REPORT_FILE.exists():
    with open(REPORT_FILE, "rb") as pdf_file:
        st.sidebar.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_file,
            file_name=REPORT_FILE.name,
            mime="application/pdf",
            use_container_width=True,
        )
else:
    st.sidebar.info("PDF report not found. Run `python main.py` first.")

st.sidebar.markdown("---")
st.sidebar.caption("Core model: FinCEN SAR Stats | Context: TBI, FBI/NIBRS, Comptroller, OFAC")


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

st.markdown(
    """
    <div style="height: 0.4rem;"></div>
    <div class="main-title">Tennessee Financial Crime Intelligence Dashboard</div>
    <div class="main-subtitle">
        SAR trends, law-enforcement context, sanctions geography, public-sector fraud indicators,
        current monitoring signals, and financial crime intelligence interpretation.
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Overview
# ------------------------------------------------------------

if page == "Overview":
    render_hero()
    render_methodology_boundary_card()

    pressure_row = get_pressure_row(sar_pressure_index)

    latest_year = pressure_row.get("latest_year", "N/A")
    pressure_score = pressure_row.get("sar_pressure_index", None)
    pressure_signal = pressure_row.get("signal", "N/A")

    render_kpi_cards(
        [
            {
                "label": "Latest Year",
                "value": str(latest_year),
                "note": "Latest SAR model year",
            },
            {
                "label": "SAR Pressure Index",
                "value": f"{format_float(pressure_score)} / 100",
                "note": "Composite reporting-pressure score",
            },
            {
                "label": "Signal",
                "value": str(pressure_signal),
                "note": "Model classification",
            },
            {
                "label": "Current Indicator Rows",
                "value": (
                    format_number(len(current_indicators_context))
                    if not current_indicators_context.empty
                    else "0"
                ),
                "note": "Forward-looking context indicators",
            },
        ]
    )

    st.markdown("---")

    section_intro(
        "Executive Intelligence Snapshot",
        "A compact view of the primary model and context-layer signals.",
    )

    snapshot_rows = []

    if not scorecard.empty:
        for dimension in [
            "Overall SAR Pressure",
            "Tennessee SAR Trend Pressure",
            "National Divergence",
            "Industry Concentration",
            "High-Risk Category Context",
            "OFAC Context",
            "Current Indicators",
        ]:
            signal = metric_from_scorecard(scorecard, dimension, "signal")
            status = metric_from_scorecard(scorecard, dimension, "score_or_status")
            evidence = metric_from_scorecard(scorecard, dimension, "evidence")

            snapshot_rows.append(
                {
                    "Dimension": dimension,
                    "Signal": signal,
                    "Status": status,
                    "Evidence": evidence,
                }
            )

    if snapshot_rows:
        table_card(pd.DataFrame(snapshot_rows), "Snapshot Table", height=300)
    else:
        st.info("Scorecard output is not available yet.")

    col_a, col_b = st.columns(2)

    with col_a:
        chart_card(
            CHARTS_DIR / "tennessee_sar_trend.png",
            "Tennessee SAR Filings Trend",
        )

    with col_b:
        chart_card(
            CHARTS_DIR / "tennessee_vs_us_sar_index.png",
            "Tennessee vs U.S. SAR Growth Index",
        )


# ------------------------------------------------------------
# Scorecard
# ------------------------------------------------------------

elif page == "Scorecard":
    section_intro(
        "Financial Crime Intelligence Scorecard",
        "A front-of-dashboard summary of model-driven signals and supporting context layers.",
    )

    render_how_to_read(
        "Use the scorecard as a one-page intelligence summary. Rows marked Yes are part of the "
        "SAR-based model. Rows marked No are supporting context only. A higher score does not prove "
        "financial crime; it indicates stronger reporting pressure, concentration, or contextual monitoring relevance."
    )

    table_card(scorecard, "Scorecard", height=450)
    download_button_for_csv(
        scorecard,
        "financial_crime_intelligence_scorecard.csv",
        "Download Scorecard CSV",
    )


# ------------------------------------------------------------
# Methodology
# ------------------------------------------------------------

elif page == "Methodology":
    section_intro(
        "Methodology Matrix",
        "How the dashboard separates SAR model inputs from supporting context layers.",
    )

    render_how_to_read(
        "Only FinCEN SAR Stats data feeds the core SAR model. TBI, FBI/NIBRS, Comptroller, OFAC, "
        "elder exploitation, and current indicators are used to support interpretation, not to change the core SAR score."
    )

    render_methodology_boundary_card()
    table_card(methodology_matrix, "Methodology Matrix", height=460)

    download_button_for_csv(
        methodology_matrix,
        "methodology_matrix.csv",
        "Download Methodology Matrix CSV",
    )


# ------------------------------------------------------------
# SAR Trends
# ------------------------------------------------------------

elif page == "SAR Trends":
    section_intro(
        "Tennessee vs U.S. SAR Trend Analysis",
        "Long-run Tennessee SAR filings compared with broader U.S. SAR filing growth.",
    )

    render_how_to_read(
        "SAR filings measure reporting activity and monitoring behavior. They should not be interpreted as "
        "confirmed financial crime."
    )

    table_card(trend_summary, "Trend Summary", height=240)

    col_a, col_b = st.columns(2)

    with col_a:
        chart_card(CHARTS_DIR / "tennessee_sar_trend.png", "Tennessee SAR Filings")

    with col_b:
        chart_card(CHARTS_DIR / "tennessee_vs_us_sar_index.png", "Indexed SAR Trend Comparison")

    download_button_for_csv(
        trend_summary,
        "trend_summary.csv",
        "Download Trend Summary CSV",
    )


# ------------------------------------------------------------
# Industry Concentration
# ------------------------------------------------------------

elif page == "Industry Concentration":
    section_intro(
        "Tennessee SAR Industry Concentration",
        "Which filing industries account for extracted Tennessee SAR activity.",
    )

    render_how_to_read(
        "Industry concentration is part of the SAR Pressure Index because it helps identify reporting-channel "
        "concentration. It does not identify individual institutions or cases."
    )

    if not industry_summary.empty:
        top_industry = industry_summary.iloc[0]

        render_kpi_cards(
            [
                {
                    "label": "Top Industry",
                    "value": str(top_industry.get("industry_name", "N/A")),
                    "note": "Largest latest-year filing industry",
                },
                {
                    "label": "Latest Filings",
                    "value": format_number(top_industry.get("end_filings")),
                    "note": "Top industry filing count",
                },
                {
                    "label": "Latest Share",
                    "value": format_pct(top_industry.get("latest_year_share")),
                    "note": "Share of extracted Tennessee filings",
                },
                {
                    "label": "Peak Year",
                    "value": str(top_industry.get("peak_year", "N/A")),
                    "note": "Top industry peak year",
                },
            ]
        )

    table_card(industry_summary, "Industry Summary", height=420)
    chart_card(CHARTS_DIR / "tennessee_sar_by_industry.png", "SAR Filings by Industry")

    download_button_for_csv(
        industry_summary,
        "industry_summary.csv",
        "Download Industry Summary CSV",
    )


# ------------------------------------------------------------
# Category Intelligence
# ------------------------------------------------------------

elif page == "Category Intelligence":
    section_intro(
        "Suspicious Activity Category Intelligence",
        "SAR-theme context extracted from FinCEN industry exhibits.",
    )

    render_how_to_read(
        "Read suspicious activity categories as SAR-theme intelligence, not Tennessee-specific category counts "
        "unless source data explicitly supports that state-level breakdown."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Top Categories",
            "High-Risk Categories",
            "Category Summary",
        ]
    )

    with tab1:
        table_card(top_categories, "Top Suspicious Activity Categories", height=420)
        chart_card(CHARTS_DIR / "top_suspicious_activity_categories.png", "Top Categories")
        download_button_for_csv(
            top_categories,
            "top_suspicious_activity_categories_latest_year.csv",
            "Download Top Categories CSV",
        )

    with tab2:
        table_card(high_risk_categories, "High-Risk Categories", height=420)
        chart_card(
            CHARTS_DIR / "high_risk_suspicious_activity_categories.png",
            "High-Risk Suspicious Activity Themes",
        )
        download_button_for_csv(
            high_risk_categories,
            "high_risk_suspicious_activity_categories.csv",
            "Download High-Risk Categories CSV",
        )

    with tab3:
        search_text = st.text_input("Search category summary")
        filtered_category_summary = filter_by_search(category_summary, search_text)
        table_card(filtered_category_summary, "Category Summary", height=500)
        download_button_for_csv(
            category_summary,
            "suspicious_activity_category_summary.csv",
            "Download Category Summary CSV",
        )


# ------------------------------------------------------------
# SAR Pressure Index
# ------------------------------------------------------------

elif page == "SAR Pressure Index":
    section_intro(
        "Tennessee SAR Pressure Index",
        "A composite SAR-based signal for strategic reporting-pressure interpretation.",
    )

    render_how_to_read(
        "The SAR Pressure Index is a structured reporting-pressure signal, not a crime rate. "
        "It combines SAR growth, recent momentum, national divergence, industry concentration, and high-risk category context."
    )

    pressure_row = get_pressure_row(sar_pressure_index)

    render_kpi_cards(
        [
            {
                "label": "Latest Year",
                "value": str(pressure_row.get("latest_year", "N/A")),
                "note": "Model reference year",
            },
            {
                "label": "Index Score",
                "value": f"{format_float(pressure_row.get('sar_pressure_index'))} / 100",
                "note": "Composite SAR-based score",
            },
            {
                "label": "Signal",
                "value": str(pressure_row.get("signal", "N/A")),
                "note": "Reporting-pressure interpretation",
            },
            {
                "label": "Model Scope",
                "value": "SAR Only",
                "note": "Context layers excluded from score",
            },
        ]
    )

    col_a, col_b = st.columns([1, 1])

    with col_a:
        table_card(sar_pressure_index, "SAR Pressure Index", height=180)

    with col_b:
        table_card(sar_pressure_components, "Index Components", height=300)

    download_button_for_csv(
        sar_pressure_index,
        "sar_pressure_index.csv",
        "Download SAR Pressure Index CSV",
    )

    download_button_for_csv(
        sar_pressure_components,
        "sar_pressure_components.csv",
        "Download Components CSV",
    )


# ------------------------------------------------------------
# Change Detection
# ------------------------------------------------------------

elif page == "Change Detection":
    section_intro(
        "Integrated Change Detection",
        "Model and context-layer flags for notable analytical movements.",
    )

    render_how_to_read(
        "Change-detection severity reflects analytical importance within this project. It is not legal severity, "
        "confirmed criminal activity, or enforcement priority."
    )

    if not change_detection_flags.empty and "severity" in change_detection_flags.columns:
        severity_options = sorted(change_detection_flags["severity"].dropna().unique().tolist())

        severity_filter = st.multiselect(
            "Filter by severity",
            severity_options,
            default=severity_options,
        )

        filtered_flags = change_detection_flags[
            change_detection_flags["severity"].isin(severity_filter)
        ]
    else:
        filtered_flags = change_detection_flags

    table_card(filtered_flags, "Change Detection Flags", height=520)
    table_card(change_detection_summary, "Change Detection Summary", height=260)

    download_button_for_csv(
        change_detection_flags,
        "change_detection_flags.csv",
        "Download Change Detection Flags CSV",
    )


# ------------------------------------------------------------
# Scenario & Sensitivity
# ------------------------------------------------------------

elif page == "Scenario & Sensitivity":
    section_intro(
        "Scenario & Sensitivity Analysis",
        "Forward-looking SAR filing assumptions and SAR Pressure Index weighting stability.",
    )

    render_how_to_read(
        "Scenarios are assumption-based projections, not forecasts. Sensitivity analysis tests how stable "
        "the SAR Pressure Index is under alternative weighting assumptions."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Scenario Summary",
            "Scenario Projections",
            "Sensitivity",
        ]
    )

    with tab1:
        table_card(scenario_summary, "Scenario Summary", height=320)
        chart_card(CHARTS_DIR / "tennessee_sar_scenario_projection.png", "Scenario Projection Chart")
        download_button_for_csv(
            scenario_summary,
            "sar_scenario_summary.csv",
            "Download Scenario Summary CSV",
        )

    with tab2:
        table_card(scenario_projections, "Scenario Projections", height=500)
        download_button_for_csv(
            scenario_projections,
            "sar_scenario_projections.csv",
            "Download Scenario Projections CSV",
        )

    with tab3:
        table_card(sensitivity, "Sensitivity Results", height=360)
        chart_card(CHARTS_DIR / "sar_pressure_sensitivity.png", "Sensitivity Chart")
        download_button_for_csv(
            sensitivity,
            "sar_pressure_sensitivity.csv",
            "Download Sensitivity CSV",
        )


# ------------------------------------------------------------
# Law-Enforcement Context
# ------------------------------------------------------------

elif page == "Law-Enforcement Context":
    section_intro(
        "Law-Enforcement Context: TBI and FBI/NIBRS",
        "Reported offense context for financial-crime-adjacent themes.",
    )

    render_how_to_read(
        "TBI and FBI/NIBRS counts are reported offense context, not SAR filings. Use this section to compare "
        "SAR themes with broader fraud, identity theft, exploitation, and financial-crime-adjacent offense patterns."
    )

    tab1, tab2 = st.tabs(["TBI / TIBRS", "FBI / NIBRS"])

    with tab1:
        table_card(tbi_summary, "TBI / TIBRS Context Summary", height=420)
        chart_card(CHARTS_DIR / "tbi_financial_crime_context.png", "TBI Financial-Crime Context")
        download_button_for_csv(
            tbi_summary,
            "tbi_financial_crime_context_summary.csv",
            "Download TBI Context CSV",
        )

    with tab2:
        table_card(fbi_summary, "FBI / NIBRS Context Summary", height=420)
        chart_card(CHARTS_DIR / "fbi_financial_crime_context.png", "FBI / NIBRS Context")
        download_button_for_csv(
            fbi_summary,
            "fbi_financial_crime_context_summary.csv",
            "Download FBI Context CSV",
        )


# ------------------------------------------------------------
# Elder Exploitation
# ------------------------------------------------------------

elif page == "Elder Exploitation":
    section_intro(
        "Elder Financial Exploitation Context",
        "Victim-risk, policy, SAR-theme, and law-enforcement context.",
    )

    render_how_to_read(
        "This is victim-risk and policy context. It connects elder exploitation to SAR themes and law-enforcement context, "
        "but it is not a Tennessee-specific elder SAR count unless source data explicitly supports that."
    )

    table_card(elder_context, "Elder Exploitation Context", height=500)
    chart_card(CHARTS_DIR / "elder_financial_exploitation_context.png", "Elder Financial Exploitation Context")

    download_button_for_csv(
        elder_context,
        "elder_financial_exploitation_context.csv",
        "Download Elder Context CSV",
    )


# ------------------------------------------------------------
# Comptroller Context
# ------------------------------------------------------------

elif page == "Comptroller Context":
    section_intro(
        "Comptroller Public-Sector Fraud and Audit Context",
        "Fraud, waste, abuse, allegation, hotline, audit, and oversight context.",
    )

    render_how_to_read(
        "Comptroller data reflects fraud, waste, abuse, hotline, allegation, audit, and oversight context. "
        "It is not SAR activity, confirmed fraud, charges, or convictions."
    )

    table_card(comptroller_context, "Comptroller Context", height=460)
    chart_card(
        CHARTS_DIR / "comptroller_public_sector_fraud_context.png",
        "Comptroller Public-Sector Fraud Context",
    )

    download_button_for_csv(
        comptroller_context,
        "comptroller_public_sector_fraud_context.csv",
        "Download Comptroller Context CSV",
    )


# ------------------------------------------------------------
# OFAC Context
# ------------------------------------------------------------

elif page == "OFAC Context":
    section_intro(
        "OFAC Sanctions Geography Context",
        "Sanctions-list address screening for accepted Tennessee-related geography indicators.",
    )

    render_how_to_read(
        "OFAC screening is sanctions-geography context only. A match would not prove Tennessee SAR activity, "
        "local criminal activity, or enforcement action."
    )

    if not ofac_summary.empty and "metric" in ofac_summary.columns:
        total_matches_rows = ofac_summary[
            ofac_summary["metric"].astype(str).str.lower().eq("tennessee ofac address matches")
        ]

        if not total_matches_rows.empty:
            matches_value = total_matches_rows.iloc[0].get("value", 0)

            render_kpi_cards(
                [
                    {
                        "label": "Accepted Tennessee OFAC Address Matches",
                        "value": format_number(matches_value),
                        "note": "After stricter geography validation",
                    },
                    {
                        "label": "Interpretation",
                        "value": "Context Only",
                        "note": "Not evidence of SAR activity or local criminal activity",
                    },
                    {
                        "label": "Screening Scope",
                        "value": "SDN + Non-SDN",
                        "note": "Public OFAC address files",
                    },
                    {
                        "label": "Model Impact",
                        "value": "Excluded",
                        "note": "Not included in SAR Pressure Index",
                    },
                ]
            )

    table_card(ofac_summary, "OFAC Context Summary", height=260)
    table_card(ofac_matches, "Accepted Tennessee Address Matches", height=360)
    chart_card(CHARTS_DIR / "ofac_tennessee_programs.png", "OFAC Tennessee Program Context")

    download_button_for_csv(
        ofac_summary,
        "ofac_tennessee_context_summary.csv",
        "Download OFAC Summary CSV",
    )

    download_button_for_csv(
        ofac_matches,
        "ofac_tennessee_address_matches.csv",
        "Download OFAC Matches CSV",
    )


# ------------------------------------------------------------
# Current Indicators
# ------------------------------------------------------------

elif page == "Current Indicators":
    section_intro(
        "Looking Forward: 2025-2026 Current Indicators",
        "Current monitoring layer kept separate from the 2014-2024 SAR model.",
    )

    render_how_to_read(
        "Current indicators keep the report timely, but they are not blended into the comparable 2014-2024 "
        "SAR trend model or SAR Pressure Index."
    )

    table_card(current_indicators_context, "Current Indicators", height=500)

    download_button_for_csv(
        current_indicators_context,
        "current_indicators_context.csv",
        "Download Current Indicators CSV",
    )


# ------------------------------------------------------------
# Source Appendix
# ------------------------------------------------------------

elif page == "Source Appendix":
    section_intro(
        "Source Appendix",
        "Public source references and methodological limitations.",
    )

    render_how_to_read(
        "The dashboard uses public aggregated SAR data and contextual public-source materials. "
        "Source references support auditability but do not change the model outputs."
    )

    source_df = source_dataframe()
    table_card(source_df, "Source References", height=540)

    download_button_for_csv(
        source_df,
        "source_appendix.csv",
        "Download Source Appendix CSV",
    )


# ------------------------------------------------------------
# Downloads
# ------------------------------------------------------------

elif page == "Downloads":
    section_intro(
        "Downloads",
        "Download the final PDF report and generated project output tables.",
    )

    if REPORT_FILE.exists():
        with open(REPORT_FILE, "rb") as pdf_file:
            st.download_button(
                label="Download Final PDF Report",
                data=pdf_file,
                file_name=REPORT_FILE.name,
                mime="application/pdf",
                use_container_width=True,
            )
    else:
        st.warning("PDF report was not found. Run `python main.py` first.")

    st.markdown("---")
    st.subheader("Key Tables")

    table_downloads = {
        "trend_summary.csv": trend_summary,
        "industry_summary.csv": industry_summary,
        "sar_pressure_index.csv": sar_pressure_index,
        "sar_pressure_components.csv": sar_pressure_components,
        "financial_crime_intelligence_scorecard.csv": scorecard,
        "methodology_matrix.csv": methodology_matrix,
        "change_detection_flags.csv": change_detection_flags,
        "sar_scenario_summary.csv": scenario_summary,
        "sar_pressure_sensitivity.csv": sensitivity,
        "top_suspicious_activity_categories_latest_year.csv": top_categories,
        "high_risk_suspicious_activity_categories.csv": high_risk_categories,
        "tbi_financial_crime_context_summary.csv": tbi_summary,
        "fbi_financial_crime_context_summary.csv": fbi_summary,
        "elder_financial_exploitation_context.csv": elder_context,
        "comptroller_public_sector_fraud_context.csv": comptroller_context,
        "ofac_tennessee_context_summary.csv": ofac_summary,
        "ofac_tennessee_address_matches.csv": ofac_matches,
        "current_indicators_context.csv": current_indicators_context,
    }

    for filename, df in table_downloads.items():
        download_button_for_csv(df, filename, f"Download {filename}")