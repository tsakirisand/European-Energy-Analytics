import streamlit as st
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(
    page_title="European Energy Analytics Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stMetricValue {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ European Energy Analytics Platform")
st.markdown("### Official Production Data Engineering & Analytics System")
st.markdown("""
Welcome to **European Energy Analytics**, an end-to-end data engineering platform analyzing 100% REAL European energy data sourced directly from **Eurostat** official dissemination endpoints.

Use the left navigation bar to explore the 12 analytical pages:
- **1. Overview**: Region-wide energy snapshot, KPIs, renewable & fossil shares
- **2. Country Comparison**: Multi-country generation & energy mix comparisons (Greece vs. DE, FR, IT, ES, etc.)
- **3. Greece Analysis**: Dedicated deep dive into Greece's energy transition, solar/wind growth & mix
- **4. Energy Mix**: Complete fuel breakdown (Solar, Wind, Hydro, Nuclear, Coal, Gas, Oil)
- **5. Renewable Energy**: Country rankings by renewable share (%) and absolute GWh generation
- **6. Electricity Prices**: Household vs. Industrial price trends (€/kWh)
- **7. Consumption**: Total electricity consumption and per capita metrics (kWh/person)
- **8. Emissions**: Power-sector GHG emissions (Tonnes CO2eq) & carbon intensity
- **9. Trends**: Long-term YoY and CAGR historical growth rates
- **10. Forecasts**: Transparent time-series projections explicitly tagged as Forecast Models
- **11. Report Generator**: Dynamically generated executive summaries & exports
- **12. Data Sources**: Data dictionary, provenance metadata, API endpoints & licensing
""")

st.info("👈 Select a page from the sidebar navigation to view detailed analytics.")
