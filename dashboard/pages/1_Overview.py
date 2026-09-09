import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_kpi_card, render_source_provenance_footer
from dashboard.components.charts import create_stacked_area_chart, create_country_ranking_chart

st.set_page_config(page_title="Overview | European Energy Analytics", page_icon="📊", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]
countries = filters["selected_countries"]

st.title(f"📊 European Energy Overview ({year})")
st.caption("Latest Available Data: YYYY-MM / YYYY (Eurostat Verified Official Data)")

# Fetch KPIs
kpis = analytics.get_overview_kpis(year, countries)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    render_kpi_card("Total Generation", f"{kpis['total_gen_gwh']:,.0f} GWh", "Gross electricity production", color_accent="#6366f1")

with col2:
    render_kpi_card("Renewable Share", f"{kpis['renewable_share_pct']:.1f}%", f"{kpis['ren_gen_gwh']:,.0f} GWh renewable", color_accent="#10b981")

with col3:
    render_kpi_card("Fossil Share", f"{kpis['fossil_share_pct']:.1f}%", f"{kpis['fossil_gen_gwh']:,.0f} GWh fossil", color_accent="#ef4444")

with col4:
    render_kpi_card("Nuclear Share", f"{kpis['nuclear_share_pct']:.1f}%", f"{kpis['nuclear_gen_gwh']:,.0f} GWh nuclear", color_accent="#8b5cf6")

with col5:
    render_kpi_card("Total Consumption", f"{kpis['total_cons_gwh']:,.0f} GWh", "Final electricity consumption", color_accent="#06b6d4")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Historical Generation Trend by Fuel")
    hist_df = analytics.get_historical_generation(2010, year, countries)
    if not hist_df.empty:
        fig_area = create_stacked_area_chart(hist_df, "year", "generation_gwh", "source_name", "Regional Electricity Generation by Source (2010 - Present)")
        st.plotly_chart(fig_area, use_container_width=True)
    else:
        st.warning("No historical generation data available for selected criteria.")

with col_right:
    st.subheader("Renewable Energy Share Ranking")
    ranking_df = analytics.get_renewable_ranking(year)
    if not ranking_df.empty:
        fig_rank = create_country_ranking_chart(ranking_df.head(10), "country_name", "calculated_renewable_share_pct", f"Top 10 European Nations by Renewable Share ({year})", "% Renewable")
        st.plotly_chart(fig_rank, use_container_width=True)

render_source_provenance_footer("nrg_bal_c", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", f"{year}")
