import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from database.db_manager import get_db_engine
from src.analytics.sql_queries import (
    SQL_OVERVIEW_KPIS,
    SQL_COUNTRY_ENERGY_MIX,
    SQL_HISTORICAL_GENERATION_BY_FUEL,
    SQL_COUNTRY_RENEWABLE_RANKING,
    SQL_GREECE_DEEP_DIVE,
    SQL_ELECTRICITY_PRICES,
    SQL_PER_CAPITA_METRICS
)

ALL_COUNTRIES = [
    "GR", "DE", "FR", "IT", "ES", "PT", "NL", "BE", "AT",
    "SE", "NO", "DK", "FI", "PL", "CZ", "IE"
]

class AnalyticsEngine:
    """SQL Analytics Backend Engine executing queries against PostgreSQL."""

    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()

    def get_available_years(self) -> List[int]:
        """Fetch list of available years in database."""
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT DISTINCT year FROM dim_date WHERE period_type = 'yearly' ORDER BY year ASC")).fetchall()
            return [r[0] for r in res] if res else [2023]

    def get_available_countries(self) -> List[Dict[str, str]]:
        """Fetch list of available countries."""
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT iso2_code, country_name FROM dim_country ORDER BY country_name")).fetchall()
            return [{"code": r[0], "name": r[1]} for r in res]

    def get_overview_kpis(self, year: int, countries: List[str] = None) -> Dict[str, Any]:
        """Get aggregate KPIs for selected year and countries."""
        country_list = countries or ALL_COUNTRIES
        with self.engine.connect() as conn:
            df = pd.read_sql(text(SQL_OVERVIEW_KPIS), conn, params={"target_year": year, "countries": tuple(country_list)})

        if df.empty:
            return {
                "year": year, "total_gen_gwh": 0.0, "ren_gen_gwh": 0.0,
                "fossil_gen_gwh": 0.0, "nuclear_gen_gwh": 0.0, "total_cons_gwh": 0.0,
                "renewable_share_pct": 0.0, "fossil_share_pct": 0.0, "nuclear_share_pct": 0.0
            }

        row = df.iloc[0]
        return {
            "year": int(row["year"]),
            "total_gen_gwh": float(row["total_gen"]),
            "ren_gen_gwh": float(row["ren_gen"]),
            "fossil_gen_gwh": float(row["fossil_gen"]),
            "nuclear_gen_gwh": float(row["nuclear_gen"]),
            "total_cons_gwh": float(row["total_cons"]),
            "renewable_share_pct": float(row["renewable_share_pct"]),
            "fossil_share_pct": float(row["fossil_share_pct"]),
            "nuclear_share_pct": float(row["nuclear_share_pct"])
        }

    def get_energy_mix(self, year: int, countries: List[str] = None) -> pd.DataFrame:
        """Fetch energy generation mix by fuel for a target year."""
        country_list = countries or ALL_COUNTRIES
        with self.engine.connect() as conn:
            df = pd.read_sql(text(SQL_COUNTRY_ENERGY_MIX), conn, params={"target_year": year, "countries": tuple(country_list)})
        return df

    def get_historical_generation(self, start_year: int, end_year: int, countries: List[str] = None) -> pd.DataFrame:
        """Fetch historical annual generation grouped by fuel source."""
        country_list = countries or ALL_COUNTRIES
        with self.engine.connect() as conn:
            df = pd.read_sql(text(SQL_HISTORICAL_GENERATION_BY_FUEL), conn, params={"start_year": start_year, "end_year": end_year, "countries": tuple(country_list)})
        return df

    def get_renewable_ranking(self, year: int) -> pd.DataFrame:
        """Fetch country ranking by renewable share and absolute renewable generation."""
        with self.engine.connect() as conn:
            df = pd.read_sql(text(SQL_COUNTRY_RENEWABLE_RANKING), conn, params={"target_year": year})
        return df

    def get_greece_analysis(self) -> pd.DataFrame:
        """Fetch historical time series for Greece."""
        with self.engine.connect() as conn:
            df = pd.read_sql(text(SQL_GREECE_DEEP_DIVE), conn)
        
        if not df.empty:
            df["renewable_share_pct"] = np.where(
                df["total_gwh"] > 0,
                (df["total_renewable_gwh"] / df["total_gwh"]) * 100.0,
                0.0
            )
            df["fossil_share_pct"] = np.where(
                df["total_gwh"] > 0,
                (df["fossil_gwh"] / df["total_gwh"]) * 100.0,
                0.0
            )
            # Calculate YoY for Greece renewable generation
            df["renewable_yoy_pct"] = df["total_renewable_gwh"].pct_change() * 100.0

        return df

    def get_electricity_prices(self, countries: List[str] = None) -> pd.DataFrame:
        """Fetch household & industrial electricity prices."""
        country_list = countries or ALL_COUNTRIES
        with self.engine.connect() as conn:
            df = pd.read_sql(text(SQL_ELECTRICITY_PRICES), conn, params={"countries": tuple(country_list)})
        return df

    def get_per_capita_metrics(self, year: int, countries: List[str] = None) -> pd.DataFrame:
        """Fetch per-capita generation and consumption metrics."""
        country_list = countries or ALL_COUNTRIES
        with self.engine.connect() as conn:
            df = pd.read_sql(text(SQL_PER_CAPITA_METRICS), conn, params={"target_year": year, "countries": tuple(country_list)})
        return df

    @staticmethod
    def calculate_cagr(start_val: float, end_val: float, years: int) -> Optional[float]:
        """Calculate Compound Annual Growth Rate (CAGR) deterministically."""
        if start_val <= 0 or end_val <= 0 or years <= 0:
            return None
        return ((end_val / start_val) ** (1.0 / years) - 1.0) * 100.0

    @staticmethod
    def calculate_yoy(previous_val: float, current_val: float) -> Optional[float]:
        """Calculate Year-over-Year (YoY) percentage change."""
        if previous_val == 0:
            return None
        return ((current_val / previous_val) - 1.0) * 100.0
