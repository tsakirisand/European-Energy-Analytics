import streamlit as st
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer
from dashboard.components.charts import create_country_ranking_chart

st.set_page_config(page_title="Renewable Energy | European Energy Analytics", page_icon="🌱", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]

st.title(f"🌱 Renewable Energy & Transition Rankings ({year})")

ren_df = analytics.get_renewable_ranking(year)

if not ren_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ranking by Renewable Share (%)")
        fig1 = create_country_ranking_chart(ren_df, "country_name", "calculated_renewable_share_pct", f"Renewable Share of Generation ({year})", "% Renewable")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Ranking by Absolute Renewable Generation (GWh)")
        fig2 = create_country_ranking_chart(ren_df, "country_name", "renewable_gwh", f"Absolute Renewable Generation ({year})", "GWh")
        st.plotly_chart(fig2, use_container_width=True)

render_source_provenance_footer("nrg_ind_ren", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_ind_ren", f"{year}")
