import streamlit as st
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer

st.set_page_config(page_title="Country Comparison | European Energy Analytics", page_icon="⚔️", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]
countries = filters["selected_countries"]

st.title(f"⚔️ European Country Comparison ({year})")
st.markdown("Compare energy generation, renewable shares, and fuel mix across selected European nations (e.g. Greece vs. Germany, France, Italy, Spain).")

ranking_df = analytics.get_renewable_ranking(year)
if not ranking_df.empty:
    comp_df = ranking_df[ranking_df["iso2_code"].isin(countries)].copy()

    st.subheader("Selected Country KPI Comparison Table")
    st.dataframe(
        comp_df[["country_name", "iso2_code", "total_gwh", "renewable_gwh", "calculated_renewable_share_pct"]].rename(columns={
            "country_name": "Country",
            "iso2_code": "ISO Code",
            "total_gwh": "Total Generation (GWh)",
            "renewable_gwh": "Renewable Generation (GWh)",
            "calculated_renewable_share_pct": "Renewable Share (%)"
        }).style.format({
            "Total Generation (GWh)": "{:,.1f}",
            "Renewable Generation (GWh)": "{:,.1f}",
            "Renewable Share (%)": "{:.2f}%"
        }),
        use_container_width=True
    )

    col1, col2 = st.columns(2)
    with col1:
        fig_bar = px.bar(
            comp_df, x="country_name", y="calculated_renewable_share_pct",
            title=f"Renewable Share Comparison ({year})",
            color="calculated_renewable_share_pct",
            color_continuous_scale="emerald",
            text_auto=".1f"
        )
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
        fig_bar.update_yaxes(title_text="Renewable Share (%)")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        fig_tot = px.bar(
            comp_df, x="country_name", y="total_gwh",
            title=f"Total Electricity Generation Comparison ({year})",
            color="total_gwh",
            color_continuous_scale="Blues",
            text_auto=",.0f"
        )
        fig_tot.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
        fig_tot.update_yaxes(title_text="Generation (GWh)")
        st.plotly_chart(fig_tot, use_container_width=True)

render_source_provenance_footer("nrg_bal_c", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", f"{year}")
