import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from reports.generator import ExecutiveReportGenerator
from src.export.exporter import DataExporter
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer

st.set_page_config(page_title="Report Generator | European Energy Analytics", page_icon="📄", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]
countries = filters["selected_countries"]

st.title("📄 Executive Energy Report Generator")
st.markdown("Generate and export dynamically computed executive energy summary reports.")

report_gen = ExecutiveReportGenerator(analytics)

if st.button("🚀 Generate Executive Report Now"):
    report_md = report_gen.build_markdown_report(year, countries)
    
    st.markdown("---")
    st.markdown(report_md)

    st.markdown("### 📥 Download Options")
    st.download_button(
        label="Download Executive Report (.md)",
        data=report_md,
        file_name=f"European_Energy_Report_{year}.md",
        mime="text/markdown"
    )

    # Export filtered generation dataset as CSV
    hist_df = analytics.get_historical_generation(2010, year, countries)
    csv_bytes = DataExporter.export_to_csv(hist_df, {"Target Year": year, "Countries": countries})
    st.download_button(
        label="Download Raw Dataset (.csv)",
        data=csv_bytes,
        file_name=f"european_energy_data_{year}.csv",
        mime="text/csv"
    )

render_source_provenance_footer("Dynamic Analytics Engine", "https://ec.europa.eu/eurostat", f"{year}")
