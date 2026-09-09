import streamlit as st
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer
from dashboard.components.charts import create_stacked_area_chart, FUEL_COLOR_MAP

st.set_page_config(page_title="Energy Mix | European Energy Analytics", page_icon="🔋", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]
countries = filters["selected_countries"]

st.title(f"🔋 European Energy Mix Analysis ({year})")
st.markdown("Detailed fuel breakdown: Solar, Wind, Hydro, Nuclear, Coal, Gas, Oil Products.")

mix_df = analytics.get_energy_mix(year, countries)
hist_df = analytics.get_historical_generation(2010, year, countries)

if not mix_df.empty:
    st.subheader(f"Fuel Breakdown by Country ({year})")
    # Filter out TOTAL and Renewables Total to prevent double counting
    fuel_mix = mix_df[~mix_df["eurostat_code"].isin(["TOTAL", "RA000"])].copy()

    fig_bar = px.bar(
        fuel_mix, x="country_name", y="generation_gwh", color="source_name",
        title=f"Electricity Generation by Source and Country ({year})",
        color_discrete_map=FUEL_COLOR_MAP,
        barmode="stack"
    )
    fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
    fig_bar.update_yaxes(title_text="Generation (GWh)")
    st.plotly_chart(fig_bar, use_container_width=True)

if not hist_df.empty:
    st.subheader("Historical Energy Mix Composition")
    fuel_hist = hist_df[~hist_df["eurostat_code"].isin(["TOTAL", "RA000"])].copy()
    fig_area = create_stacked_area_chart(fuel_hist, "year", "generation_gwh", "source_name", "Historical Electricity Mix (2010 - Present)")
    st.plotly_chart(fig_area, use_container_width=True)

render_source_provenance_footer("nrg_bal_c", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", f"{year}")
