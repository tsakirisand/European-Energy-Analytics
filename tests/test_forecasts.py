import pytest
import pandas as pd
from src.forecasting.forecaster import Forecaster

def test_forecast_tagging():
    df = pd.DataFrame([
        {"year": 2018, "val": 100.0},
        {"year": 2019, "val": 110.0},
        {"year": 2020, "val": 120.0},
        {"year": 2021, "val": 130.0}
    ])
    res_df, meta = Forecaster.forecast_linear(df, "year", "val", horizon_years=3)
    assert not res_df.empty
    assert len(res_df) == 7 # 4 hist + 3 fc
    
    hist_types = res_df[res_df["data_type"] == "Historical Fact (Official Source)"]
    fc_types = res_df[res_df["data_type"] == "Forecast / Model Projection (NOT Fact)"]

    assert len(hist_types) == 4
    assert len(fc_types) == 3
    assert meta["r2_score"] > 0.95
