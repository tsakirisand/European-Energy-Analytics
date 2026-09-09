import streamlit as st
from typing import Dict, Any, List
from src.analytics.analytics_engine import AnalyticsEngine, ALL_COUNTRIES

def render_sidebar(analytics: AnalyticsEngine) -> Dict[str, Any]:
    """Render global sidebar filters and return user choices."""
    st.sidebar.markdown("### 🇪🇺 Filters & Settings")

    available_years = analytics.get_available_years()
    if not available_years:
        available_years = [2024, 2023, 2022, 2021, 2020]

    default_year = 2024 if 2024 in available_years else max(available_years)

    target_year = st.sidebar.selectbox(
        "Target Analysis Year",
        options=sorted(available_years, reverse=True),
        index=sorted(available_years, reverse=True).index(default_year) if default_year in available_years else 0
    )

    available_countries = analytics.get_available_countries()
    if not available_countries:
        country_opts = ALL_COUNTRIES
        country_labels = {c: c for c in ALL_COUNTRIES}
    else:
        country_opts = [c["code"] for c in available_countries]
        country_labels = {c["code"]: c["name"] for c in available_countries}

    default_candidates = ["GR", "DE", "FR", "IT", "ES"]
    valid_defaults = [c for c in default_candidates if c in country_opts]
    if not valid_defaults and country_opts:
        valid_defaults = country_opts[:5]

    selected_countries = st.sidebar.multiselect(
        "Select Countries",
        options=country_opts,
        default=valid_defaults,
        format_func=lambda code: country_labels.get(code, code)
    )

    if not selected_countries:
        selected_countries = valid_defaults or country_opts[:5]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Target Analysis Year:** `{target_year}`")
    st.sidebar.markdown("**Source:** `Eurostat Official API`")

    return {
        "target_year": target_year,
        "selected_countries": selected_countries,
        "country_labels": country_labels
    }
