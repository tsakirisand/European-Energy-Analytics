import pandas as pd
import numpy as np
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.engine import Engine
from database.db_manager import get_db_engine

COUNTRY_MAP = {
    "EL": {"iso2": "GR", "iso3": "GRC", "name": "Greece", "region": "Southern Europe", "is_eu": True},
    "GR": {"iso2": "GR", "iso3": "GRC", "name": "Greece", "region": "Southern Europe", "is_eu": True},
    "DE": {"iso2": "DE", "iso3": "DEU", "name": "Germany", "region": "Western Europe", "is_eu": True},
    "FR": {"iso2": "FR", "iso3": "FRA", "name": "France", "region": "Western Europe", "is_eu": True},
    "IT": {"iso2": "IT", "iso3": "ITA", "name": "Italy", "region": "Southern Europe", "is_eu": True},
    "ES": {"iso2": "ES", "iso3": "ESP", "name": "Spain", "region": "Southern Europe", "is_eu": True},
    "PT": {"iso2": "PT", "iso3": "PRT", "name": "Portugal", "region": "Southern Europe", "is_eu": True},
    "NL": {"iso2": "NL", "iso3": "NLD", "name": "Netherlands", "region": "Western Europe", "is_eu": True},
    "BE": {"iso2": "BE", "iso3": "BEL", "name": "Belgium", "region": "Western Europe", "is_eu": True},
    "AT": {"iso2": "AT", "iso3": "AUT", "name": "Austria", "region": "Central Europe", "is_eu": True},
    "SE": {"iso2": "SE", "iso3": "SWE", "name": "Sweden", "region": "Northern Europe", "is_eu": True},
    "NO": {"iso2": "NO", "iso3": "NOR", "name": "Norway", "region": "Northern Europe", "is_eu": False},
    "DK": {"iso2": "DK", "iso3": "DNK", "name": "Denmark", "region": "Northern Europe", "is_eu": True},
    "FI": {"iso2": "FI", "iso3": "FIN", "name": "Finland", "region": "Northern Europe", "is_eu": True},
    "PL": {"iso2": "PL", "iso3": "POL", "name": "Poland", "region": "Eastern Europe", "is_eu": True},
    "CZ": {"iso2": "CZ", "iso3": "CZE", "name": "Czechia", "region": "Central Europe", "is_eu": True},
    "IE": {"iso2": "IE", "iso3": "IRL", "name": "Ireland", "region": "Western Europe", "is_eu": True},
    "EU27_2020": {"iso2": "EU27", "iso3": "EU27", "name": "European Union (EU27)", "region": "Aggregate", "is_eu": False}
}

ENERGY_SOURCES = [
    {"eurostat_code": "TOTAL", "name": "Total Electricity Generation", "group": "total"},
    {"eurostat_code": "RA000", "name": "Renewables & Biofuels Total", "group": "renewable"},
    {"eurostat_code": "RA100", "name": "Hydro Power", "group": "renewable"},
    {"eurostat_code": "RA300", "name": "Wind Power", "group": "renewable"},
    {"eurostat_code": "RA420", "name": "Solar Photovoltaic", "group": "renewable"},
    {"eurostat_code": "RA410", "name": "Solar Thermal", "group": "renewable"},
    {"eurostat_code": "RA200", "name": "Geothermal Energy", "group": "renewable"},
    {"eurostat_code": "R5110-5150_W6000RI", "name": "Primary Solid Biofuels & Waste", "group": "renewable"},
    {"eurostat_code": "N900H", "name": "Nuclear Power", "group": "nuclear"},
    {"eurostat_code": "C0000X0350-0370", "name": "Solid Fossil Fuels (Coal)", "group": "fossil"},
    {"eurostat_code": "G3000", "name": "Natural Gas", "group": "fossil"},
    {"eurostat_code": "O4000XBIO", "name": "Oil & Petroleum Products", "group": "fossil"}
]

