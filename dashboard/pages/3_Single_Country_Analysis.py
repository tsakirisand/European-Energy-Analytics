import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.analytics.analytics_engine import AnalyticsEngine
from dashboard.components.sidebar import render_sidebar
from dashboard.components.cards import render_kpi_card, render_source_provenance_footer

st.set_page_config(page_title="Single Country Deep Dive | European Energy Analytics", page_icon="🏳️", layout="wide")

analytics = AnalyticsEngine()
filters = render_sidebar(analytics)
year = filters["target_year"]

COUNTRY_FLAGS = {
    "AL": "🇦🇱", "AT": "🇦🇹", "BE": "🇧🇪", "BA": "🇧🇦", "BG": "🇧🇬",
    "HR": "🇭🇷", "CY": "🇨🇾", "CZ": "🇨🇿", "DK": "🇩🇰", "EE": "🇪🇪",
    "FI": "🇫🇮", "FR": "🇫🇷", "DE": "🇩🇪", "GR": "🇬🇷", "HU": "🇭🇺",
    "IS": "🇮🇸", "IE": "🇮🇪", "IT": "🇮🇹", "LV": "🇱🇻", "LT": "🇱🇹",
    "LU": "🇱🇺", "MT": "🇲🇹", "ME": "🇲🇪", "NL": "🇳🇱", "MK": "🇲🇰",
    "NO": "🇳🇴", "PL": "🇵🇱", "PT": "🇵🇹", "RO": "🇷🇴", "SK": "🇸🇰",
    "SI": "🇸🇮", "ES": "🇪🇸", "SE": "🇸🇪", "CH": "🇨🇭", "UK": "🇬🇧",
    "RS": "🇷🇸"
}

available_countries = analytics.get_available_countries()
country_opts = [c["code"] for c in available_countries]
country_labels = {c["code"]: f"{COUNTRY_FLAGS.get(c['code'], '🏳️')} {c['name']}" for c in available_countries}
code_to_name = {c["code"]: c["name"] for c in available_countries}

st.title("🏳️ Single Country Energy Transition Deep Dive")
st.markdown("Inspect comprehensive energy balance streams, structural fuel shifts, retail electricity price trajectories, and power sector air emissions for any European nation.")

col_sel, _ = st.columns([1, 2])
with col_sel:
    selected_country_code = st.selectbox(
        "Select Target European Country",
        options=country_opts,
        index=country_opts.index("GR") if "GR" in country_opts else 0,
        format_func=lambda code: country_labels.get(code, code)
    )

country_name = code_to_name.get(selected_country_code, selected_country_code)
flag_emoji = COUNTRY_FLAGS.get(selected_country_code, "🏳️")

st.caption(f"Official Data Sourced directly from Eurostat (`nrg_bal_c`, `nrg_cb_e`, `nrg_pc_204`, `env_ac_ainah_r2`, `demo_pjan`) | Target Nation: **{flag_emoji} {country_name}** | Focus Year: **{year}**")

c_df = analytics.get_country_deep_dive(selected_country_code)
fuel_df = analytics.get_country_fuel_breakdown(selected_country_code, year)
price_df = analytics.get_country_price_history(selected_country_code)
em_df = analytics.get_country_emissions_history(selected_country_code)

