import pytest
from src.analytics.analytics_engine import AnalyticsEngine

def test_cagr_calculation():
    # 100 GWh to 200 GWh over 10 years
    cagr = AnalyticsEngine.calculate_cagr(100.0, 200.0, 10)
    assert cagr is not None
    assert round(cagr, 2) == 7.18

def test_cagr_invalid_values():
    assert AnalyticsEngine.calculate_cagr(-10.0, 100.0, 5) is None
    assert AnalyticsEngine.calculate_cagr(100.0, 200.0, 0) is None

def test_yoy_calculation():
    yoy = AnalyticsEngine.calculate_yoy(100.0, 120.0)
    assert yoy is not None
    assert round(yoy, 2) == 20.0
    assert AnalyticsEngine.calculate_yoy(0.0, 120.0) is None
