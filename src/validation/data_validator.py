import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

class DataValidator:
    """Automated data quality and validation engine for European energy datasets."""

    def __init__(self):
        self.validation_logs: List[Dict[str, Any]] = []

    def log_issue(self, dataset_name: str, check_type: str, severity: str, message: str, count: int):
        self.validation_logs.append({
            "dataset": dataset_name,
            "check_type": check_type,
            "severity": severity,
            "message": message,
            "affected_count": count
        })

    def validate_generation_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate energy generation dataset (nrg_bal_c / GEP)."""
        dataset_name = "nrg_bal_c_generation"
        initial_count = len(df)
        
        if df.empty:
            self.log_issue(dataset_name, "COMPLETENESS", "CRITICAL", "DataFrame is empty", 0)
            return df, {"total_rows": 0, "valid_rows": 0, "invalid_rows": 0}

        # 1. Missing Critical Fields Check
        required_cols = ["geo", "time", "siec", "value"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.log_issue(dataset_name, "SCHEMA", "CRITICAL", f"Missing required columns: {missing_cols}", initial_count)
            return pd.DataFrame(), {"total_rows": initial_count, "valid_rows": 0, "invalid_rows": initial_count}

        valid_df = df.copy()

        # 2. Check null values in critical fields
        null_mask = valid_df[required_cols].isnull().any(axis=1)
        null_count = null_mask.sum()
        if null_count > 0:
            self.log_issue(dataset_name, "NULL_CHECK", "HIGH", f"Found {null_count} rows with nulls in critical fields", int(null_count))
            valid_df = valid_df[~null_mask]

        # 3. Check for Negative Generation Values (Generation GWh >= 0)
        neg_mask = valid_df["value"] < 0
        neg_count = neg_mask.sum()
        if neg_count > 0:
            self.log_issue(dataset_name, "RANGE_CHECK", "MEDIUM", f"Found {neg_count} negative generation observations (set to 0)", int(neg_count))
            # Generation cannot be negative (except pumped storage which is separate), clamp negative generation to 0
            valid_df.loc[neg_mask, "value"] = 0.0

        # 4. Check Duplicate Country / Date / Fuel Combination
        dup_mask = valid_df.duplicated(subset=["geo", "time", "siec"], keep="first")
        dup_count = dup_mask.sum()
        if dup_count > 0:
            self.log_issue(dataset_name, "DUPLICATE_CHECK", "HIGH", f"Found {dup_count} duplicate country/date/fuel records", int(dup_count))
            valid_df = valid_df[~dup_mask]

        # 5. Outlier Detection (Z-score > 4 within country & fuel, flagged without deletion)
        valid_df["is_outlier"] = False
        for (geo, siec), group in valid_df.groupby(["geo", "siec"]):
            if len(group) >= 5 and group["value"].std() > 0:
                mean = group["value"].mean()
                std = group["value"].std()
                z_scores = (group["value"] - mean).abs() / std
                outlier_indices = group[z_scores > 4.0].index
                valid_df.loc[outlier_indices, "is_outlier"] = True

        outlier_count = valid_df["is_outlier"].sum()
        if outlier_count > 0:
            self.log_issue(dataset_name, "OUTLIER_CHECK", "INFO", f"Flagged {outlier_count} statistical outliers for review", int(outlier_count))

        stats = {
            "total_rows": initial_count,
            "valid_rows": len(valid_df),
            "invalid_rows": initial_count - len(valid_df),
            "duplicate_rows": int(dup_count),
            "null_rows": int(null_count),
            "negative_rows": int(neg_count),
            "outlier_rows": int(outlier_count),
            "date_range": [str(valid_df["time"].min()), str(valid_df["time"].max())] if not valid_df.empty else []
        }

        return valid_df, stats

    def validate_renewable_shares(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate renewable energy share percentages (0 <= pct <= 100)."""
        dataset_name = "nrg_ind_ren_shares"
        initial_count = len(df)

        if df.empty:
            return df, {"total_rows": 0, "valid_rows": 0, "invalid_rows": 0}

        valid_df = df.copy()

        # Check percentages outside [0, 100]
        invalid_pct_mask = (valid_df["value"] < 0) | (valid_df["value"] > 100)
        invalid_pct_count = invalid_pct_mask.sum()
        if invalid_pct_count > 0:
            self.log_issue(dataset_name, "PERCENTAGE_BOUNDS", "HIGH", f"Found {invalid_pct_count} percentage values outside [0, 100]", int(invalid_pct_count))
            valid_df = valid_df[~invalid_pct_mask]

        # Check duplicates
        dup_mask = valid_df.duplicated(subset=["geo", "time"], keep="first")
        dup_count = dup_mask.sum()
        if dup_count > 0:
            valid_df = valid_df[~dup_mask]

        stats = {
            "total_rows": initial_count,
            "valid_rows": len(valid_df),
            "invalid_rows": initial_count - len(valid_df),
            "duplicate_rows": int(dup_count),
            "invalid_percentage_rows": int(invalid_pct_count),
            "date_range": [str(valid_df["time"].min()), str(valid_df["time"].max())] if not valid_df.empty else []
        }

        return valid_df, stats

    def validate_prices(self, df: pd.DataFrame, price_type: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate electricity price data in EUR/kWh."""
        dataset_name = f"price_{price_type}"
        initial_count = len(df)

        if df.empty:
            return df, {"total_rows": 0, "valid_rows": 0, "invalid_rows": 0}

        valid_df = df.copy()

        # Prices cannot be negative or absurdly high (e.g. > €5/kWh)
        invalid_price_mask = (valid_df["value"] <= 0) | (valid_df["value"] > 5.0)
        invalid_count = invalid_price_mask.sum()
        if invalid_count > 0:
            self.log_issue(dataset_name, "PRICE_BOUNDS", "HIGH", f"Found {invalid_count} price values <=0 or > 5.0 EUR/kWh", int(invalid_count))
            valid_df = valid_df[~invalid_price_mask]

        stats = {
            "total_rows": initial_count,
            "valid_rows": len(valid_df),
            "invalid_rows": initial_count - len(valid_df),
            "invalid_price_rows": int(invalid_count)
        }

        return valid_df, stats
