import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer

st.set_page_config(page_title="Emissions | European Energy Analytics", page_icon="🏭", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
countries = filters["selected_countries"]

st.title("🏭 Power Sector Air Emissions & Carbon Intensity")
st.caption("Official Eurostat Dataset: Air Emissions Accounts by NACE Rev. 2 Activity (env_ac_ainah_r2) | Sector D")

with analytics.engine.connect() as conn:
    stmt = text("""
        SELECT 
            c.country_name,
            c.iso2_code,
            d.year,
            e.emissions_tonnes_co2
        FROM fact_emissions e
        JOIN dim_date d ON e.date_id = d.date_id
        JOIN dim_country c ON e.country_id = c.country_id
        WHERE c.iso2_code IN :countries
        ORDER BY d.year ASC, c.country_name;
    """).bindparams(bindparam("countries", expanding=True))
    df_em = pd.read_sql(stmt, conn, params={"countries": list(countries)})

if not df_em.empty:
    st.subheader("Historical Greenhouse Gas Emissions by Country (Tonnes CO2eq)")
    fig_em = px.line(
        df_em, x="year", y="emissions_tonnes_co2", color="country_name",
        title="Power Sector Air Emissions Trajectory (Tonnes CO2eq)",
        markers=True
    )
    fig_em.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
    fig_em.update_yaxes(title_text="Tonnes CO2eq")
    st.plotly_chart(fig_em, use_container_width=True)

render_source_provenance_footer("env_ac_ainah_r2", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/env_ac_ainah_r2", "Annual Air Emissions Accounts")
