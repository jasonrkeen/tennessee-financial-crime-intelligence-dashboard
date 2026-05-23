from src.category_analysis import run_category_analysis
from src.change_detection import run_change_detection
from src.comptroller_context import run_comptroller_context_analysis
from src.config import END_YEAR, START_YEAR
from src.current_indicators import run_current_indicators_analysis
from src.elder_financial_exploitation import run_elder_financial_exploitation_analysis
from src.fbi_crime_data import run_fbi_crime_data_analysis
from src.intelligence_scorecard import run_intelligence_scorecard_analysis
from src.methodology_matrix import run_methodology_matrix_analysis
from src.ofac_context import run_ofac_context_analysis
from src.report_generator import generate_pdf_report
from src.risk_scoring import build_sar_pressure_index
from src.sar_loader import download_fincen_workbooks, inspect_workbooks
from src.sar_processing import run_sar_processing_pipeline
from src.scenario_analysis import run_scenario_analysis
from src.sensitivity_analysis import run_sensitivity_analysis
from src.tbi_context import run_tbi_context_analysis
from src.trend_analysis import run_trend_analysis
from src.visualization import (
    save_all_charts,
    save_comptroller_context_chart,
    save_elder_exploitation_chart,
    save_fbi_context_chart,
    save_high_risk_category_chart,
    save_ofac_context_chart,
    save_scenario_projection_chart,
    save_sensitivity_chart,
    save_tbi_context_chart,
    save_top_category_chart,
)


def print_dataframe_preview(title: str, df, rows: int = 15):
    """
    Print a consistent dataframe preview message.
    """

    print(f"\n{title}")

    if df is None or df.empty:
        print("No data created.")
    else:
        print(df.head(rows))


