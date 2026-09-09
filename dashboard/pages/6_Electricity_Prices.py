import streamlit as st
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer

st.set_page_config(page_title="Electricity Prices | European Energy Analytics", page_icon="💶", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
countries = filters["selected_countries"]

st.title("💶 European Electricity Prices")
st.caption("Official Eurostat Datasets: Household (nrg_pc_204) & Industrial (nrg_pc_205) | Prices in EUR/kWh")

price_df = analytics.get_electricity_prices(countries)

if not price_df.empty:
    hh_df = price_df[price_df["consumer_type"] == "household"]
    ind_df = price_df[price_df["consumer_type"] == "industrial"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Household Electricity Prices (€/kWh)")
        if not hh_df.empty:
            fig_hh = px.line(
                hh_df, x="period_code", y="price_eur_kwh", color="country_name",
                title="Household Electricity Price Trajectory (EUR/kWh)",
                markers=True
            )
            fig_hh.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
            fig_hh.update_yaxes(title_text="EUR / kWh")
            st.plotly_chart(fig_hh, use_container_width=True)

    with col2:
        st.subheader("Industrial Electricity Prices (€/kWh)")
        if not ind_df.empty:
            fig_ind = px.line(
                ind_df, x="period_code", y="price_eur_kwh", color="country_name",
                title="Industrial Electricity Price Trajectory (EUR/kWh)",
                markers=True
            )
            fig_ind.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
            fig_ind.update_yaxes(title_text="EUR / kWh")
            st.plotly_chart(fig_ind, use_container_width=True)

render_source_provenance_footer("nrg_pc_204 / nrg_pc_205", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_pc_204", "Biannual (2007-S1 - Present)")
