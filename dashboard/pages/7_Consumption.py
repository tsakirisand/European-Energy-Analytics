import streamlit as st
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer

st.set_page_config(page_title="Consumption & Per Capita | European Energy Analytics", page_icon="📉", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]
countries = filters["selected_countries"]

st.title(f"📉 Electricity Consumption & Per Capita Metrics ({year})")

pop_df = analytics.get_per_capita_metrics(year, countries)

if not pop_df.empty:
    st.subheader(f"Per Capita Generation & Consumption ({year})")
    st.dataframe(
        pop_df[["country_name", "total_gen_gwh", "total_cons_gwh", "population_count", "gen_kwh_per_capita", "cons_kwh_per_capita"]].rename(columns={
            "country_name": "Country",
            "total_gen_gwh": "Total Generation (GWh)",
            "total_cons_gwh": "Total Consumption (GWh)",
            "population_count": "Population",
            "gen_kwh_per_capita": "Generation per Capita (kWh)",
            "cons_kwh_per_capita": "Consumption per Capita (kWh)"
        }).style.format({
            "Total Generation (GWh)": "{:,.1f}",
            "Total Consumption (GWh)": "{:,.1f}",
            "Population": "{:,.0f}",
            "Generation per Capita (kWh)": "{:,.0f}",
            "Consumption per Capita (kWh)": "{:,.0f}"
        }),
        use_container_width=True
    )

    col1, col2 = st.columns(2)
    with col1:
        fig_c1 = px.bar(
            pop_df, x="country_name", y="cons_kwh_per_capita",
            title=f"Consumption per Capita (kWh / Person) - {year}",
            color="cons_kwh_per_capita",
            color_continuous_scale="Cividis",
            text_auto=",.0f"
        )
        fig_c1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
        st.plotly_chart(fig_c1, use_container_width=True)

    with col2:
        fig_c2 = px.bar(
            pop_df, x="country_name", y="gen_kwh_per_capita",
            title=f"Generation per Capita (kWh / Person) - {year}",
            color="gen_kwh_per_capita",
            color_continuous_scale="Viridis",
            text_auto=",.0f"
        )
        fig_c2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
        st.plotly_chart(fig_c2, use_container_width=True)

render_source_provenance_footer("nrg_cb_e / demo_pjan", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjan", f"{year}")
