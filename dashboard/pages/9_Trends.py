import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer

st.set_page_config(page_title="Trends & CAGR | European Energy Analytics", page_icon="📈", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]
countries = filters["selected_countries"]

st.title("📈 Long-Term Growth Trends & CAGR Analysis")

hist_df = analytics.get_historical_generation(2005, year, countries)

if not hist_df.empty:
    st.subheader(f"Historical Generation Trajectory (2005 - {year})")
    fig_tr = px.line(
        hist_df, x="year", y="generation_gwh", color="source_name",
        title="Energy Stream Generation Trends (GWh)",
        markers=True
    )
    fig_tr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
    st.plotly_chart(fig_tr, use_container_width=True)

    # CAGR Calculation Table
    st.subheader("Compound Annual Growth Rate (CAGR) by Fuel Stream")
    years_diff = year - 2005
    if years_diff > 0:
        cagr_rows = []
        for src_name, group in hist_df.groupby("source_name"):
            val_2005 = group[group["year"] == 2005]["generation_gwh"].sum()
            val_latest = group[group["year"] == year]["generation_gwh"].sum()
            cagr = analytics.calculate_cagr(val_2005, val_latest, years_diff)
            cagr_rows.append({
                "Energy Source": src_name,
                f"2005 Generation (GWh)": val_2005,
                f"{year} Generation (GWh)": val_latest,
                "CAGR (%)": f"{cagr:.2f}%" if cagr is not None else "N/A"
            })
        
        st.dataframe(pd.DataFrame(cagr_rows), use_container_width=True)

render_source_provenance_footer("nrg_bal_c", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", f"2005 - {year}")