class Transformer:
    """Transform validated Eurostat DataFrames and insert into PostgreSQL dimension and fact tables."""

    def __init__(self, engine: Engine = None):
        self.engine = engine or get_db_engine()

    def populate_dimensions(self):
        """Populate dim_country, dim_energy_source, and dim_metric static dimensions."""
        with self.engine.begin() as conn:
            # 1. Countries
            for raw_code, info in COUNTRY_MAP.items():
                stmt = text("""
                    INSERT INTO dim_country (iso2_code, iso3_code, country_name, region, is_eu_member)
                    VALUES (:iso2, :iso3, :name, :region, :is_eu)
                    ON CONFLICT (iso2_code) DO UPDATE 
                    SET country_name = EXCLUDED.country_name, region = EXCLUDED.region;
                """)
                conn.execute(stmt, {"iso2": info["iso2"], "iso3": info["iso3"], "name": info["name"], "region": info["region"], "is_eu": info["is_eu"]})

            # 2. Energy Sources
            for src in ENERGY_SOURCES:
                stmt = text("""
                    INSERT INTO dim_energy_source (eurostat_code, source_name, fuel_group)
                    VALUES (:code, :name, :group)
                    ON CONFLICT (eurostat_code) DO UPDATE
                    SET source_name = EXCLUDED.source_name, fuel_group = EXCLUDED.fuel_group;
                """)
                conn.execute(stmt, {"code": src["eurostat_code"], "name": src["name"], "group": src["group"]})

            # 3. Metrics
            metrics = [
                ("GEP", "Gross Electricity Production", "GWh", "generation"),
                ("FC", "Final Electricity Consumption", "GWh", "consumption"),
                ("REN_ELC", "Renewable Share of Electricity", "%", "share"),
                ("PRICE_HH", "Household Electricity Price", "EUR/kWh", "price"),
                ("PRICE_IND", "Industrial Electricity Price", "EUR/kWh", "price"),
                ("EMISSIONS", "Power Sector GHG Emissions", "Tonnes CO2eq", "emissions"),
                ("POP", "Total Population", "Count", "population")
            ]
            for code, name, unit, domain in metrics:
                stmt = text("""
                    INSERT INTO dim_metric (metric_code, metric_name, unit, domain)
                    VALUES (:code, :name, :unit, :domain)
                    ON CONFLICT (metric_code) DO UPDATE
                    SET metric_name = EXCLUDED.metric_name, unit = EXCLUDED.unit;
                """)
                conn.execute(stmt, {"code": code, "name": name, "unit": unit, "domain": domain})

        print("[Transformer] Dimension tables successfully populated.")

    def ensure_dates_exist(self, periods: List[str]):
        """Ensure all periods exist in dim_date."""
        with self.engine.begin() as conn:
            for p in set(periods):
                p_str = str(p).strip()
                if not p_str:
                    continue
                
                # Determine period type
                if "-" in p_str:
                    parts = p_str.split("-")
                    year = int(parts[0])
                    if parts[1].startswith("S"): # Biannual semester e.g. 2023-S1
                        sem = int(parts[1][1:])
                        period_type = "biannual"
                        stmt = text("""
                            INSERT INTO dim_date (period_code, year, semester, period_type)
                            VALUES (:code, :yr, :sem, :ptype) ON CONFLICT (period_code) DO NOTHING;
                        """)
                        conn.execute(stmt, {"code": p_str, "yr": year, "sem": sem, "ptype": period_type})
                    else: # Monthly e.g. 2023-05
                        month = int(parts[1])
                        quarter = (month - 1) // 3 + 1
                        period_type = "monthly"
                        stmt = text("""
                            INSERT INTO dim_date (period_code, year, month, quarter, period_type)
                            VALUES (:code, :yr, :mo, :qtr, :ptype) ON CONFLICT (period_code) DO NOTHING;
                        """)
                        conn.execute(stmt, {"code": p_str, "yr": year, "mo": month, "qtr": quarter, "ptype": period_type})
                else: # Yearly e.g. 2023
                    year = int(p_str)
                    period_type = "yearly"
                    stmt = text("""
                        INSERT INTO dim_date (period_code, year, period_type)
                        VALUES (:code, :yr, :ptype) ON CONFLICT (period_code) DO NOTHING;
                    """)
                    conn.execute(stmt, {"code": p_str, "yr": year, "ptype": period_type})

    def get_country_id_map(self) -> Dict[str, int]:
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT iso2_code, country_id FROM dim_country")).fetchall()
            country_map = {r[0]: r[1] for r in res}
            # Also map original Eurostat EL to GR
            if "GR" in country_map:
                country_map["EL"] = country_map["GR"]
            return country_map

    def get_date_id_map(self) -> Dict[str, int]:
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT period_code, date_id FROM dim_date")).fetchall()
            return {r[0]: r[1] for r in res}

    def get_source_id_map(self) -> Dict[str, int]:
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT eurostat_code, source_id FROM dim_energy_source")).fetchall()
            return {r[0]: r[1] for r in res}

    def load_generation_data(self, df: pd.DataFrame, source_dataset: str = "nrg_bal_c"):
        """Transform & load electricity generation data into fact_energy_generation."""
        if df.empty:
            return
        
        self.ensure_dates_exist(df["time"].tolist())
        country_map = self.get_country_id_map()
        date_map = self.get_date_id_map()
        source_map = self.get_source_id_map()

        rows_to_insert = []
        for _, row in df.iterrows():
            geo = row["geo"]
            time_code = str(row["time"])
            siec = row.get("siec")
            val = float(row["value"])

            c_id = country_map.get(geo)
            d_id = date_map.get(time_code)
            s_id = source_map.get(siec)

            if c_id and d_id and s_id:
                rows_to_insert.append({
                    "country_id": c_id,
                    "date_id": d_id,
                    "source_id": s_id,
                    "generation_gwh": val,
                    "source_dataset": source_dataset,
                    "source_url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c"
                })

        if not rows_to_insert:
            return

        insert_df = pd.DataFrame(rows_to_insert).drop_duplicates(subset=["country_id", "date_id", "source_id"])
        
        with self.engine.begin() as conn:
            for item in insert_df.to_dict(orient="records"):
                stmt = text("""
                    INSERT INTO fact_energy_generation (country_id, date_id, source_id, generation_gwh, source_dataset, source_url)
                    VALUES (:country_id, :date_id, :source_id, :generation_gwh, :source_dataset, :source_url)
                    ON CONFLICT (country_id, date_id, source_id) DO UPDATE
                    SET generation_gwh = EXCLUDED.generation_gwh;
                """)
                conn.execute(stmt, item)

        print(f"[Transformer] Loaded {len(insert_df)} records into fact_energy_generation.")

    def load_consumption_data(self, df: pd.DataFrame, source_dataset: str = "nrg_cb_e"):
        """Transform & load electricity consumption data into fact_energy_consumption."""
        if df.empty:
            return

        self.ensure_dates_exist(df["time"].tolist())
        country_map = self.get_country_id_map()
        date_map = self.get_date_id_map()

        # Filter for FC (Final Consumption) or ID (Inland Demand)
        cons_df = df[df["nrg_bal"].isin(["FC", "ID", "AFC"])].copy()

        rows_to_insert = []
        for _, row in cons_df.iterrows():
            geo = row["geo"]
            time_code = str(row["time"])
            nrg_bal = row["nrg_bal"]
            val = float(row["value"])

            c_id = country_map.get(geo)
            d_id = date_map.get(time_code)
            ctype = "final_consumption" if nrg_bal == "FC" else "inland_demand"

            if c_id and d_id:
                rows_to_insert.append({
                    "country_id": c_id,
                    "date_id": d_id,
                    "consumption_gwh": val,
                    "consumption_type": ctype,
                    "source_dataset": source_dataset,
                    "source_url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_cb_e"
                })

        if not rows_to_insert:
            return

        insert_df = pd.DataFrame(rows_to_insert).drop_duplicates(subset=["country_id", "date_id", "consumption_type"])

        with self.engine.begin() as conn:
            for item in insert_df.to_dict(orient="records"):
                stmt = text("""
                    INSERT INTO fact_energy_consumption (country_id, date_id, consumption_gwh, consumption_type, source_dataset, source_url)
                    VALUES (:country_id, :date_id, :consumption_gwh, :consumption_type, :source_dataset, :source_url)
                    ON CONFLICT (country_id, date_id, consumption_type) DO UPDATE
                    SET consumption_gwh = EXCLUDED.consumption_gwh;
                """)
                conn.execute(stmt, item)

        print(f"[Transformer] Loaded {len(insert_df)} records into fact_energy_consumption.")

    def load_renewable_shares(self, df: pd.DataFrame, source_dataset: str = "nrg_ind_ren"):
        """Transform & load official renewable share percentages into fact_renewable_share."""
        if df.empty:
            return

        self.ensure_dates_exist(df["time"].tolist())
        country_map = self.get_country_id_map()
        date_map = self.get_date_id_map()

        rows_to_insert = []
        for _, row in df.iterrows():
            geo = row["geo"]
            time_code = str(row["time"])
            val = float(row["value"])

            c_id = country_map.get(geo)
            d_id = date_map.get(time_code)

            if c_id and d_id:
                rows_to_insert.append({
                    "country_id": c_id,
                    "date_id": d_id,
                    "renewable_share_pct": val,
                    "source_dataset": source_dataset
                })

        if not rows_to_insert:
            return

        insert_df = pd.DataFrame(rows_to_insert).drop_duplicates(subset=["country_id", "date_id"])

        with self.engine.begin() as conn:
            for item in insert_df.to_dict(orient="records"):
                stmt = text("""
                    INSERT INTO fact_renewable_share (country_id, date_id, renewable_share_pct, source_dataset)
                    VALUES (:country_id, :date_id, :renewable_share_pct, :source_dataset)
                    ON CONFLICT (country_id, date_id) DO UPDATE
                    SET renewable_share_pct = EXCLUDED.renewable_share_pct;
                """)
                conn.execute(stmt, item)

        print(f"[Transformer] Loaded {len(insert_df)} records into fact_renewable_share.")

    def load_price_data(self, df: pd.DataFrame, consumer_type: str, source_dataset: str):
        """Transform & load electricity price data into fact_energy_price."""
        if df.empty:
            return

        self.ensure_dates_exist(df["time"].tolist())
        country_map = self.get_country_id_map()
        date_map = self.get_date_id_map()

        rows_to_insert = []
        for _, row in df.iterrows():
            geo = row["geo"]
            time_code = str(row["time"])
            val = float(row["value"])

            c_id = country_map.get(geo)
            d_id = date_map.get(time_code)

            if c_id and d_id:
                rows_to_insert.append({
                    "country_id": c_id,
                    "date_id": d_id,
                    "price_eur_kwh": val,
                    "consumer_type": consumer_type,
                    "currency": "EUR",
                    "source_dataset": source_dataset,
                    "source_url": f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{source_dataset}"
                })

        if not rows_to_insert:
            return

        insert_df = pd.DataFrame(rows_to_insert).drop_duplicates(subset=["country_id", "date_id", "consumer_type"])

        with self.engine.begin() as conn:
            for item in insert_df.to_dict(orient="records"):
                stmt = text("""
                    INSERT INTO fact_energy_price (country_id, date_id, price_eur_kwh, consumer_type, currency, source_dataset, source_url)
                    VALUES (:country_id, :date_id, :price_eur_kwh, :consumer_type, :currency, :source_dataset, :source_url)
                    ON CONFLICT (country_id, date_id, consumer_type) DO UPDATE
                    SET price_eur_kwh = EXCLUDED.price_eur_kwh;
                """)
                conn.execute(stmt, item)

        print(f"[Transformer] Loaded {len(insert_df)} records into fact_energy_price ({consumer_type}).")

    def load_emissions(self, df: pd.DataFrame, source_dataset: str = "env_ac_ainah_r2"):
        """Transform & load emissions data (thousand tonnes -> tonnes CO2eq) into fact_emissions."""
        if df.empty:
            return

        self.ensure_dates_exist(df["time"].tolist())
        country_map = self.get_country_id_map()
        date_map = self.get_date_id_map()

        rows_to_insert = []
        for _, row in df.iterrows():
            geo = row["geo"]
            time_code = str(row["time"])
            # Unit is THS_T (thousand tonnes), convert to tonnes
            val_tonnes = float(row["value"]) * 1000.0

            c_id = country_map.get(geo)
            d_id = date_map.get(time_code)

            if c_id and d_id:
                rows_to_insert.append({
                    "country_id": c_id,
                    "date_id": d_id,
                    "emissions_tonnes_co2": val_tonnes,
                    "sector_code": "D",
                    "source_dataset": source_dataset,
                    "source_url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/env_ac_ainah_r2"
                })

        if not rows_to_insert:
            return

        insert_df = pd.DataFrame(rows_to_insert).drop_duplicates(subset=["country_id", "date_id", "sector_code"])

        with self.engine.begin() as conn:
            for item in insert_df.to_dict(orient="records"):
                stmt = text("""
                    INSERT INTO fact_emissions (country_id, date_id, emissions_tonnes_co2, sector_code, source_dataset, source_url)
                    VALUES (:country_id, :date_id, :emissions_tonnes_co2, :sector_code, :source_dataset, :source_url)
                    ON CONFLICT (country_id, date_id, sector_code) DO UPDATE
                    SET emissions_tonnes_co2 = EXCLUDED.emissions_tonnes_co2;
                """)
                conn.execute(stmt, item)

        print(f"[Transformer] Loaded {len(insert_df)} records into fact_emissions.")

    def load_population(self, df: pd.DataFrame, source_dataset: str = "demo_pjan"):
        """Transform & load Eurostat population figures into fact_population."""
        if df.empty:
            return

        self.ensure_dates_exist(df["time"].tolist())
        country_map = self.get_country_id_map()
        date_map = self.get_date_id_map()

        rows_to_insert = []
        for _, row in df.iterrows():
            geo = row["geo"]
            time_code = str(row["time"])
            pop_val = int(float(row["value"]))

            c_id = country_map.get(geo)
            d_id = date_map.get(time_code)

            if c_id and d_id:
                rows_to_insert.append({
                    "country_id": c_id,
                    "date_id": d_id,
                    "population_count": pop_val,
                    "source_dataset": source_dataset
                })

        if not rows_to_insert:
            return

        insert_df = pd.DataFrame(rows_to_insert).drop_duplicates(subset=["country_id", "date_id"])

        with self.engine.begin() as conn:
            for item in insert_df.to_dict(orient="records"):
                stmt = text("""
                    INSERT INTO fact_population (country_id, date_id, population_count, source_dataset)
                    VALUES (:country_id, :date_id, :population_count, :source_dataset)
                    ON CONFLICT (country_id, date_id) DO UPDATE
                    SET population_count = EXCLUDED.population_count;
                """)
                conn.execute(stmt, item)

        print(f"[Transformer] Loaded {len(insert_df)} records into fact_population.")

    def record_provenance(self, dataset_name: str, source_name: str, url: str, spatial_coverage: str, time_coverage: str, unit: str, methodology: str):
        """Record dataset provenance metadata in metadata_data_provenance table."""
        with self.engine.begin() as conn:
            stmt = text("""
                INSERT INTO metadata_data_provenance 
                (source_name, dataset_name, url, spatial_coverage, time_coverage, unit, transformation_methodology)
                VALUES (:source, :dataset, :url, :spatial, :time_cov, :unit, :method)
                ON CONFLICT (dataset_name) DO UPDATE
                SET url = EXCLUDED.url, retrieved_at = CURRENT_TIMESTAMP;
            """)
            conn.execute(stmt, {
                "source": source_name,
                "dataset": dataset_name,
                "url": url,
                "spatial": spatial_coverage,
                "time_cov": time_coverage,
                "unit": unit,
                "method": methodology
            })
