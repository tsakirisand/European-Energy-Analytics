import streamlit as st
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_kpi_card, render_source_provenance_footer

st.set_page_config(page_title="Single Country Deep Dive | European Energy Analytics", page_icon="🏳️", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]

available_countries = analytics.get_available_countries()
country_opts = [c["code"] for c in available_countries]
country_labels = {c["code"]: c["name"] for c in available_countries}

st.title("🏳️ Single Country Energy Transition Deep Dive")
st.markdown("Select any European nation below to inspect its dedicated historical generation streams, renewable expansion, and fuel trajectory.")

col_sel, _ = st.columns([1, 2])
with col_sel:
    selected_country_code = st.selectbox(
        "Select Country for Deep Dive",
        options=country_opts,
        index=country_opts.index("GR") if "GR" in country_opts else 0,
        format_func=lambda code: country_labels.get(code, code)
    )

country_name = country_labels.get(selected_country_code, selected_country_code)
st.caption(f"Official Data Sourced directly from Eurostat (`nrg_bal_c`, `nrg_cb_e`) | Target Country: **{country_name}** | Latest Available Year: 2024")

c_df = analytics.get_country_deep_dive(selected_country_code)

if not c_df.empty:
    latest_c = c_df[c_df["year"] == year]
    if latest_c.empty:
        latest_c = c_df.iloc[[-1]]
        actual_yr = int(latest_c["year"].values[0])
    else:
        actual_yr = year

    row = latest_c.iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card(f"{country_name} Total Gen", f"{row['total_gwh']:,.0f} GWh", f"Year {actual_yr}", color_accent="#3b82f6")
    with col2:
        render_kpi_card("Renewable Share", f"{row['renewable_share_pct']:.1f}%", f"{row['total_renewable_gwh']:,.0f} GWh", color_accent="#10b981")
    with col3:
        render_kpi_card("Solar PV Gen", f"{row['solar_gwh']:,.0f} GWh", "Photovoltaic generation", color_accent="#f59e0b")
    with col4:
        render_kpi_card("Wind Gen", f"{row['wind_gwh']:,.0f} GWh", "Onshore & Offshore wind", color_accent="#06b6d4")
    with col5:
        render_kpi_card("Hydro Gen", f"{row['hydro_gwh']:,.0f} GWh", "Hydroelectric plants", color_accent="#6366f1")

    st.markdown("---")
    st.subheader(f"Historical Trend of {country_name} Electricity Generation Breakdown")

    fig_c = px.line(
        c_df, x="year",
        y=["total_gwh", "total_renewable_gwh", "solar_gwh", "wind_gwh", "fossil_gwh"],
        title=f"{country_name} Historical Electricity Generation Trajectory (GWh)",
        markers=True,
        labels={"value": "Generation (GWh)", "variable": "Energy Stream"}
    )
    fig_c.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
    st.plotly_chart(fig_c, use_container_width=True)

    st.subheader(f"{country_name} Renewable Share Progression (%)")
    fig_pct = px.area(
        c_df, x="year", y="renewable_share_pct",
        title=f"{country_name} Official Renewable Share (% of Total Electricity Generation)",
        color_discrete_sequence=["#10b981"]
    )
    fig_pct.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
    fig_pct.update_yaxes(title_text="Renewable Share (%)")
    st.plotly_chart(fig_pct, use_container_width=True)
else:
    st.info(f"No detailed generation observations available for {country_name}.")

render_source_provenance_footer("nrg_bal_c", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", f"{year}")
