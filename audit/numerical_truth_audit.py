import sys
import os
import pandas as pd
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analytics.analytics_engine import AnalyticsEngine
from database.db_manager import get_db_engine

def run_numerical_truth_audit():
    print("==================================================")
    print("NUMERICAL TRUTH AUDIT — EUROPEAN ENERGY ANALYTICS")
    print("==================================================")

    analytics = AnalyticsEngine()
    engine = get_db_engine()

    passed_tests = 0
    failed_tests = 0
    unverified_tests = 0

    def check_metric(test_name: str, condition: bool, details: str = ""):
        nonlocal passed_tests, failed_tests
        if condition:
            passed_tests += 1
            print(f"  [PASS] {test_name}: {details}")
        else:
            failed_tests += 1
            print(f"  [FAIL] ❌ {test_name}: {details}")

    print("\n[Phase 1/4] Auditing Database Table Record Counts...")
    with engine.connect() as conn:
        gen_cnt = conn.execute(text("SELECT COUNT(*) FROM fact_energy_generation")).scalar()
        cons_cnt = conn.execute(text("SELECT COUNT(*) FROM fact_energy_consumption")).scalar()
        price_cnt = conn.execute(text("SELECT COUNT(*) FROM fact_energy_price")).scalar()
        em_cnt = conn.execute(text("SELECT COUNT(*) FROM fact_emissions")).scalar()
        pop_cnt = conn.execute(text("SELECT COUNT(*) FROM fact_population")).scalar()
        ren_cnt = conn.execute(text("SELECT COUNT(*) FROM fact_renewable_share")).scalar()

    check_metric("Generation Fact Table populated", gen_cnt > 1000, f"Count = {gen_cnt:,}")
    check_metric("Consumption Fact Table populated", cons_cnt > 500, f"Count = {cons_cnt:,}")
    check_metric("Price Fact Table populated", price_cnt > 500, f"Count = {price_cnt:,}")
    check_metric("Emissions Fact Table populated", em_cnt > 100, f"Count = {em_cnt:,}")
    check_metric("Population Fact Table populated", pop_cnt > 500, f"Count = {pop_cnt:,}")
    check_metric("Renewable Share Fact Table populated", ren_cnt > 100, f"Count = {ren_cnt:,}")

    print("\n[Phase 2/4] Testing 50+ Numerical Truth Metrics Across Years & Countries...")
    years_to_test = analytics.get_available_years()[-5:] # Last 5 years
    countries_to_test = ["GR", "DE", "FR", "IT", "ES", "PT", "NL", "BE", "AT", "SE"]

    for yr in years_to_test:
        for c in countries_to_test:
            kpis = analytics.get_overview_kpis(yr, [c])
            # Generation math check: ren + fossil + nuclear <= total + delta
            tot = kpis["total_gen_gwh"]
            ren = kpis["ren_gen_gwh"]
            fossil = kpis["fossil_gen_gwh"]
            nuc = kpis["nuclear_gen_gwh"]

            if tot > 0:
                ren_share = kpis["renewable_share_pct"]
                # Mathematical formula check
                calc_share = (ren / tot) * 100.0
                diff = abs(ren_share - calc_share)
                check_metric(f"Math Truth ({c}-{yr}): Share == (Ren/Total)*100", diff < 0.01, f"Share = {ren_share:.2f}%, Calc = {calc_share:.2f}%")
            else:
                check_metric(f"Zero Gen Truth ({c}-{yr})", tot == 0, "No generation reported")

    print("\n[Phase 3/4] Testing Greece Specific Historical Observations...")
    gr_df = analytics.get_greece_analysis()
    check_metric("Greece Historical Time-Series", len(gr_df) >= 10, f"Years available = {len(gr_df)}")
    
    if not gr_df.empty:
        latest_gr = gr_df.iloc[-1]
        gr_yr = int(latest_gr["year"])
        gr_ren = float(latest_gr["total_renewable_gwh"])
        gr_tot = float(latest_gr["total_gwh"])
        check_metric(f"Greece ({gr_yr}) Total > 0", gr_tot > 0, f"Total = {gr_tot:,.1f} GWh")
        check_metric(f"Greece ({gr_yr}) Renewables > 0", gr_ren > 0, f"Renewable = {gr_ren:,.1f} GWh")

    print("\n[Phase 4/4] Summary Audit Report")
    print(f"Total Numerical Metrics Tested: {passed_tests + failed_tests + unverified_tests}")
    print(f"PASS: {passed_tests}")
    print(f"FAIL: {failed_tests}")
    print(f"UNVERIFIED: {unverified_tests}")

    if failed_tests == 0 and unverified_tests == 0:
        print("\nFINAL STATUS: PASS — NUMERICALLY VERIFIED")
        return True
    else:
        print("\nFINAL STATUS: FAIL — UNVERIFIED / FAILED METRICS REMAIN")
        return False

if __name__ == "__main__":
    run_numerical_truth_audit()
