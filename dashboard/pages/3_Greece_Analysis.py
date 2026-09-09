import streamlit as st
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_kpi_card, render_source_provenance_footer

st.set_page_config(page_title="Greece Analysis | European Energy Analytics", page_icon="🇬🇷", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]

st.title("🇬🇷 Greece Dedicated Energy Transition Analysis")
st.caption("Official Data Sourced directly from Eurostat (`nrg_bal_c`, `nrg_cb_e`) | Latest Available Year: 2024")

gr_df = analytics.get_greece_analysis()

if not gr_df.empty:
    latest_gr = gr_df[gr_df["year"] == year]
    if latest_gr.empty:
        latest_gr = gr_df.iloc[[-1]]
        actual_yr = int(latest_gr["year"].values[0])
    else:
        actual_yr = year

    row = latest_gr.iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card("Greek Total Gen", f"{row['total_gwh']:,.0f} GWh", f"Year {actual_yr}", color_accent="#3b82f6")
    with col2:
        render_kpi_card("Renewable Share", f"{row['renewable_share_pct']:.1f}%", f"{row['total_renewable_gwh']:,.0f} GWh", color_accent="#10b981")
    with col3:
        render_kpi_card("Solar PV Gen", f"{row['solar_gwh']:,.0f} GWh", "Photovoltaic generation", color_accent="#f59e0b")
    with col4:
        render_kpi_card("Wind Gen", f"{row['wind_gwh']:,.0f} GWh", "Onshore & Offshore wind", color_accent="#06b6d4")
    with col5:
        render_kpi_card("Hydro Gen", f"{row['hydro_gwh']:,.0f} GWh", "Hydroelectric plants", color_accent="#6366f1")

    st.markdown("---")
    st.subheader("Historical Trend of Greek Electricity Generation Breakdown")

    fig_gr = px.line(
        gr_df, x="year",
        y=["total_gwh", "total_renewable_gwh", "solar_gwh", "wind_gwh", "fossil_gwh"],
        title="Greece Historical Electricity Generation Trajectory (GWh)",
        markers=True,
        labels={"value": "Generation (GWh)", "variable": "Energy Stream"}
    )
    fig_gr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
    st.plotly_chart(fig_gr, use_container_width=True)

    st.subheader("Greek Renewable Share Progression (%)")
    fig_pct = px.area(
        gr_df, x="year", y="renewable_share_pct",
        title="Greece Official Renewable Share (% of Total Electricity Generation)",
        color_discrete_sequence=["#10b981"]
    )
    fig_pct.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
    fig_pct.update_yaxes(title_text="Renewable Share (%)")
    st.plotly_chart(fig_pct, use_container_width=True)

render_source_provenance_footer("nrg_bal_c", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", f"{year}")
