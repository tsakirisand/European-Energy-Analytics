import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import LinearRegression

class Forecaster:
    """Transparent time-series forecasting engine with explicit scenario labeling."""

    @staticmethod
    def forecast_linear(df: pd.DataFrame, time_col: str, value_col: str, horizon_years: int = 5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Generate transparent linear trend forecast with confidence intervals.
        Returns combined historical + forecast DataFrame with clear 'data_type' tags.
        """
        if df.empty or len(df) < 3:
            return pd.DataFrame(), {"model": "Linear Regression", "status": "Insufficient data"}

        clean_df = df.dropna(subset=[time_col, value_col]).sort_values(by=time_col).copy()
        clean_df[time_col] = clean_df[time_col].astype(int)
        
        X = clean_df[[time_col]].values
        y = clean_df[value_col].values

        model = LinearRegression()
        model.fit(X, y)

        y_pred_hist = model.predict(X)
        ss_res = np.sum((y - y_pred_hist) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        rmse = float(np.sqrt(np.mean((y - y_pred_hist) ** 2)))

        last_year = int(clean_df[time_col].max())
        future_years = np.array([[last_year + i] for i in range(1, horizon_years + 1)])
        future_pred = model.predict(future_years)

        # Standard error of estimate for 95% confidence intervals
        residual_std = float(np.std(y - y_pred_hist))
        ci_95 = 1.96 * residual_std

        hist_records = []
        for idx, row in clean_df.iterrows():
            hist_records.append({
                "year": int(row[time_col]),
                "value": float(row[value_col]),
                "lower_bound": float(row[value_col]),
                "upper_bound": float(row[value_col]),
                "data_type": "Historical Fact (Official Source)"
            })

        forecast_records = []
        for year_val, pred_val in zip(future_years.flatten(), future_pred):
            forecast_records.append({
                "year": int(year_val),
                "value": max(0.0, float(pred_val)),
                "lower_bound": max(0.0, float(pred_val - ci_95)),
                "upper_bound": max(0.0, float(pred_val + ci_95)),
                "data_type": "Forecast / Model Projection (NOT Fact)"
            })

        result_df = pd.DataFrame(hist_records + forecast_records)

        metadata = {
            "model_type": "Linear Trend Regression (OLS)",
            "historical_years": f"{clean_df[time_col].min()} - {last_year}",
            "forecast_horizon": f"{last_year + 1} - {last_year + horizon_years}",
            "annual_growth_slope": float(model.coef_[0]),
            "r2_score": float(r2),
            "rmse": rmse,
            "confidence_interval": "95%",
            "disclaimer": "Forecast outputs are mathematical models based on historical trends and DO NOT constitute official historical facts."
        }

        return result_df, metadata
