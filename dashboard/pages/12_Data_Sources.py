import streamlit as st
import sys
import os
import pandas as pd
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar

st.set_page_config(page_title="Data Sources | European Energy Analytics", page_icon="📚", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)

st.title("📚 Official Data Sources & Methodology Register")
st.markdown("Complete data provenance, dataset endpoints, update frequencies, and legal licensing information.")

with analytics.engine.connect() as conn:
    prov_df = pd.read_sql(text("SELECT * FROM metadata_data_provenance"), conn)

if not prov_df.empty:
    st.subheader("Data Provenance Registry Table")
    st.dataframe(prov_df, use_container_width=True)

st.markdown("""
### 1. Eurostat Official API Dissemination
- **Official Provider:** Statistical Office of the European Union (Eurostat)
- **API Base Endpoint:** `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/`
- **Licensing:** Eurostat data is free and open to re-use under the [Eurostat Copyright Notice](https://ec.europa.eu/eurostat/web/main/help/copyright-notice), subject to acknowledgment of the source.

### 2. Core Sourced Datasets:
1. `nrg_bal_c`: Complete Annual Energy Balances (Gross Electricity Production `GEP` by SIEC fuel source in GWh).
2. `nrg_cb_e`: Annual Electricity Supply, Transformation, and Consumption (`FC` in GWh).
3. `nrg_cb_em`: Monthly Electricity Balance and Supply (GWh).
4. `nrg_ind_ren`: Shares of energy from renewable sources (% `REN_ELC`).
5. `nrg_pc_204`: Electricity prices for household consumers (EUR/kWh, bi-annual).
6. `nrg_pc_205`: Electricity prices for non-household / industrial consumers (EUR/kWh, bi-annual).
7. `env_ac_ainah_r2`: Greenhouse gas emissions for Electricity supply sector D (Thousand Tonnes CO2eq).
8. `demo_pjan`: Official Population on 1 January (Count).

### 3. Data Integrity & Validation Rules:
- **No Synthetic Fallback:** All factual metrics originate from Eurostat REST API endpoints.
- **Weighted Aggregation:** Regional renewable percentages are strictly derived via `sum(renewable_gwh) / sum(total_gwh) * 100` to avoid statistical distortion from averaging percentages.
""")
