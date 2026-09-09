import os
import sys
import time
import datetime
from database.db_manager import ensure_postgres_running, init_schema, get_db_engine
from src.ingestion.eurostat_ingestor import EurostatIngestor
from src.validation.data_validator import DataValidator
from src.transformation.transformer import Transformer
from src.data_quality.quality_reporter import QualityReporter

def run_pipeline():
    print("==================================================")
    print("EUROPEAN ENERGY ANALYTICS — ETL PIPELINE RUNNER")
    print("==================================================")
    print(f"Timestamp: {datetime.datetime.utcnow().isoformat()}")

    # Step 1: Ensure Postgres & Schema
    print("\n[Step 1/5] Initializing Database & Schema...")
    ensure_postgres_running()
    init_schema()

    # Step 2: Ingest Raw Eurostat Data
    print("\n[Step 2/5] Ingesting Official Eurostat Data...")
    ingestor = EurostatIngestor()

    df_gen_raw, meta_gen = ingestor.fetch_annual_generation()
    df_cons_raw, meta_cons = ingestor.fetch_annual_consumption()
    df_ren_raw, meta_ren = ingestor.fetch_renewable_shares()
    df_price_hh_raw, meta_p_hh = ingestor.fetch_household_prices()
    df_price_ind_raw, meta_p_ind = ingestor.fetch_industrial_prices()
    df_emiss_raw, meta_emiss = ingestor.fetch_emissions()
    df_pop_raw, meta_pop = ingestor.fetch_population()

    # Step 3: Data Validation Checks
    print("\n[Step 3/5] Executing Data Quality & Bound Checks...")
    validator = DataValidator()

    df_gen, gen_stats = validator.validate_generation_data(df_gen_raw)
    df_ren, ren_stats = validator.validate_renewable_shares(df_ren_raw)
    df_price_hh, price_hh_stats = validator.validate_prices(df_price_hh_raw, "household")
    df_price_ind, price_ind_stats = validator.validate_prices(df_price_ind_raw, "industrial")

    print(f"  Generation Validated: {gen_stats['valid_rows']}/{gen_stats['total_rows']} rows")
    print(f"  Renewable Shares Validated: {ren_stats['valid_rows']}/{ren_stats['total_rows']} rows")

    # Step 4: Data Transformation & Warehousing
    print("\n[Step 4/5] Loading Transformed Data into PostgreSQL Warehouse...")
    transformer = Transformer()
    transformer.populate_dimensions()

    transformer.load_generation_data(df_gen, "nrg_bal_c")
    transformer.load_consumption_data(df_cons_raw, "nrg_cb_e")
    transformer.load_renewable_shares(df_ren, "nrg_ind_ren")
    transformer.load_price_data(df_price_hh, "household", "nrg_pc_204")
    transformer.load_price_data(df_price_ind, "industrial", "nrg_pc_205")
    transformer.load_emissions(df_emiss_raw, "env_ac_ainah_r2")
    transformer.load_population(df_pop_raw, "demo_pjan")

    # Record Provenance
    transformer.record_provenance("nrg_bal_c", "Eurostat", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c", "European Union & EEA", "2000 - 2024", "GWh", "Gross Electricity Production by fuel source")
    transformer.record_provenance("nrg_ind_ren", "Eurostat", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_ind_ren", "European Union & EEA", "2004 - 2024", "%", "Official Eurostat share of electricity from renewable sources")
    transformer.record_provenance("demo_pjan", "Eurostat", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjan", "European Union & EEA", "1960 - 2024", "Count", "Population on 1 January")

    # Step 5: Data Quality Report
    print("\n[Step 5/5] Generating Automated Data Quality Report...")
    reporter = QualityReporter()
    print(reporter.generate_text_report())

    print("==================================================")
    print("ETL PIPELINE COMPLETED SUCCESSFULLY")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()