if not c_df.empty:
    latest_c = c_df[c_df["year"] == year]
    if latest_c.empty:
        latest_c = c_df.iloc[[-1]]
        actual_yr = int(latest_c["year"].values[0])
    else:
        actual_yr = year

    row = latest_c.iloc[0]
    tot_gwh = row["total_gwh"]
    ren_share = row["renewable_share_pct"]
    ren_gwh = row["total_renewable_gwh"]
    fossil_gwh = row["fossil_gwh"]
    fossil_share = row["fossil_share_pct"]
    nuclear_gwh = row.get("nuclear_gwh", 0.0)
    nuclear_share = row.get("nuclear_share_pct", 0.0)
    solar_gwh = row["solar_gwh"]
    wind_gwh = row["wind_gwh"]
    hydro_gwh = row["hydro_gwh"]

    # 10-year historical delta
    past_10_row = c_df[c_df["year"] == (actual_yr - 10)]
    past_10_str = ""
    if not past_10_row.empty:
        past_ren_pct = past_10_row.iloc[0]["renewable_share_pct"]
        ren_diff = ren_share - past_ren_pct
        past_10_str = f" Over the decade from {actual_yr - 10} to {actual_yr}, {country_name}'s renewable share shifted by **{ren_diff:+.1f}%** percentage points (from {past_ren_pct:.1f}% to {ren_share:.1f}%)."

    # Price summary metrics
    hh_price_str = "N/A"
    ind_price_str = "N/A"
    if not price_df.empty:
        hh_prices = price_df[price_df["consumer_type"].str.lower() == "household"]
        if not hh_prices.empty:
            hh_price_str = f"€{hh_prices.iloc[-1]['price_eur_kwh']:.4f}/kWh"
        ind_prices = price_df[price_df["consumer_type"].str.lower() == "industrial"]
        if not ind_prices.empty:
            ind_price_str = f"€{ind_prices.iloc[-1]['price_eur_kwh']:.4f}/kWh"

    # Emissions summary metrics
    em_str = "N/A"
    if not em_df.empty:
        latest_em = em_df.iloc[-1]
        em_str = f"{latest_em['emissions_tonnes_co2'] / 1e6:,.2f} Mt CO₂eq"

    # Executive Intelligence Callout Box
    st.info(
        f"### {flag_emoji} {country_name} Energy Profile & Executive Narrative ({actual_yr})\n"
        f"In **{actual_yr}**, **{country_name}** recorded a total electricity generation of **{tot_gwh:,.0f} GWh**. "
        f"Clean renewable power streams generated **{ren_gwh:,.0f} GWh**, accounting for **{ren_share:.1f}%** of national electricity output. "
        f"Fossil thermal generation stood at **{fossil_gwh:,.0f} GWh ({fossil_share:.1f}%)**, while nuclear energy supplied **{nuclear_gwh:,.0f} GWh ({nuclear_share:.1f}%)**."
        f"{past_10_str} "
        f"Retail power tariffs were recorded at **{hh_price_str}** for households and **{ind_price_str}** for industry, with total power sector GHG emissions standing at **{em_str}**."
    )

    st.markdown("---")

    # 6 Metric KPI Cards
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        render_kpi_card("Total Generation", f"{tot_gwh:,.0f} GWh", f"Year {actual_yr}", color_accent="#3b82f6")
    with k2:
        render_kpi_card("Renewable Share", f"{ren_share:.1f}%", f"{ren_gwh:,.0f} GWh", color_accent="#10b981")
    with k3:
        render_kpi_card("Fossil Share", f"{fossil_share:.1f}%", f"{fossil_gwh:,.0f} GWh", color_accent="#ef4444")
    with k4:
        render_kpi_card("Nuclear Share", f"{nuclear_share:.1f}%", f"{nuclear_gwh:,.0f} GWh", color_accent="#8b5cf6")
    with k5:
        render_kpi_card("Household Price", hh_price_str, "Eurostat Band DC", color_accent="#f59e0b")
    with k6:
        render_kpi_card("Industrial Price", ind_price_str, "Eurostat Band ID", color_accent="#06b6d4")

    st.markdown("---")

    # Tabbed Analytical Deep Dive
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Energy Mix & Fuel Breakdown",
        "📈 Historical Trajectory (1990-2024)",
        "💶 Electricity Price Evolution",
        "🌍 Air Emissions & Carbon Intensity",
        "⚡ Per Capita & Growth Benchmarks"
    ])

    # TAB 1: Fuel Breakdown
    with tab1:
        st.subheader(f"{flag_emoji} {country_name} Fuel Breakdown ({actual_yr})")
        if not fuel_df.empty:
            c1, c2 = st.columns([1, 1])
            with c1:
                fig_pie = px.pie(
                    fuel_df, values="generation_gwh", names="source_name",
                    title=f"{country_name} Generation Breakdown by Fuel ({actual_yr})",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                st.markdown(f"#### Fuel Stream Generation Breakdown (GWh)")
                fuel_df["share_pct"] = np.where(tot_gwh > 0, (fuel_df["generation_gwh"] / tot_gwh) * 100.0, 0.0)
                display_fuel = fuel_df[["source_name", "fuel_group", "generation_gwh", "share_pct"]].rename(columns={
                    "source_name": "Fuel Stream",
                    "fuel_group": "Group",
                    "generation_gwh": "Generation (GWh)",
                    "share_pct": "% Share"
                })
                st.dataframe(
                    display_fuel.style.format({
                        "Generation (GWh)": "{:,.1f}",
                        "% Share": "{:.2f}%"
                    }),
                    use_container_width=True
                )
        else:
            st.info(f"No fuel breakdown observations recorded for {country_name} in {actual_yr}.")

    # TAB 2: Historical Trajectory
    with tab2:
        st.subheader(f"{flag_emoji} {country_name} 35-Year Generation Trajectory (1990 - {actual_yr})")
        
        fig_hist = px.line(
            c_df, x="year",
            y=["total_gwh", "total_renewable_gwh", "fossil_gwh", "nuclear_gwh", "solar_gwh", "wind_gwh", "hydro_gwh"],
            title=f"{country_name} Electricity Generation by Stream (1990 - {actual_yr})",
            markers=True,
            labels={"value": "Generation (GWh)", "variable": "Energy Stream"}
        )
        fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
        st.plotly_chart(fig_hist, use_container_width=True)

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.markdown("#### Renewable vs Fossil vs Nuclear Share (%)")
            fig_shares = px.line(
                c_df, x="year",
                y=["renewable_share_pct", "fossil_share_pct", "nuclear_share_pct"],
                title=f"{country_name} Grid Composition Progression (%)",
                labels={"value": "Share (%)", "variable": "Category"},
                color_discrete_sequence=["#10b981", "#ef4444", "#8b5cf6"]
            )
            fig_shares.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
            st.plotly_chart(fig_shares, use_container_width=True)

        with col_h2:
            st.markdown("#### Solar PV & Wind Acceleration (GWh)")
            fig_sol_wind = px.bar(
                c_df, x="year", y=["solar_gwh", "wind_gwh"],
                title=f"{country_name} Solar & Wind Volume Expansion",
                labels={"value": "Generation (GWh)", "variable": "Technology"},
                barmode="stack",
                color_discrete_sequence=["#f59e0b", "#06b6d4"]
            )
            fig_sol_wind.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
            st.plotly_chart(fig_sol_wind, use_container_width=True)

    # TAB 3: Electricity Prices
    with tab3:
        st.subheader(f"{flag_emoji} {country_name} Electricity Price & Tariff Evolution")
        st.caption("Official Eurostat Biannual Price Statistics (`nrg_pc_204` / `nrg_pc_205`) including taxes and levies")

        if not price_df.empty:
            fig_price = px.line(
                price_df, x="period_code", y="price_eur_kwh", color="consumer_type",
                title=f"{country_name} Electricity Price History (EUR / kWh)",
                markers=True,
                labels={"price_eur_kwh": "EUR per kWh", "period_code": "Semester", "consumer_type": "Consumer Sector"},
                color_discrete_sequence=["#f59e0b", "#06b6d4"]
            )
            fig_price.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
            st.plotly_chart(fig_price, use_container_width=True)
        else:
            st.info(f"No biannual electricity price data available for {country_name}.")

    # TAB 4: Air Emissions
    with tab4:
        st.subheader(f"{flag_emoji} {country_name} Power Sector GHG Air Emissions")
        st.caption("Eurostat Air Emissions Accounts by NACE Rev. 2 Activity (`env_ac_ainah_r2`) - Sector D (Electricity, gas, steam and air conditioning supply)")

        if not em_df.empty:
            em_df["emissions_mt"] = em_df["emissions_tonnes_co2"] / 1e6
            fig_em = px.line(
                em_df, x="year", y="emissions_mt",
                title=f"{country_name} GHG Air Emissions Trajectory (Million Tonnes CO₂eq)",
                markers=True,
                color_discrete_sequence=["#ef4444"]
            )
            fig_em.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
            fig_em.update_yaxes(title_text="Million Tonnes CO₂eq")
            st.plotly_chart(fig_em, use_container_width=True)
        else:
            st.info(f"No greenhouse gas emissions observations recorded for {country_name}.")

    # TAB 5: Growth Benchmarks & CAGR
    with tab5:
        st.subheader(f"{flag_emoji} {country_name} Growth Benchmarks & Compound Annual Growth Rates")
        
        cagr_5y_ren = analytics.calculate_cagr(
            c_df[c_df["year"] == (actual_yr - 5)]["total_renewable_gwh"].values[0] if not c_df[c_df["year"] == (actual_yr - 5)].empty else 0,
            ren_gwh, 5
        )
        cagr_10y_ren = analytics.calculate_cagr(
            c_df[c_df["year"] == (actual_yr - 10)]["total_renewable_gwh"].values[0] if not c_df[c_df["year"] == (actual_yr - 10)].empty else 0,
            ren_gwh, 10
        )
        cagr_10y_solar = analytics.calculate_cagr(
            c_df[c_df["year"] == (actual_yr - 10)]["solar_gwh"].values[0] if not c_df[c_df["year"] == (actual_yr - 10)].empty else 0,
            solar_gwh, 10
        )
        cagr_10y_wind = analytics.calculate_cagr(
            c_df[c_df["year"] == (actual_yr - 10)]["wind_gwh"].values[0] if not c_df[c_df["year"] == (actual_yr - 10)].empty else 0,
            wind_gwh, 10
        )

        cagr_table = pd.DataFrame([
            {"Metric": "Renewables Total (5-Year CAGR)", "Rate": f"{cagr_5y_ren:.2f}%" if cagr_5y_ren else "N/A"},
            {"Metric": "Renewables Total (10-Year CAGR)", "Rate": f"{cagr_10y_ren:.2f}%" if cagr_10y_ren else "N/A"},
            {"Metric": "Solar Photovoltaic (10-Year CAGR)", "Rate": f"{cagr_10y_solar:.2f}%" if cagr_10y_solar else "N/A"},
            {"Metric": "Wind Power (10-Year CAGR)", "Rate": f"{cagr_10y_wind:.2f}%" if cagr_10y_wind else "N/A"},
        ])
        st.table(cagr_table)

else:
    st.info(f"No detailed generation observations available for {country_name}.")

render_source_provenance_footer("nrg_bal_c / nrg_pc_204 / env_ac_ainah_r2", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", f"{year}")
