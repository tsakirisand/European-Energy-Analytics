-- European Energy Analytics Database Schema (PostgreSQL)

CREATE TABLE IF NOT EXISTS dim_country (
    country_id SERIAL PRIMARY KEY,
    iso2_code VARCHAR(10) UNIQUE NOT NULL,
    iso3_code VARCHAR(10),
    country_name VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    is_eu_member BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    period_code VARCHAR(20) UNIQUE NOT NULL, -- e.g. '2023' or '2023-05' or '2023-S1'
    year INTEGER NOT NULL,
    month INTEGER,                          -- NULL for annual data
    quarter INTEGER,                        -- NULL for annual data
    semester INTEGER,                       -- 1 or 2 for biannual prices
    period_type VARCHAR(20) NOT NULL        -- 'yearly', 'monthly', 'biannual'
);

CREATE TABLE IF NOT EXISTS dim_energy_source (
    source_id SERIAL PRIMARY KEY,
    eurostat_code VARCHAR(50) UNIQUE NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    fuel_group VARCHAR(50) NOT NULL         -- 'renewable', 'fossil', 'nuclear', 'total', 'other'
);

CREATE TABLE IF NOT EXISTS dim_metric (
    metric_id SERIAL PRIMARY KEY,
    metric_code VARCHAR(50) UNIQUE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    domain VARCHAR(50) NOT NULL            -- 'generation', 'consumption', 'price', 'emissions', 'share', 'population'
);

CREATE TABLE IF NOT EXISTS fact_energy_generation (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES dim_country(country_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    source_id INTEGER REFERENCES dim_energy_source(source_id),
    generation_gwh NUMERIC(14, 4) NOT NULL,
    source_dataset VARCHAR(100) NOT NULL,
    source_url TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_gen_country_date_source UNIQUE (country_id, date_id, source_id)
);

CREATE TABLE IF NOT EXISTS fact_energy_consumption (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES dim_country(country_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    consumption_gwh NUMERIC(14, 4) NOT NULL,
    consumption_type VARCHAR(50) NOT NULL, -- 'final_consumption', 'inland_demand'
    source_dataset VARCHAR(100) NOT NULL,
    source_url TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_cons_country_date_type UNIQUE (country_id, date_id, consumption_type)
);

CREATE TABLE IF NOT EXISTS fact_energy_price (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES dim_country(country_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    price_eur_kwh NUMERIC(10, 6) NOT NULL,
    consumer_type VARCHAR(50) NOT NULL,    -- 'household', 'industrial'
    currency VARCHAR(10) DEFAULT 'EUR',
    source_dataset VARCHAR(100) NOT NULL,
    source_url TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_price_country_date_type UNIQUE (country_id, date_id, consumer_type)
);

CREATE TABLE IF NOT EXISTS fact_emissions (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES dim_country(country_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    emissions_tonnes_co2 NUMERIC(16, 2) NOT NULL,
    sector_code VARCHAR(50) DEFAULT 'D35',
    source_dataset VARCHAR(100) NOT NULL,
    source_url TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_emissions_country_date UNIQUE (country_id, date_id, sector_code)
);

CREATE TABLE IF NOT EXISTS fact_population (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES dim_country(country_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    population_count BIGINT NOT NULL,
    source_dataset VARCHAR(100) NOT NULL,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_pop_country_date UNIQUE (country_id, date_id)
);

CREATE TABLE IF NOT EXISTS fact_renewable_share (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES dim_country(country_id),
    date_id INTEGER REFERENCES dim_date(date_id),
    renewable_share_pct NUMERIC(6, 2) NOT NULL,
    source_dataset VARCHAR(100) NOT NULL,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_ren_country_date UNIQUE (country_id, date_id)
);

CREATE TABLE IF NOT EXISTS metadata_data_provenance (
    dataset_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    dataset_name VARCHAR(100) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    spatial_coverage VARCHAR(255),
    time_coverage VARCHAR(255),
    unit VARCHAR(50),
    transformation_methodology TEXT
);
