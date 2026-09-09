import pytest
import pandas as pd
from src.validation.data_validator import DataValidator

def test_generation_validation():
    validator = DataValidator()
    df = pd.DataFrame([
        {"geo": "GR", "time": "2023", "siec": "RA300", "value": 5000.0},
        {"geo": "GR", "time": "2023", "siec": "RA300", "value": 5000.0}, # Duplicate
        {"geo": "DE", "time": "2023", "siec": "RA300", "value": -50.0}    # Negative
    ])
    val_df, stats = validator.validate_generation_data(df)
    assert stats["duplicate_rows"] == 1
    assert stats["negative_rows"] == 1
    assert len(val_df) == 2
    assert val_df[val_df["geo"] == "DE"]["value"].values[0] == 0.0

def test_renewable_share_validation():
    validator = DataValidator()
    df = pd.DataFrame([
        {"geo": "GR", "time": "2023", "value": 45.2},
        {"geo": "DE", "time": "2023", "value": 120.0} # Out of bounds
    ])
    val_df, stats = validator.validate_renewable_shares(df)
    assert stats["invalid_percentage_rows"] == 1
    assert len(val_df) == 1
    assert val_df.iloc[0]["geo"] == "GR"