def main():
    print("=" * 80)
    print("Tennessee Financial Crime Intelligence Dashboard")
    print(
        "SAR trends, suspicious activity category intelligence, pressure index, "
        "scenario analysis, sensitivity analysis, TBI/TIBRS context, FBI/NIBRS context, "
        "elder financial exploitation context, Comptroller public-sector fraud context, "
        "OFAC sanctions geography context, current indicators, methodology matrix, "
        "financial crime intelligence scorecard, and integrated change detection"
    )
    print("=" * 80)

    print("\nStep 1: Downloading FinCEN SAR Stats workbooks...")
    download_fincen_workbooks(overwrite=False)

    print("\nStep 2: Inspecting workbook sheets...")
    inventory = inspect_workbooks()
    print_dataframe_preview("Workbook inventory preview:", inventory, rows=20)

    print("\nStep 3: Processing SAR workbook data...")
    results = run_sar_processing_pipeline()

    extracted = results["extracted"]
    industry_trend = results["industry_trend"]
    tn_vs_us_trend = results["tn_vs_us_trend"]

    print_dataframe_preview("Tennessee vs U.S. trend preview:", tn_vs_us_trend, rows=20)
    print_dataframe_preview("Industry trend preview:", industry_trend, rows=20)

    print("\nStep 4: Running trend intelligence analysis...")
    analysis_results = run_trend_analysis(
        tn_vs_us=tn_vs_us_trend,
        industry_trend=industry_trend,
    )

    trend_summary = analysis_results["trend_summary"]
    industry_summary = analysis_results["industry_summary"]

    print("\nKey findings:")
    for finding in analysis_results["key_findings"]:
        print(f"- {finding}")

    print("\nStep 5: Running suspicious activity category analysis...")
    category_results = run_category_analysis()

    category_summary = category_results["category_summary"]
    top_categories = category_results["top_categories"]
    high_risk_categories = category_results["high_risk_categories"]

    print_dataframe_preview("Top suspicious activity categories preview:", top_categories)
    print_dataframe_preview("High-risk suspicious activity categories preview:", high_risk_categories)

    print("\nStep 6: Building Tennessee SAR Pressure Index...")
    pressure_results = build_sar_pressure_index(
        tn_vs_us=tn_vs_us_trend,
        industry_summary=industry_summary,
        category_summary=category_summary,
    )

    sar_pressure_index = pressure_results["index"]
    sar_pressure_components = pressure_results["components"]

    print_dataframe_preview("SAR Pressure Index:", sar_pressure_index)
    print_dataframe_preview("SAR Pressure Components:", sar_pressure_components)

    print("\nStep 7: Running scenario analysis...")
    scenario_results = run_scenario_analysis(
        tn_vs_us=tn_vs_us_trend,
        projection_horizon=3,
    )

    scenario_projections = scenario_results["scenario_projections"]
    scenario_summary = scenario_results["scenario_summary"]

    print_dataframe_preview("Scenario Summary:", scenario_summary)

    print("\nStep 8: Running sensitivity analysis...")
    sensitivity_results = run_sensitivity_analysis(
        components=sar_pressure_components,
    )

    print_dataframe_preview("Sensitivity Analysis Results:", sensitivity_results)

    print("\nStep 9: Running TBI/TIBRS financial-crime context analysis...")
    tbi_results = run_tbi_context_analysis()

    tbi_summary = tbi_results["tbi_summary"]
    tbi_flags = tbi_results["tbi_flags"]

    print_dataframe_preview("TBI Context Flags:", tbi_flags)
    print_dataframe_preview("TBI Context Summary:", tbi_summary)

    print("\nStep 10: Running FBI Crime Data Explorer / NIBRS context analysis...")
    fbi_results = run_fbi_crime_data_analysis(
        state_abbr="TN",
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    fbi_summary = fbi_results["fbi_summary"]
    fbi_flags = fbi_results["fbi_flags"]

    print_dataframe_preview("FBI Context Flags:", fbi_flags)
    print_dataframe_preview("FBI Context Summary:", fbi_summary)

    print("\nStep 11: Running elder financial exploitation context analysis...")
    elder_results = run_elder_financial_exploitation_analysis()

    elder_context_summary = elder_results["elder_context_summary"]
    elder_context_flags = elder_results["elder_context_flags"]

    print_dataframe_preview("Elder Financial Exploitation Context Flags:", elder_context_flags)
    print_dataframe_preview("Elder Financial Exploitation Context Summary:", elder_context_summary)

    print("\nStep 12: Running Comptroller public-sector fraud context analysis...")
    comptroller_results = run_comptroller_context_analysis()

    comptroller_context = comptroller_results["comptroller_context"]
    comptroller_flags = comptroller_results["comptroller_flags"]

    print_dataframe_preview("Comptroller Context Flags:", comptroller_flags)
    print_dataframe_preview("Comptroller Context Summary:", comptroller_context)

    print("\nStep 13: Running OFAC sanctions geography context analysis...")
    ofac_results = run_ofac_context_analysis()

    ofac_summary = ofac_results["ofac_summary"]
    ofac_flags = ofac_results["ofac_flags"]
    ofac_matches = ofac_results["ofac_matches"]

    print_dataframe_preview("OFAC Context Flags:", ofac_flags)
    print_dataframe_preview("OFAC Context Summary:", ofac_summary)
    print_dataframe_preview("OFAC Tennessee Address Matches Preview:", ofac_matches, rows=20)

    print("\nStep 14: Running current indicators / looking-forward context analysis...")
    current_indicator_results = run_current_indicators_analysis()

    current_indicators_context = current_indicator_results["current_indicators_context"]
    current_indicators_flags = current_indicator_results["current_indicators_flags"]

    print_dataframe_preview("Current Indicators Flags:", current_indicators_flags)
    print_dataframe_preview("Current Indicators Context:", current_indicators_context)

    print("\nStep 15: Building methodology matrix...")
    methodology_results = run_methodology_matrix_analysis()
    methodology_matrix = methodology_results["methodology_matrix"]

    print_dataframe_preview("Methodology Matrix:", methodology_matrix)

    print("\nStep 16: Building financial crime intelligence scorecard...")
    scorecard_results = run_intelligence_scorecard_analysis(
        sar_pressure_index=sar_pressure_index,
        sar_pressure_components=sar_pressure_components,
        trend_summary=trend_summary,
        industry_summary=industry_summary,
        tbi_summary=tbi_summary,
        fbi_summary=fbi_summary,
        comptroller_context=comptroller_context,
        ofac_summary=ofac_summary,
        current_indicators_context=current_indicators_context,
    )

    intelligence_scorecard = scorecard_results["intelligence_scorecard"]

    print_dataframe_preview(
        "Financial Crime Intelligence Scorecard:",
        intelligence_scorecard,
    )

    print("\nStep 17: Running integrated change detection...")
    change_detection_results = run_change_detection(
        tn_vs_us=tn_vs_us_trend,
        industry_trend=industry_trend,
        sar_pressure_index=sar_pressure_index,
        tbi_summary=tbi_summary,
        fbi_summary=fbi_summary,
        elder_context_summary=elder_context_summary,
        ofac_summary=ofac_summary,
        comptroller_context=comptroller_context,
    )

    change_flags = change_detection_results["flags"]
    change_summary = change_detection_results["summary"]

    print_dataframe_preview("Integrated Change Detection Flags:", change_flags, rows=25)
    print_dataframe_preview("Integrated Change Detection Summary:", change_summary)

    print("\nStep 18: Saving charts...")
    save_all_charts(tn_vs_us_trend, industry_trend)
    save_top_category_chart(category_summary)
    save_high_risk_category_chart(category_summary)
    save_scenario_projection_chart(
        tn_vs_us=tn_vs_us_trend,
        scenario_projections=scenario_projections,
    )
    save_sensitivity_chart(sensitivity_results)
    save_tbi_context_chart(tbi_summary)
    save_fbi_context_chart(fbi_summary)
    save_elder_exploitation_chart(elder_context_summary)
    save_comptroller_context_chart(comptroller_context)
    save_ofac_context_chart(ofac_summary)

    print("\nStep 19: Generating PDF report...")
    generate_pdf_report()

    print("\nPipeline complete.")
    print("Check these folders:")
    print("- data/raw")
    print("- data/processed")
    print("- outputs/charts")
    print("- outputs/tables")
    print("- outputs/reports")


if __name__ == "__main__":
    main()