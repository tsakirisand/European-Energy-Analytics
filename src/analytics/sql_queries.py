"""
Repository of analytical SQL queries for European Energy Analytics.
All metrics adhere strictly to mathematical aggregation rules.
"""

SQL_OVERVIEW_KPIS = """
WITH gen_summary AS (
    SELECT 
        d.year,
        SUM(CASE WHEN s.fuel_group = 'total' AND s.eurostat_code = 'TOTAL' THEN g.generation_gwh ELSE 0 END) AS total_gen,
        SUM(CASE WHEN s.fuel_group = 'renewable' THEN g.generation_gwh ELSE 0 END) AS ren_gen,
        SUM(CASE WHEN s.fuel_group = 'fossil' THEN g.generation_gwh ELSE 0 END) AS fossil_gen,
        SUM(CASE WHEN s.fuel_group = 'nuclear' THEN g.generation_gwh ELSE 0 END) AS nuclear_gen
    FROM fact_energy_generation g
    JOIN dim_date d ON g.date_id = d.date_id
    JOIN dim_country c ON g.country_id = c.country_id
    JOIN dim_energy_source s ON g.source_id = s.source_id
    WHERE d.year = :target_year
      AND c.iso2_code = ANY(:countries)
    GROUP BY d.year
),
cons_summary AS (
    SELECT 
        d.year,
        SUM(c_fact.consumption_gwh) AS total_cons
    FROM fact_energy_consumption c_fact
    JOIN dim_date d ON c_fact.date_id = d.date_id
    JOIN dim_country c ON c_fact.country_id = c.country_id
    WHERE d.year = :target_year
      AND c.iso2_code = ANY(:countries)
      AND c_fact.consumption_type = 'final_consumption'
    GROUP BY d.year
)
SELECT 
    g.year,
    g.total_gen,
    g.ren_gen,
    g.fossil_gen,
    g.nuclear_gen,
    COALESCE(c.total_cons, 0) AS total_cons,
    CASE WHEN g.total_gen > 0 THEN (g.ren_gen / g.total_gen * 100.0) ELSE 0 END AS renewable_share_pct,
    CASE WHEN g.total_gen > 0 THEN (g.fossil_gen / g.total_gen * 100.0) ELSE 0 END AS fossil_share_pct,
    CASE WHEN g.total_gen > 0 THEN (g.nuclear_gen / g.total_gen * 100.0) ELSE 0 END AS nuclear_share_pct
FROM gen_summary g
LEFT JOIN cons_summary c ON g.year = c.year;
"""

SQL_COUNTRY_ENERGY_MIX = """
SELECT 
    c.country_name,
    c.iso2_code,
    d.year,
    s.eurostat_code,
    s.source_name,
    s.fuel_group,
    g.generation_gwh
FROM fact_energy_generation g
JOIN dim_date d ON g.date_id = d.date_id
JOIN dim_country c ON g.country_id = c.country_id
JOIN dim_energy_source s ON g.source_id = s.source_id
WHERE d.year = :target_year
  AND c.iso2_code = ANY(:countries)
ORDER BY c.country_name, s.source_id;
"""

SQL_HISTORICAL_GENERATION_BY_FUEL = """
SELECT 
    d.year,
    s.eurostat_code,
    s.source_name,
    s.fuel_group,
    SUM(g.generation_gwh) AS generation_gwh
FROM fact_energy_generation g
JOIN dim_date d ON g.date_id = d.date_id
JOIN dim_country c ON g.country_id = c.country_id
JOIN dim_energy_source s ON g.source_id = s.source_id
WHERE d.year BETWEEN :start_year AND :end_year
  AND c.iso2_code = ANY(:countries)
GROUP BY d.year, s.source_id, s.eurostat_code, s.source_name, s.fuel_group
ORDER BY d.year, s.source_id;
"""

