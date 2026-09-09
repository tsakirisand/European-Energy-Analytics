import streamlit as st
from typing import Dict, Any, List
from src.analytics.analytics_engine import AnalyticsEngine

def render_sidebar(analytics: AnalyticsEngine) -> Dict[str, Any]:
    """Render global sidebar filters and return user choices."""
    st.sidebar.markdown("### 🇪🇺 Filters & Settings")

    available_years = analytics.get_available_years()
    default_year = max(available_years) if available_years else 2024

    target_year = st.sidebar.selectbox(
        "Target Analysis Year",
        options=sorted(available_years, reverse=True),
        index=0 if default_year in available_years else 0
    )

    available_countries = analytics.get_available_countries()
    country_opts = [c["code"] for c in available_countries]
    country_labels = {c["code"]: c["name"] for c in available_countries}

    selected_countries = st.sidebar.multiselect(
        "Select Countries",
        options=country_opts,
        default=["GR", "DE", "FR", "IT", "ES"],
        format_func=lambda code: country_labels.get(code, code)
    )

    if not selected_countries:
        selected_countries = ["GR", "DE", "FR", "IT", "ES"]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Latest Available Data:** `{default_year}`")
    st.sidebar.markdown("**Source:** `Eurostat API`")

    return {
        "target_year": target_year,
        "selected_countries": selected_countries,
        "country_labels": country_labels
    }
