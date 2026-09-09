import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from src.forecasting.forecaster import Forecaster
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_source_provenance_footer
from dashboard.components.charts import create_forecast_chart

st.set_page_config(page_title="Forecasts | European Energy Analytics", page_icon="🔮", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]
countries = filters["selected_countries"]

st.title("🔮 Transparent Time-Series Energy Projections")

st.warning("⚠️ **NOTICE ON FORECAST DATA:** Numerical figures tagged as 'Forecast / Model Projection' are mathematical projections based on historical trend estimation. They DO NOT constitute official historical facts.")

stream_choice = st.selectbox("Select Energy Stream to Forecast", ["Renewables & Biofuels Total", "Solar Photovoltaic", "Wind Power", "Total Electricity Generation"])
horizon = st.slider("Forecast Horizon (Years)", min_value=1, max_value=10, value=5)

hist_df = analytics.get_historical_generation(2005, year, countries)

if not hist_df.empty:
    stream_df = hist_df[hist_df["source_name"] == stream_choice]
    
    if not stream_df.empty:
        agg_hist = stream_df.groupby("year")["generation_gwh"].sum().reset_index()
        fc_df, meta = Forecaster.forecast_linear(agg_hist, "year", "generation_gwh", horizon_years=horizon)

        if not fc_df.empty:
            st.subheader(f"Linear Trend Forecast: {stream_choice} (Through {int(agg_hist['year'].max()) + horizon})")
            
            fig = create_forecast_chart(fc_df, f"Historical Fact vs. Model Forecast — {stream_choice}")
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Model Type", meta["model_type"])
            with col2:
                st.metric("Annual Growth Slope", f"{meta['annual_growth_slope']:,.1f} GWh/yr")
            with col3:
                st.metric("R² Score", f"{meta['r2_score']:.3f}")
            with col4:
                st.metric("RMSE", f"{meta['rmse']:,.1f} GWh")

            st.markdown("### Projection Dataset Table")
            st.dataframe(fc_df, use_container_width=True)

render_source_provenance_footer("nrg_bal_c (OLS Linear Model)", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", "Historical OLS Extrapolation")