SQL_COUNTRY_RENEWABLE_RANKING = """
SELECT 
    c.country_name,
    c.iso2_code,
    d.year,
    SUM(CASE WHEN s.fuel_group = 'renewable' THEN g.generation_gwh ELSE 0 END) AS renewable_gwh,
    SUM(CASE WHEN s.fuel_group = 'total' AND s.eurostat_code = 'TOTAL' THEN g.generation_gwh ELSE 0 END) AS total_gwh,
    CASE 
        WHEN SUM(CASE WHEN s.fuel_group = 'total' AND s.eurostat_code = 'TOTAL' THEN g.generation_gwh ELSE 0 END) > 0 
        THEN (SUM(CASE WHEN s.fuel_group = 'renewable' THEN g.generation_gwh ELSE 0 END) / 
              SUM(CASE WHEN s.fuel_group = 'total' AND s.eurostat_code = 'TOTAL' THEN g.generation_gwh ELSE 0 END) * 100.0)
        ELSE 0 
    END AS calculated_renewable_share_pct,
    r.renewable_share_pct AS official_renewable_share_pct
FROM fact_energy_generation g
JOIN dim_date d ON g.date_id = d.date_id
JOIN dim_country c ON g.country_id = c.country_id
JOIN dim_energy_source s ON g.source_id = s.source_id
LEFT JOIN fact_renewable_share r ON r.country_id = c.country_id AND r.date_id = d.date_id
WHERE d.year = :target_year
  AND c.iso2_code != 'EU27'
GROUP BY c.country_name, c.iso2_code, d.year, r.renewable_share_pct
ORDER BY calculated_renewable_share_pct DESC;
"""

SQL_SINGLE_COUNTRY_DEEP_DIVE = """
SELECT 
    d.year,
    SUM(CASE WHEN s.eurostat_code = 'TOTAL' THEN g.generation_gwh ELSE 0 END) AS total_gwh,
    SUM(CASE WHEN s.eurostat_code = 'RA300' THEN g.generation_gwh ELSE 0 END) AS wind_gwh,
    SUM(CASE WHEN s.eurostat_code = 'RA420' THEN g.generation_gwh ELSE 0 END) AS solar_gwh,
    SUM(CASE WHEN s.eurostat_code = 'RA100' THEN g.generation_gwh ELSE 0 END) AS hydro_gwh,
    SUM(CASE WHEN s.fuel_group = 'fossil' THEN g.generation_gwh ELSE 0 END) AS fossil_gwh,
    SUM(CASE WHEN s.fuel_group = 'renewable' THEN g.generation_gwh ELSE 0 END) AS total_renewable_gwh
FROM fact_energy_generation g
JOIN dim_date d ON g.date_id = d.date_id
JOIN dim_country c ON g.country_id = c.country_id
JOIN dim_energy_source s ON g.source_id = s.source_id
WHERE c.iso2_code = :country_code
GROUP BY d.year
ORDER BY d.year ASC;
"""

SQL_ELECTRICITY_PRICES = """
SELECT 
    c.country_name,
    c.iso2_code,
    d.period_code,
    d.year,
    d.semester,
    p.price_eur_kwh,
    p.consumer_type
FROM fact_energy_price p
JOIN dim_date d ON p.date_id = d.date_id
JOIN dim_country c ON p.country_id = c.country_id
WHERE c.iso2_code = ANY(:countries)
ORDER BY d.period_code ASC, c.country_name;
"""

SQL_PER_CAPITA_METRICS = """
SELECT 
    c.country_name,
    c.iso2_code,
    d.year,
    g_tot.total_gen_gwh,
    c_tot.total_cons_gwh,
    p.population_count,
    CASE WHEN p.population_count > 0 THEN (g_tot.total_gen_gwh * 1000000.0 / p.population_count) ELSE NULL END AS gen_kwh_per_capita,
    CASE WHEN p.population_count > 0 THEN (c_tot.total_cons_gwh * 1000000.0 / p.population_count) ELSE NULL END AS cons_kwh_per_capita
FROM dim_country c
JOIN dim_date d ON 1=1
JOIN fact_population p ON p.country_id = c.country_id AND p.date_id = d.date_id
LEFT JOIN (
    SELECT country_id, date_id, generation_gwh AS total_gen_gwh
    FROM fact_energy_generation g
    JOIN dim_energy_source s ON g.source_id = s.source_id
    WHERE s.eurostat_code = 'TOTAL'
) g_tot ON g_tot.country_id = c.country_id AND g_tot.date_id = d.date_id
LEFT JOIN (
    SELECT country_id, date_id, consumption_gwh AS total_cons_gwh
    FROM fact_energy_consumption
    WHERE consumption_type = 'final_consumption'
) c_tot ON c_tot.country_id = c.country_id AND c_tot.date_id = d.date_id
WHERE d.year = :target_year
  AND c.iso2_code = ANY(:countries)
ORDER BY gen_kwh_per_capita DESC;
"""
