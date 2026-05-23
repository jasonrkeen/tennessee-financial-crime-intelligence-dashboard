from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.config import (
    CHARTS_DIR,
    PROJECT_TITLE,
    REPORT_FILE,
    TABLES_DIR,
)


def read_csv_safe(path: Path) -> pd.DataFrame:
    """
    Safely read a CSV file.
    """

    if not path.exists():
        print(f"Missing table: {path}")
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception as exc:
        print(f"Could not read {path}: {exc}")
        return pd.DataFrame()


def format_number(value):
    """
    Format numbers for report display.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.0f}"
    except Exception:
        return str(value)


def format_float(value, decimals: int = 2):
    """
    Format floats for report display.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return str(value)


def format_pct(value):
    """
    Format decimal values as percentages.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value) * 100:,.1f}%"
    except Exception:
        return str(value)


def format_year(value):
    """
    Format year-like values safely.
    """

    if pd.isna(value):
        return "N/A"

    try:
        return str(int(value))
    except Exception:
        return str(value)


def format_context_value(value):
    """
    Format mixed numeric / qualitative context values for report tables.
    """

    if pd.isna(value):
        return "Qualitative"

    text = str(value).strip()

    if text.lower() in {"nan", "none", ""}:
        return "Qualitative"

    numeric_value = pd.to_numeric(value, errors="coerce")

    if pd.isna(numeric_value):
        return text

    return f"{numeric_value:,.0f}"


def truncate_text(value, max_len: int = 110) -> str:
    """
    Truncate long table text.
    """

    text = str(value)

    if len(text) <= max_len:
        return text

    return text[: max_len - 3] + "..."


def escape_paragraph_text(value) -> str:
    """
    Escape XML-sensitive characters for ReportLab Paragraph rendering.
    """

    text = str(value)

    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def wrap_cell_text(value, style, max_len: int | None = None):
    """
    Convert table cell values into ReportLab Paragraphs so text wraps
    inside table boundaries.
    """

    if value is None:
        text = ""
    else:
        try:
            if pd.isna(value):
                text = ""
            else:
                text = str(value)
        except Exception:
            text = str(value)

    if max_len is not None:
        text = truncate_text(text, max_len)

    text = escape_paragraph_text(text)

    return Paragraph(text, style)


def build_styles():
    """
    Build report paragraph styles.
    """

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=18,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading1"],
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor("#1F2937"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubsectionHeader",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor("#374151"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#555555"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="Finding",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            leftIndent=10,
            bulletIndent=0,
            spaceAfter=5,
        )
    )

    return styles


def make_table(data, col_widths=None, font_size=7.5):
    """
    Create a styled ReportLab table with wrapped cell text.
    """

    base_styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        name=f"TableHeader_{font_size}",
        parent=base_styles["BodyText"],
        fontSize=font_size,
        leading=font_size + 2,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        wordWrap="CJK",
        splitLongWords=True,
    )

    cell_style = ParagraphStyle(
        name=f"TableCell_{font_size}",
        parent=base_styles["BodyText"],
        fontSize=font_size,
        leading=font_size + 2,
        alignment=TA_LEFT,
        wordWrap="CJK",
        splitLongWords=True,
    )

    wrapped_data = []

    for row_idx, row in enumerate(data):
        wrapped_row = []

        for cell in row:
            style = header_style if row_idx == 0 else cell_style
            wrapped_row.append(wrap_cell_text(cell, style))

        wrapped_data.append(wrapped_row)

    table = Table(
        wrapped_data,
        colWidths=col_widths,
        repeatRows=1,
        splitByRow=True,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F9FAFB")],
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    return table


def add_chart(story, chart_path: Path, styles, width=6.7 * inch):
    """
    Add a chart image if it exists.
    """

    if chart_path.exists():
        story.append(Image(str(chart_path), width=width, height=width * 0.58))
        story.append(Spacer(1, 0.15 * inch))
    else:
        story.append(Paragraph(f"Chart not found: {chart_path.name}", styles["Small"]))
        story.append(Spacer(1, 0.1 * inch))


def add_how_to_read_box(story, styles, text: str):
    """
    Add a short reader guidance box before interpretation-heavy sections.
    """

    box_data = [
        ["How to Read This Section"],
        [text],
    ]

    table = make_table(
        box_data,
        col_widths=[6.7 * inch],
        font_size=7.3,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F3F4F6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#9CA3AF")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 0.12 * inch))


def load_report_inputs():
    """
    Load all tables used in the PDF report.
    """

    return {
        "trend_summary": read_csv_safe(TABLES_DIR / "trend_summary.csv"),
        "industry_summary": read_csv_safe(TABLES_DIR / "industry_summary.csv"),
        "key_findings": TABLES_DIR / "key_findings.txt",
        "sar_pressure_index": read_csv_safe(TABLES_DIR / "sar_pressure_index.csv"),
        "sar_pressure_components": read_csv_safe(TABLES_DIR / "sar_pressure_components.csv"),
        "change_detection_flags": read_csv_safe(TABLES_DIR / "change_detection_flags.csv"),
        "scenario_summary": read_csv_safe(TABLES_DIR / "sar_scenario_summary.csv"),
        "sensitivity": read_csv_safe(TABLES_DIR / "sar_pressure_sensitivity.csv"),
        "top_categories": read_csv_safe(TABLES_DIR / "top_suspicious_activity_categories_latest_year.csv"),
        "high_risk_categories": read_csv_safe(TABLES_DIR / "high_risk_suspicious_activity_categories.csv"),
        "tbi_summary": read_csv_safe(TABLES_DIR / "tbi_financial_crime_context_summary.csv"),
        "tbi_flags": read_csv_safe(TABLES_DIR / "tbi_financial_crime_context_flags.csv"),
        "fbi_summary": read_csv_safe(TABLES_DIR / "fbi_financial_crime_context_summary.csv"),
        "fbi_flags": read_csv_safe(TABLES_DIR / "fbi_financial_crime_context_flags.csv"),
        "elder_context": read_csv_safe(TABLES_DIR / "elder_financial_exploitation_context.csv"),
        "elder_flags": read_csv_safe(TABLES_DIR / "elder_financial_exploitation_flags.csv"),
        "ofac_summary": read_csv_safe(TABLES_DIR / "ofac_tennessee_context_summary.csv"),
        "ofac_flags": read_csv_safe(TABLES_DIR / "ofac_tennessee_context_flags.csv"),
        "ofac_matches": read_csv_safe(TABLES_DIR / "ofac_tennessee_address_matches.csv"),
        "tbi_cid_context": read_csv_safe(TABLES_DIR / "tbi_criminal_investigation_division_context.csv"),
        "comptroller_context": read_csv_safe(TABLES_DIR / "comptroller_public_sector_fraud_context.csv"),
        "current_indicators_context": read_csv_safe(TABLES_DIR / "current_indicators_context.csv"),
        "current_indicators_flags": read_csv_safe(TABLES_DIR / "current_indicators_flags.csv"),
        "methodology_matrix": read_csv_safe(TABLES_DIR / "methodology_matrix.csv"),
        "intelligence_scorecard": read_csv_safe(TABLES_DIR / "financial_crime_intelligence_scorecard.csv"),
    }


def read_key_findings(path: Path) -> list[str]:
    """
    Read key findings from the text output.
    """

    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    findings = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line[0:2].isdigit() or line[:1].isdigit():
            parts = line.split(".", 1)
            if len(parts) == 2:
                findings.append(parts[1].strip())

    return findings


def add_title_page(story, styles, sar_pressure_index: pd.DataFrame):
    """
    Add title and executive overview.
    """

    story.append(Paragraph(PROJECT_TITLE, styles["ReportTitle"]))
    story.append(
        Paragraph(
            "SAR Trends, Law-Enforcement Context, Sanctions Geography, "
            "Public-Sector Fraud Indicators, and Current Monitoring Signals",
            styles["ReportSubtitle"],
        )
    )

    story.append(
        Paragraph(
            "Prepared by Jason Keen | keenjasonr@gmail.com",
            styles["ReportSubtitle"],
        )
    )

    if not sar_pressure_index.empty:
        row = sar_pressure_index.iloc[0]
        score = format_float(row.get("sar_pressure_index"), 2)
        signal = row.get("signal", "N/A")
        year = row.get("latest_year", "N/A")

        score_table = [
            ["Latest Year", "SAR Pressure Index", "Signal"],
            [str(year), f"{score} / 100", str(signal)],
        ]

        story.append(
            make_table(
                score_table,
                col_widths=[1.6 * inch, 2.0 * inch, 2.4 * inch],
                font_size=9,
            )
        )
        story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Executive Summary", styles["SectionHeader"]))
    story.append(
        Paragraph(
            "This report analyzes public FinCEN SAR Stats data to evaluate Tennessee SAR filing trends "
            "relative to national filings, identify Tennessee industry-level SAR concentration, summarize "
            "suspicious activity category themes, and build a SAR Pressure Index. The report also adds "
            "supporting law-enforcement, public-sector fraud, policy, exploitation, and sanctions context "
            "from TBI/TIBRS, FBI/NIBRS, elder financial exploitation materials, Tennessee Comptroller "
            "public-sector fraud materials, OFAC sanctions geography indicators, and current monitoring "
            "signals. The analysis is designed as strategic financial intelligence and does not use raw SAR "
            "narratives, transaction-level records, or institution-specific case data.",
            styles["Body"],
        )
    )


def add_key_findings(story, styles, findings: list[str]):
    """
    Add key findings section.
    """

    story.append(Paragraph("Key Findings", styles["SectionHeader"]))

    if not findings:
        story.append(Paragraph("No key findings file was available.", styles["Body"]))
        return

    for finding in findings:
        story.append(Paragraph(f"- {finding}", styles["Finding"]))


def add_intelligence_scorecard_section(story, styles, scorecard: pd.DataFrame):
    """
    Add front-of-report Financial Crime Intelligence Scorecard.
    """

    if scorecard.empty:
        return

    story.append(PageBreak())
    story.append(Paragraph("Financial Crime Intelligence Scorecard", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "The scorecard summarizes the project’s major analytical signals in one view. "
            "It is an interpretation layer only and does not change the SAR Pressure Index methodology.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "Use this scorecard as a one-page intelligence summary. Rows marked 'Yes' are part of "
            "the SAR-based model. Rows marked 'No' are supporting context only. A higher score does "
            "not prove financial crime; it indicates stronger reporting pressure, concentration, or "
            "contextual monitoring relevance."
        ),
    )

    rows = [["Dimension", "Signal", "Status", "Evidence", "Index?"]]

    for _, row in scorecard.iterrows():
        rows.append(
            [
                truncate_text(row.get("dimension", ""), 28),
                truncate_text(row.get("signal", ""), 24),
                truncate_text(row.get("score_or_status", ""), 22),
                truncate_text(row.get("evidence", ""), 82),
                truncate_text(row.get("included_in_sar_pressure_index", ""), 8),
            ]
        )

    story.append(
        make_table(
            rows,
            col_widths=[
                1.35 * inch,
                1.15 * inch,
                1.0 * inch,
                2.55 * inch,
                0.55 * inch,
            ],
            font_size=5.9,
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Methodology note: rows marked “Yes” are SAR-based model components. Rows marked “No” "
            "are supporting context layers and should not be interpreted as direct SAR activity.",
            styles["Small"],
        )
    )


def add_methodology(story, styles):
    """
    Add methodology section.
    """

    story.append(Paragraph("Data and Methodology", styles["SectionHeader"]))
    story.append(
        Paragraph(
            "The project downloads FinCEN SAR Stats Excel workbooks by filing-industry section, extracts "
            "annual U.S. total rows from Exhibit 1, extracts Tennessee annual rows from Exhibit 2, and uses "
            "later exhibits to summarize suspicious activity category themes. Tennessee and U.S. SAR filings "
            "are indexed to 2014 = 100 to compare growth paths. The SAR Pressure Index combines long-run "
            "Tennessee growth, recent momentum, Tennessee-vs-U.S. divergence, industry concentration, and "
            "high-risk category context.",
            styles["Body"],
        )
    )

    story.append(
        Paragraph(
            "The TBI, FBI, elder financial exploitation, Comptroller, OFAC, TBI CID, and current-indicator "
            "layers are supporting context layers. They are not included in the SAR Pressure Index because "
            "they measure different things: law-enforcement reported offenses, investigative capability, "
            "policy/victim-risk context, public-sector fraud controls, sanctions-list address indicators, "
            "and forward-looking monitoring signals.",
            styles["Small"],
        )
    )

    story.append(
        Paragraph(
            "Important limitation: suspicious activity category exhibits are treated as industry-level / national "
            "context. They are not interpreted as Tennessee-specific category counts unless FinCEN explicitly "
            "provides that state-level category breakdown.",
            styles["Small"],
        )
    )


def add_methodology_matrix_section(story, styles, methodology_matrix: pd.DataFrame):
    """
    Add methodology matrix section.
    """

    if methodology_matrix.empty:
        return

    story.append(PageBreak())
    story.append(Paragraph("Methodology Matrix", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "This matrix documents each source layer used in the project, what it measures, "
            "how it is used, whether it is included in the SAR Pressure Index, and the main "
            "interpretive limitation.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "Use this matrix to understand what each data layer measures and how it should be interpreted. "
            "Only FinCEN SAR Stats feeds the SAR Pressure Index. TBI, FBI, Comptroller, OFAC, elder exploitation, "
            "and current-indicator layers are used to support interpretation, not to change the core SAR score."
        ),
    )

    rows = [["Layer", "What It Measures", "Index?", "Key Limitation"]]

    for _, row in methodology_matrix.iterrows():
        rows.append(
            [
                truncate_text(row.get("layer", ""), 24),
                truncate_text(row.get("what_it_measures", ""), 92),
                truncate_text(row.get("included_in_sar_pressure_index", ""), 8),
                truncate_text(row.get("key_limitation", ""), 105),
            ]
        )

    story.append(
        make_table(
            rows,
            col_widths=[
                1.3 * inch,
                2.2 * inch,
                0.6 * inch,
                2.5 * inch,
            ],
            font_size=5.9,
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Methodology note: only the FinCEN SAR Stats layer is included in the SAR Pressure Index. "
            "All other layers are supporting context and should not be interpreted as direct measures of SAR activity.",
            styles["Small"],
        )
    )


def add_trend_section(story, styles, trend_summary: pd.DataFrame):
    """
    Add trend summary and charts.
    """

    story.append(PageBreak())
    story.append(Paragraph("Tennessee vs U.S. SAR Trend Analysis", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "This section compares Tennessee SAR filing growth against U.S. SAR filing growth across the "
            "2014-2024 study period.",
            styles["Body"],
        )
    )

    if not trend_summary.empty:
        rows = [["Metric", "Start", "End", "Total Growth", "CAGR", "Peak Year"]]

        for _, row in trend_summary.iterrows():
            rows.append(
                [
                    truncate_text(row.get("metric", ""), 32),
                    format_number(row.get("start_value")),
                    format_number(row.get("end_value")),
                    format_pct(row.get("total_growth_pct")),
                    format_pct(row.get("cagr")),
                    format_year(row.get("peak_year")),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    2.0 * inch,
                    1.0 * inch,
                    1.0 * inch,
                    1.0 * inch,
                    0.9 * inch,
                    0.8 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

    add_chart(story, CHARTS_DIR / "tennessee_sar_trend.png", styles)
    add_chart(story, CHARTS_DIR / "tennessee_vs_us_sar_index.png", styles)


def add_industry_section(story, styles, industry_summary: pd.DataFrame):
    """
    Add industry concentration section.
    """

    story.append(PageBreak())
    story.append(Paragraph("Tennessee SAR Industry Concentration", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "This section summarizes which filing industries contribute most to extracted Tennessee SAR filings "
            "in the latest year and which industries drove the largest changes over the study period.",
            styles["Body"],
        )
    )

    if not industry_summary.empty:
        display = industry_summary.head(8).copy()
        rows = [["Industry", "Latest Filings", "Latest Share", "Abs. Change", "Peak Year"]]

        for _, row in display.iterrows():
            rows.append(
                [
                    truncate_text(row.get("industry_name", ""), 32),
                    format_number(row.get("end_filings")),
                    format_pct(row.get("latest_year_share")),
                    format_number(row.get("absolute_change")),
                    format_year(row.get("peak_year")),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    2.4 * inch,
                    1.1 * inch,
                    1.0 * inch,
                    1.0 * inch,
                    0.8 * inch,
                ],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

    add_chart(story, CHARTS_DIR / "tennessee_sar_by_industry.png", styles)


def add_category_section(story, styles, top_categories: pd.DataFrame):
    """
    Add suspicious activity category section.
    """

    story.append(PageBreak())
    story.append(Paragraph("Suspicious Activity Category Intelligence", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "This section summarizes suspicious activity categories extracted from FinCEN industry exhibits. "
            "These categories provide financial-crime context for the SAR environment, including source-of-funds "
            "concerns, no apparent lawful purpose, suspicious EFT/wire transfers, transactions below CTR threshold, "
            "identity theft, elder financial exploitation, terrorist-organization-related activity, sanctions, "
            "corruption, and bribery.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "Read these categories as SAR-theme intelligence, not as Tennessee-specific suspicious activity "
            "category counts unless the source data explicitly supports that breakdown. Larger category counts "
            "indicate stronger national or industry-level reporting themes."
        ),
    )

    if not top_categories.empty:
        if "category_theme" in top_categories.columns:
            rows = [["Category", "Theme", "Latest Filings", "Risk Tier"]]

            for _, row in top_categories.head(10).iterrows():
                rows.append(
                    [
                        truncate_text(row.get("category", ""), 42),
                        truncate_text(row.get("category_theme", ""), 28),
                        format_number(row.get("end_filings")),
                        truncate_text(row.get("risk_tier", ""), 18),
                    ]
                )

            story.append(
                make_table(
                    rows,
                    col_widths=[
                        2.5 * inch,
                        1.7 * inch,
                        1.0 * inch,
                        1.1 * inch,
                    ],
                    font_size=6.5,
                )
            )
        else:
            rows = [["Category", "Latest Filings", "Growth", "High Risk"]]

            for _, row in top_categories.head(10).iterrows():
                rows.append(
                    [
                        truncate_text(row.get("category", ""), 55),
                        format_number(row.get("end_filings")),
                        format_pct(row.get("total_growth_pct")),
                        "Yes" if bool(row.get("high_risk_flag")) else "No",
                    ]
                )

            story.append(
                make_table(
                    rows,
                    col_widths=[
                        3.6 * inch,
                        1.1 * inch,
                        1.0 * inch,
                        0.8 * inch,
                    ],
                    font_size=7,
                )
            )

        story.append(Spacer(1, 0.2 * inch))

    add_chart(story, CHARTS_DIR / "top_suspicious_activity_categories.png", styles)

    story.append(
        Paragraph(
            "The following chart narrows the category context to high-risk suspicious activity themes. "
            "These are contextual category counts and should not be interpreted as Tennessee-specific SAR category totals.",
            styles["Small"],
        )
    )

    add_chart(story, CHARTS_DIR / "high_risk_suspicious_activity_categories.png", styles)


def add_pressure_index_section(
    story,
    styles,
    pressure_index: pd.DataFrame,
    components: pd.DataFrame,
):
    """
    Add SAR Pressure Index section.
    """

    story.append(PageBreak())
    story.append(Paragraph("Tennessee SAR Pressure Index", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "The Tennessee SAR Pressure Index is a composite score designed to summarize strategic SAR pressure "
            "using trend growth, recent momentum, national divergence, industry concentration, and high-risk "
            "category context. The index is not a prediction of criminal activity; it is an analytical signal "
            "for strategic monitoring and reporting pressure.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "Read the SAR Pressure Index as a structured reporting-pressure signal, not as a crime rate. "
            "The score combines SAR growth, recent momentum, national divergence, industry concentration, "
            "and high-risk SAR category context. Supporting law-enforcement and sanctions layers are excluded."
        ),
    )

    if not pressure_index.empty:
        row = pressure_index.iloc[0]
        story.append(
            Paragraph(
                f"Latest signal: <b>{row.get('signal', 'N/A')}</b> with an index score of "
                f"<b>{format_float(row.get('sar_pressure_index'), 2)} / 100</b> for "
                f"{row.get('latest_year', 'N/A')}.",
                styles["Body"],
            )
        )

        if "methodology_scope" in pressure_index.columns:
            story.append(
                Paragraph(
                    truncate_text(row.get("methodology_scope", ""), 500),
                    styles["Small"],
                )
            )

    if not components.empty:
        rows = [["Component", "Score", "Weight", "Weighted Score"]]

        for _, row in components.iterrows():
            rows.append(
                [
                    truncate_text(row.get("component", ""), 34),
                    format_float(row.get("score"), 2),
                    format_pct(row.get("weight")),
                    format_float(row.get("weighted_score"), 2),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    2.7 * inch,
                    0.9 * inch,
                    0.9 * inch,
                    1.2 * inch,
                ],
                font_size=7.2,
            )
        )


def add_change_detection_section(story, styles, change_flags: pd.DataFrame):
    """
    Add change detection section.
    """

    story.append(PageBreak())
    story.append(Paragraph("Change Detection", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "The change detection layer flags notable movements in Tennessee SAR trends, industry concentration, "
            "national divergence, the SAR Pressure Index, and supporting context-layer data-quality or interpretation signals.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "Read these rows as alerts for notable analytical movements or context signals. Severity reflects "
            "analytical importance within this project, not legal severity, confirmed criminal activity, or "
            "enforcement priority."
        ),
    )

    if not change_flags.empty:
        if "source_layer" in change_flags.columns:
            rows = [["Layer", "Severity", "Flag Type", "Description"]]

            for _, row in change_flags.head(14).iterrows():
                rows.append(
                    [
                        truncate_text(row.get("source_layer", ""), 24),
                        row.get("severity", ""),
                        truncate_text(row.get("flag_type", ""), 24),
                        truncate_text(row.get("description", ""), 125),
                    ]
                )

            story.append(
                make_table(
                    rows,
                    col_widths=[
                        1.2 * inch,
                        0.8 * inch,
                        1.4 * inch,
                        3.3 * inch,
                    ],
                    font_size=6.4,
                )
            )
        else:
            rows = [["Severity", "Flag Type", "Description"]]

            for _, row in change_flags.head(10).iterrows():
                rows.append(
                    [
                        row.get("severity", ""),
                        row.get("flag_type", ""),
                        truncate_text(row.get("description", ""), 150),
                    ]
                )

            story.append(
                make_table(
                    rows,
                    col_widths=[
                        0.9 * inch,
                        1.6 * inch,
                        4.2 * inch,
                    ],
                    font_size=7,
                )
            )


def add_scenario_sensitivity_section(
    story,
    styles,
    scenario_summary: pd.DataFrame,
    sensitivity: pd.DataFrame,
):
    """
    Add scenario and sensitivity analysis.
    """

    story.append(PageBreak())
    story.append(Paragraph("Scenario Analysis", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "Scenario analysis projects Tennessee SAR filings forward under transparent assumptions, including "
            "baseline continuation, recent momentum, national convergence, fraud/digital-payments acceleration, "
            "and a lower-growth monitoring case.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "Scenarios are assumption-based projections, not forecasts. They show how Tennessee SAR filings "
            "could evolve under different growth assumptions. Sensitivity analysis tests whether the SAR Pressure "
            "Index signal changes when component weights are adjusted."
        ),
    )

    if not scenario_summary.empty:
        rows = [["Scenario", "Growth Rate", "Projection Year", "Projected Filings", "Change"]]

        for _, row in scenario_summary.iterrows():
            rows.append(
                [
                    truncate_text(row.get("scenario", ""), 34),
                    format_pct(row.get("annual_growth_rate")),
                    format_year(row.get("projection_year")),
                    format_number(row.get("final_projected_sar_filings")),
                    format_number(row.get("final_projected_change_from_base")),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    2.3 * inch,
                    0.9 * inch,
                    1.0 * inch,
                    1.2 * inch,
                    1.0 * inch,
                ],
                font_size=6.8,
            )
        )
        story.append(Spacer(1, 0.2 * inch))

    add_chart(story, CHARTS_DIR / "tennessee_sar_scenario_projection.png", styles)

    story.append(Paragraph("Sensitivity Analysis", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "Sensitivity analysis tests whether the SAR Pressure Index remains stable under alternative component "
            "weighting assumptions.",
            styles["Body"],
        )
    )

    if not sensitivity.empty:
        rows = [["Weighting Scenario", "Index", "Signal", "Diff."]]

        for _, row in sensitivity.iterrows():
            rows.append(
                [
                    truncate_text(row.get("weighting_scenario", ""), 38),
                    format_float(row.get("sar_pressure_index"), 2),
                    truncate_text(row.get("signal", ""), 26),
                    format_float(row.get("difference_from_base"), 2),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    2.5 * inch,
                    0.8 * inch,
                    2.0 * inch,
                    0.8 * inch,
                ],
                font_size=6.8,
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        if "signal_stability_note" in sensitivity.columns:
            note = sensitivity["signal_stability_note"].dropna()
            if not note.empty:
                story.append(Paragraph(truncate_text(note.iloc[0], 500), styles["Small"]))

    add_chart(story, CHARTS_DIR / "sar_pressure_sensitivity.png", styles)


def add_law_enforcement_context_section(
    story,
    styles,
    tbi_summary: pd.DataFrame,
    fbi_summary: pd.DataFrame,
    tbi_cid_context: pd.DataFrame,
):
    """
    Add TBI and FBI law-enforcement context sections.
    """

    story.append(PageBreak())
    story.append(Paragraph("Law-Enforcement Context: TBI and FBI/NIBRS", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "The TBI and FBI layers provide law-enforcement reported offense context for financial-crime-adjacent "
            "themes. These counts are not SAR filings and are not used in the SAR Pressure Index. They help connect "
            "the SAR trend study to Tennessee and federal crime-data context.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "TBI and FBI/NIBRS counts are reported offense context, not SAR filings. Use this section to compare "
            "SAR themes with broader fraud, identity theft, exploitation, and financial-crime-adjacent offense patterns."
        ),
    )

    story.append(Paragraph("TBI CrimeInsight / TIBRS Context", styles["SubsectionHeader"]))

    if not tbi_summary.empty and "crime_category" in tbi_summary.columns:
        rows = [["Category", "Latest Year", "Reported Count", "Clearance Rate"]]

        for _, row in tbi_summary.head(10).iterrows():
            rows.append(
                [
                    truncate_text(row.get("crime_category", ""), 42),
                    format_year(row.get("latest_year")),
                    format_number(row.get("latest_reported_count")),
                    format_pct(row.get("clearance_rate")),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    3.0 * inch,
                    0.9 * inch,
                    1.2 * inch,
                    1.1 * inch,
                ],
                font_size=7,
            )
        )
        story.append(Spacer(1, 0.2 * inch))

    add_chart(story, CHARTS_DIR / "tbi_financial_crime_context.png", styles)

    if not tbi_cid_context.empty:
        story.append(Paragraph("TBI Criminal Investigation Division Context", styles["SubsectionHeader"]))

        rows = [["Theme", "Metric", "Value", "Interpretation"]]

        for _, row in tbi_cid_context.head(6).iterrows():
            rows.append(
                [
                    truncate_text(row.get("context_theme", ""), 26),
                    truncate_text(row.get("metric", ""), 24),
                    truncate_text(row.get("value", ""), 16),
                    truncate_text(row.get("interpretation", ""), 105),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    1.3 * inch,
                    1.2 * inch,
                    0.8 * inch,
                    3.2 * inch,
                ],
                font_size=6.4,
            )
        )
        story.append(Spacer(1, 0.2 * inch))
    else:
        story.append(
            Paragraph(
                "TBI Criminal Investigation Division context can be added as a narrative layer describing complex financial-crime, public-corruption, and investigative-assist capabilities.",
                styles["Small"],
            )
        )

    story.append(Paragraph("FBI Crime Data Explorer / NIBRS Context", styles["SubsectionHeader"]))

    if not fbi_summary.empty and "crime_category" in fbi_summary.columns:
        rows = [["Category", "Latest Year", "Reported Count", "Count Type"]]

        for _, row in fbi_summary.head(10).iterrows():
            rows.append(
                [
                    truncate_text(row.get("crime_category", ""), 42),
                    format_year(row.get("latest_year")),
                    format_number(row.get("latest_reported_count")),
                    truncate_text(row.get("count_type", ""), 18),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    3.0 * inch,
                    0.9 * inch,
                    1.2 * inch,
                    1.1 * inch,
                ],
                font_size=7,
            )
        )
        story.append(Spacer(1, 0.2 * inch))

    add_chart(story, CHARTS_DIR / "fbi_financial_crime_context.png", styles)


def add_elder_context_section(story, styles, elder_context: pd.DataFrame):
    """
    Add elder financial exploitation context section.
    """

    story.append(PageBreak())
    story.append(Paragraph("Elder Financial Exploitation Context", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "Elder financial exploitation is included as a supporting policy and risk-context layer because it "
            "overlaps with SAR themes such as identity theft, account takeover, suspicious EFT/wire activity, "
            "source-of-funds concerns, and fraud. This section uses the project's elder context table to connect "
            "SAR category intelligence with TBI and FBI law-enforcement context.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "This section connects elder exploitation to SAR themes and law-enforcement context. It should be read "
            "as victim-risk and policy context, not as a Tennessee-specific elder SAR count unless the source data "
            "explicitly supports that interpretation."
        ),
    )

    if not elder_context.empty:
        rows = [["Evidence Type", "Topic", "Metric", "Interpretation"]]

        for _, row in elder_context.head(8).iterrows():
            metric_value = row.get("metric_value", "")

            metric = (
                format_number(metric_value)
                if not pd.isna(metric_value)
                else row.get("metric_name", "Qualitative")
            )

            rows.append(
                [
                    truncate_text(row.get("evidence_type", ""), 28),
                    truncate_text(row.get("topic", ""), 28),
                    truncate_text(metric, 18),
                    truncate_text(row.get("interpretation", ""), 115),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    1.3 * inch,
                    1.3 * inch,
                    0.9 * inch,
                    3.1 * inch,
                ],
                font_size=6.4,
            )
        )
        story.append(Spacer(1, 0.2 * inch))

    add_chart(story, CHARTS_DIR / "elder_financial_exploitation_context.png", styles)


def add_comptroller_context_section(story, styles, comptroller_context: pd.DataFrame):
    """
    Add optional Comptroller public-sector fraud / audit context.
    """

    if comptroller_context.empty:
        return

    story.append(PageBreak())
    story.append(Paragraph("Comptroller Public-Sector Fraud and Audit Context", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "The Comptroller layer provides public-sector fraud, waste, abuse, and internal-control context. "
            "This is not SAR filing data, but it helps connect financial-intelligence themes to public-sector "
            "fraud reporting, audit findings, and referral pathways.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "Comptroller data reflects public-sector fraud, waste, abuse, allegation, hotline, and audit context. "
            "It is useful for oversight interpretation, but it is not SAR activity, confirmed fraud, charges, or convictions."
        ),
    )

    rows = [["Theme", "Metric", "Value", "Interpretation"]]

    for _, row in comptroller_context.head(8).iterrows():
        rows.append(
            [
                truncate_text(row.get("context_theme", ""), 28),
                truncate_text(row.get("metric", ""), 28),
                truncate_text(format_context_value(row.get("value", "")), 18),
                truncate_text(row.get("interpretation", ""), 115),
            ]
        )

    story.append(
        make_table(
            rows,
            col_widths=[
                1.3 * inch,
                1.4 * inch,
                0.8 * inch,
                3.1 * inch,
            ],
            font_size=6.4,
        )
    )

    add_chart(story, CHARTS_DIR / "comptroller_public_sector_fraud_context.png", styles)


def add_current_indicators_section(
    story,
    styles,
    current_indicators_context: pd.DataFrame,
):
    """
    Add Looking Forward / Current Indicators section.
    """

    if current_indicators_context.empty:
        return

    story.append(PageBreak())
    story.append(Paragraph("Looking Forward: 2025-2026 Current Indicators", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "The core SAR trend model remains anchored to the 2014-2024 FinCEN SAR Stats study period. "
            "This section adds newer current indicators as forward-looking context only. These indicators "
            "should not be interpreted as direct extensions of the SAR trend model or inputs to the SAR "
            "Pressure Index.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "Use this section as a looking-forward monitoring layer. These 2025-2026 indicators keep the report current, "
            "but they are not blended into the comparable 2014-2024 SAR trend model or SAR Pressure Index."
        ),
    )

    rows = [["Theme", "Indicator", "Period", "Data Type", "Interpretation"]]

    for _, row in current_indicators_context.head(8).iterrows():
        rows.append(
            [
                truncate_text(row.get("indicator_theme", ""), 24),
                truncate_text(row.get("indicator_name", ""), 28),
                truncate_text(row.get("indicator_period", ""), 18),
                truncate_text(row.get("data_type", ""), 28),
                truncate_text(row.get("interpretation", ""), 105),
            ]
        )

    story.append(
        make_table(
            rows,
            col_widths=[
                1.1 * inch,
                1.3 * inch,
                0.8 * inch,
                1.3 * inch,
                2.1 * inch,
            ],
            font_size=6.2,
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Methodology note: current indicators are used to keep the report timely while preserving "
            "the comparability of the core SAR analysis. Comparable 2025 or 2026 FinCEN state/industry "
            "SAR Stats data would be required before extending the SAR trend model beyond 2024.",
            styles["Small"],
        )
    )


def add_ofac_context_section(
    story,
    styles,
    ofac_summary: pd.DataFrame,
    ofac_matches: pd.DataFrame,
):
    """
    Add OFAC sanctions geography context section.
    """

    story.append(PageBreak())
    story.append(Paragraph("OFAC Sanctions Geography Context", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "The OFAC layer screens public OFAC sanctions-list address files for Tennessee-related geographic "
            "indicators. Accepted matches require explicit Tennessee, TN with clear U.S. country support, "
            "or a Tennessee city/county term with clear U.S. geography support. This is sanctions-screening "
            "geography context only; it does not indicate Tennessee SAR activity, confirmed local criminal "
            "activity, or Tennessee enforcement action.",
            styles["Body"],
        )
    )

    add_how_to_read_box(
        story,
        styles,
        text=(
            "OFAC screening is sanctions-geography context only. A match would not prove Tennessee SAR activity, "
            "local criminal activity, or enforcement action. In this report, the stricter geography validation found "
            "zero accepted Tennessee-related OFAC address matches."
        ),
    )

    if not ofac_summary.empty:
        rows = [["Metric", "Value", "Interpretation"]]

        for _, row in ofac_summary.head(10).iterrows():
            rows.append(
                [
                    truncate_text(row.get("metric", ""), 40),
                    format_number(row.get("value")),
                    truncate_text(row.get("interpretation", ""), 120),
                ]
            )

        story.append(
            make_table(
                rows,
                col_widths=[
                    2.1 * inch,
                    0.8 * inch,
                    3.7 * inch,
                ],
                font_size=6.7,
            )
        )
        story.append(Spacer(1, 0.2 * inch))

    ofac_chart_path = CHARTS_DIR / "ofac_tennessee_programs.png"

    if ofac_chart_path.exists():
        add_chart(story, ofac_chart_path, styles)
    else:
        story.append(
            Paragraph(
                "No OFAC program chart was generated because no accepted Tennessee-related OFAC program rows were available.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 0.1 * inch))

    if not ofac_matches.empty:
        story.append(Paragraph("Accepted Tennessee Address Match Preview", styles["SubsectionHeader"]))

        if "match_quality" in ofac_matches.columns:
            rows = [["List", "Name", "Program", "Match", "Quality", "Address / City-State"]]

            for _, row in ofac_matches.head(8).iterrows():
                address_text = f"{row.get('address', '')} {row.get('city_state_postal', '')}"

                rows.append(
                    [
                        truncate_text(row.get("list_type", ""), 12),
                        truncate_text(row.get("sdn_name", ""), 22),
                        truncate_text(row.get("program", ""), 17),
                        truncate_text(row.get("match_level", ""), 12),
                        truncate_text(row.get("match_quality", ""), 20),
                        truncate_text(address_text, 35),
                    ]
                )

            story.append(
                make_table(
                    rows,
                    col_widths=[
                        0.6 * inch,
                        1.2 * inch,
                        0.9 * inch,
                        0.7 * inch,
                        1.1 * inch,
                        2.0 * inch,
                    ],
                    font_size=5.8,
                )
            )
        elif "match_level" in ofac_matches.columns:
            rows = [["List", "Name", "Program", "Match", "Address / City-State"]]

            for _, row in ofac_matches.head(8).iterrows():
                address_text = f"{row.get('address', '')} {row.get('city_state_postal', '')}"

                rows.append(
                    [
                        truncate_text(row.get("list_type", ""), 14),
                        truncate_text(row.get("sdn_name", ""), 28),
                        truncate_text(row.get("program", ""), 20),
                        truncate_text(row.get("match_level", ""), 14),
                        truncate_text(address_text, 45),
                    ]
                )

            story.append(
                make_table(
                    rows,
                    col_widths=[
                        0.7 * inch,
                        1.5 * inch,
                        1.1 * inch,
                        0.8 * inch,
                        2.5 * inch,
                    ],
                    font_size=6.2,
                )
            )


def add_limitations_conclusion(story, styles):
    """
    Add limitations and conclusion section.
    """

    story.append(PageBreak())
    story.append(Paragraph("Limitations", styles["SectionHeader"]))

    limitations = [
        "The project uses public aggregated SAR Stats data, not raw SAR filings or SAR narratives.",
        "The analysis does not identify individual subjects, institutions, transactions, or investigations.",
        "Tennessee-specific SAR analysis is strongest for annual state and industry trend data.",
        "Suspicious activity category analysis is used as contextual intelligence and should not be interpreted as a Tennessee-specific category breakdown unless explicitly supported by the source data.",
        "SAR filing counts reflect reporting activity and monitoring behavior; they are not direct measures of confirmed financial crime.",
        "TBI and FBI/NIBRS data measure law-enforcement reported offense context, not SAR activity.",
        "TBI Criminal Investigation Division material is investigative-capability context, not a statewide offense-count dataset.",
        "Comptroller public-sector fraud and audit material is public-sector oversight context, not SAR activity.",
        "OFAC address matches are sanctions-screening geography context only and do not imply local criminal activity or enforcement action.",
        "Elder financial exploitation context is treated as a supporting policy and risk layer, not as a direct SAR Pressure Index input.",
        "Current indicators are forward-looking context only and should not be treated as direct extensions of the 2014-2024 SAR trend model.",
    ]

    for item in limitations:
        story.append(Paragraph(f"- {item}", styles["Finding"]))

    story.append(Paragraph("Conclusion", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "The Tennessee Financial Crime Intelligence Dashboard demonstrates how public SAR Stats data can be "
            "transformed into a structured financial intelligence product. The project identifies long-run SAR "
            "growth in Tennessee, high industry concentration in depository institution filings, relevant suspicious "
            "activity themes, a SAR Pressure Index signal, and scenario/sensitivity outputs that support disciplined "
            "interpretation. The supporting TBI, FBI, elder exploitation, Comptroller, OFAC, TBI CID, and current-indicator "
            "layers broaden the report into a multi-source AML, fraud, sanctions, public-sector fraud, exploitation, "
            "and financial intelligence study while preserving clear methodological boundaries.",
            styles["Body"],
        )
    )


def add_source_appendix(story, styles):
    """
    Add source appendix section with source references / URLs.
    """

    story.append(PageBreak())
    story.append(Paragraph("Source Appendix", styles["SectionHeader"]))

    story.append(
        Paragraph(
            "This appendix summarizes the public sources and data layers used in the Tennessee "
            "Financial Crime Intelligence Dashboard. The project relies on aggregated public data "
            "and contextual public-source materials only. It does not use raw SAR filings, SAR narratives, "
            "transaction-level data, subject-level information, or institution-specific confidential records.",
            styles["Body"],
        )
    )

    rows = [
        [
            "Source / Layer",
            "Source Reference / URL",
            "Primary Use in Project",
            "Notes / Limitations",
        ],
        [
            "FinCEN SAR Stats",
            "https://www.fincen.gov/resources/reports/sar-stats/sar-filings-industry",
            (
                "Core SAR filing trend data used for Tennessee-vs-U.S. SAR trends, "
                "industry concentration, suspicious activity category context, SAR Pressure Index, "
                "scenario analysis, sensitivity analysis, and change detection."
            ),
            (
                "Public aggregated SAR filing data. SAR filings measure reporting activity and monitoring "
                "behavior, not confirmed financial crime. Category exhibits are treated as context unless "
                "state-specific category detail is explicitly available."
            ),
        ],
        [
            "FinCEN SAR Stats filing-industry workbooks",
            "https://www.fincen.gov/reports/sar-stats",
            (
                "Source workbooks for Casino/Card Club, Depository Institution, Insurance Company, "
                "Money Services Business, Securities/Futures, Other, Loan or Finance Company, and "
                "Housing Government Sponsored Enterprise SAR filing trends."
            ),
            (
                "Exhibit 1 is used for U.S. total rows; Exhibit 2 is used for Tennessee state rows. "
                "Later exhibits support suspicious activity category context."
            ),
        ],
        [
            "TBI / TIBRS CrimeInsight",
            "https://www.tn.gov/tbi/divisions/cjis-division/tncrimeonline.html",
            (
                "Supporting law-enforcement context for fraud, identity theft, extortion, bribery, "
                "embezzlement, stolen property, and human-trafficking-adjacent indicators."
            ),
            (
                "Law-enforcement reported offense data is not SAR filing data and is not included in "
                "the SAR Pressure Index."
            ),
        ],
        [
            "TBI Crime in Tennessee publications",
            "https://www.tn.gov/tbi/divisions/cjis-division/recent-publications.html",
            (
                "Statewide crime-publication context and TIBRS background used to support the Tennessee "
                "law-enforcement context layer."
            ),
            (
                "Crime in Tennessee publications are supporting context only. They should not be interpreted "
                "as SAR data or transaction-level financial intelligence."
            ),
        ],
        [
            "FBI Crime Data Explorer / NIBRS",
            "https://cde.ucr.cjis.gov/",
            (
                "Federal law-enforcement context for Tennessee financial-crime-adjacent categories "
                "and human trafficking indicators."
            ),
            (
                "Reported offense context only. Not equivalent to SAR filings, confirmed convictions, "
                "or transaction-level illicit finance."
            ),
        ],
        [
            "FBI Crime Data API",
            "https://github.com/fbi-cde/crime-data-api",
            (
                "Fallback or supporting API reference for Crime Data Explorer / NIBRS offense data access."
            ),
            (
                "API outputs depend on available FBI-published data and should be interpreted as reported "
                "law-enforcement statistics, not confirmed financial-crime outcomes."
            ),
        ],
        [
            "Elder financial exploitation context",
            (
                "Project-derived context from SAR category analysis, TBI/FBI context, and public "
                "elder-exploitation policy framing."
            ),
            (
                "Policy, victim-risk, and SAR-theme context connecting elder exploitation with identity theft, "
                "fraud, account takeover, suspicious transfers, and exploitation-related financial crime."
            ),
            (
                "Interpretive context only. Not a direct Tennessee SAR category count unless explicitly supported "
                "by source data."
            ),
        ],
        [
            "Tennessee Comptroller fraud, waste, and abuse materials",
            "https://comptroller.tn.gov/office-functions/investigations/fraud-waste-and-abuse.html",
            (
                "Public-sector fraud, waste, abuse, hotline notification, allegation, audit, and internal-control "
                "context."
            ),
            (
                "Allegation/reporting and oversight context only. Not SAR activity, confirmed fraud, charges, "
                "or convictions."
            ),
        ],
        [
            "OFAC Sanctions List Service",
            "https://ofac.treasury.gov/sanctions-list-service",
            (
                "Sanctions-screening geography context used to identify accepted Tennessee-related address "
                "indicators in public OFAC files."
            ),
            (
                "OFAC address matches do not indicate Tennessee SAR activity, local criminal activity, or "
                "enforcement action. TN-only matches require clear U.S. support to avoid false positives."
            ),
        ],
        [
            "OFAC SDN List",
            "https://sanctionslist.ofac.treas.gov/Home/SdnList",
            (
                "Public SDN list address data used as one source for Tennessee-related sanctions geography screening."
            ),
            (
                "Sanctions-list geography screening is context only and should not be interpreted as local "
                "criminal activity or SAR activity."
            ),
        ],
        [
            "OFAC Consolidated Non-SDN List",
            "https://sanctionslist.ofac.treas.gov/Home/ConsolidatedList",
            (
                "Public consolidated non-SDN sanctions address data used as one source for Tennessee-related "
                "sanctions geography screening."
            ),
            (
                "Non-SDN sanctions-list address records are screened conservatively. Ambiguous geography is not "
                "accepted without clear U.S./Tennessee support."
            ),
        ],
        [
            "Current indicators / looking-forward context",
            (
                "Current public indicators from TBI, Comptroller, OFAC, and FinCEN release monitoring."
            ),
            (
                "2025-2026 current-context layer covering current TBI, Comptroller, OFAC, and FinCEN "
                "release-monitoring indicators."
            ),
            (
                "Forward-looking context only. Not blended into the comparable 2014-2024 SAR trend model "
                "or SAR Pressure Index."
            ),
        ],
        [
            "Project-generated outputs",
            "outputs/tables; outputs/charts; outputs/reports",
            (
                "Processed CSV tables, charts, methodology matrix, intelligence scorecard, scenario outputs, "
                "sensitivity outputs, and final PDF report."
            ),
            (
                "Generated outputs depend on public-source data extraction and transparent assumptions. "
                "They should be interpreted as analytical intelligence products, not official findings."
            ),
        ],
    ]

    story.append(
        make_table(
            rows,
            col_widths=[
                1.25 * inch,
                1.75 * inch,
                1.85 * inch,
                1.85 * inch,
            ],
            font_size=5.3,
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Suggested citation language: Tennessee Financial Crime Intelligence Dashboard, prepared by "
            "Jason Keen, using public FinCEN SAR Stats, TBI/TIBRS, FBI/NIBRS, Tennessee Comptroller, "
            "OFAC, and related public-source context materials.",
            styles["Small"],
        )
    )


def generate_pdf_report():
    """
    Generate the Tennessee Financial Crime Intelligence PDF report.
    """

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    styles = build_styles()
    data = load_report_inputs()

    doc = SimpleDocTemplate(
        str(REPORT_FILE),
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )

    story = []

    findings = read_key_findings(data["key_findings"])

    add_title_page(story, styles, data["sar_pressure_index"])
    add_key_findings(story, styles, findings)

    add_intelligence_scorecard_section(
        story,
        styles,
        data["intelligence_scorecard"],
    )

    add_methodology(story, styles)

    add_methodology_matrix_section(
        story,
        styles,
        data["methodology_matrix"],
    )

    add_trend_section(story, styles, data["trend_summary"])
    add_industry_section(story, styles, data["industry_summary"])
    add_category_section(story, styles, data["top_categories"])

    add_pressure_index_section(
        story,
        styles,
        data["sar_pressure_index"],
        data["sar_pressure_components"],
    )

    add_change_detection_section(story, styles, data["change_detection_flags"])

    add_scenario_sensitivity_section(
        story,
        styles,
        data["scenario_summary"],
        data["sensitivity"],
    )

    add_law_enforcement_context_section(
        story,
        styles,
        data["tbi_summary"],
        data["fbi_summary"],
        data["tbi_cid_context"],
    )

    add_elder_context_section(story, styles, data["elder_context"])

    add_comptroller_context_section(
        story,
        styles,
        data["comptroller_context"],
    )

    add_current_indicators_section(
        story,
        styles,
        data["current_indicators_context"],
    )

    add_ofac_context_section(
        story,
        styles,
        data["ofac_summary"],
        data["ofac_matches"],
    )

    add_limitations_conclusion(story, styles)
    add_source_appendix(story, styles)

    doc.build(story)

    print(f"PDF report created: {REPORT_FILE}")
    return REPORT_FILE