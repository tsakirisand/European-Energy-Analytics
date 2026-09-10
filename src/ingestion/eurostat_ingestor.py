import os
import json
import datetime
import pandas as pd
from typing import Dict, Any, List, Tuple
from src.ingestion.base_ingestor import BaseIngestor

TARGET_COUNTRIES = [
    "EL", "GR", "DE", "FR", "IT", "ES", "PT", "NL", "BE", "AT",
    "SE", "NO", "DK", "FI", "PL", "CZ", "IE", "BG", "RO", "HU",
    "SK", "HR", "SI", "CY", "MT", "LU", "LT", "LV", "EE", "IS",
    "CH", "UK", "AL", "ME", "MK", "RS", "BA", "EU27_2020"
]

class EurostatIngestor(BaseIngestor):
    """Ingest official European energy & statistical datasets directly from Eurostat API."""

    BASE_API_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

    def decode_eurostat_json(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Decode Eurostat JSON-stat matrix format into a flattened pandas DataFrame."""
        if not data or "id" not in data or "size" not in data:
            return pd.DataFrame()

        dims = data["id"]
        sizes = data["size"]
        index_maps = [data["dimension"][d]["category"]["index"] for d in dims]
        label_maps = [data["dimension"][d]["category"].get("label", {}) for d in dims]

        # Calculate strides for row-major matrix indexing
        strides = [1] * len(sizes)
        for i in range(len(sizes) - 2, -1, -1):
            strides[i] = strides[i + 1] * sizes[i + 1]

        # Reverse index mapping: int -> code
        rev_maps = []
        for cat_index in index_maps:
            rev = {v: k for k, v in cat_index.items()}
            rev_maps.append(rev)

        values = data.get("value", {})
        rows = []

        for idx_str, val in values.items():
            if val is None:
                continue
            idx = int(idx_str)
            rem = idx
            row_dict = {}
            for i in range(len(sizes)):
                c = rem // strides[i]
                rem = rem % strides[i]
                code = rev_maps[i].get(c, "")
                dim_name = dims[i]
                row_dict[dim_name] = code
                row_dict[f"{dim_name}_label"] = label_maps[i].get(code, code)
            
            row_dict["value"] = float(val)
            rows.append(row_dict)

        return pd.DataFrame(rows)

    def fetch_dataset(self, dataset_code: str, params: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch Eurostat dataset by code and optional parameters."""
        query_parts = ["lang=EN"]
        if params:
            for k, v in params.items():
                if isinstance(v, list):
                    for item in v:
                        query_parts.append(f"{k}={item}")
                else:
                    query_parts.append(f"{k}={v}")
        
        query_str = "&".join(query_parts)
        url = f"{self.BASE_API_URL}/{dataset_code}?{query_str}"

        # Prioritize loading committed raw JSON files in raw_data_dir for instant, complete historical data
        if os.path.exists(self.raw_data_dir):
            local_files = [f for f in os.listdir(self.raw_data_dir) if f.startswith(f"eurostat_{dataset_code}_") and f.endswith(".json") and not f.endswith(".meta.json")]
            if local_files:
                latest_file = sorted(local_files)[-1]
                local_path = os.path.join(self.raw_data_dir, latest_file)
                print(f"[EurostatIngestor] Loading cached local raw file '{latest_file}'...")
                try:
                    with open(local_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    df = self.decode_eurostat_json(data)
                    metadata = {
                        "source_name": "Eurostat (Local Raw Cache)",
                        "dataset_code": dataset_code,
                        "url": url,
                        "retrieved_at": datetime.datetime.utcnow().isoformat(),
                        "total_records": len(df),
                        "columns": list(df.columns) if not df.empty else []
                    }
                    return df, metadata
                except Exception as e:
                    print(f"[EurostatIngestor] Note: Failed to read local raw cache '{latest_file}': {e}. Fetching live.")

        print(f"[EurostatIngestor] Fetching dataset '{dataset_code}' from Eurostat API...")
        data = self._fetch_url(url)
        df = self.decode_eurostat_json(data)

        metadata = {
            "source_name": "Eurostat",
            "dataset_code": dataset_code,
            "url": url,
            "retrieved_at": datetime.datetime.utcnow().isoformat(),
            "total_records": len(df),
            "columns": list(df.columns) if not df.empty else []
        }

        # Save raw JSON & metadata to data/raw/
        raw_filename = f"eurostat_{dataset_code}_{datetime.date.today().isoformat()}.json"
        self.save_raw_json(raw_filename, data, metadata)

        return df, metadata

    def fetch_annual_generation(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch annual Gross Electricity Production by fuel source (nrg_bal_c)."""
        params = {
            "nrg_bal": "GEP",
            "unit": "GWH",
            "geo": TARGET_COUNTRIES
        }
        return self.fetch_dataset("nrg_bal_c", params)

    def fetch_annual_consumption(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch annual Electricity Balance and Final Consumption (nrg_cb_e)."""
        params = {
            "unit": "GWH",
            "geo": TARGET_COUNTRIES
        }
        return self.fetch_dataset("nrg_cb_e", params)

    def fetch_monthly_electricity(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch monthly Electricity supply and imports/exports (nrg_cb_em)."""
        params = {
            "unit": "GWH",
            "geo": TARGET_COUNTRIES
        }
        return self.fetch_dataset("nrg_cb_em", params)

    def fetch_renewable_shares(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch official Eurostat renewable energy share (% REN_ELC) (nrg_ind_ren)."""
        params = {
            "nrg_bal": "REN_ELC",
            "geo": TARGET_COUNTRIES
        }
        return self.fetch_dataset("nrg_ind_ren", params)

    def fetch_household_prices(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch household electricity prices in EUR/kWh (nrg_pc_204)."""
        params = {
            "currency": "EUR",
            "geo": TARGET_COUNTRIES
        }
        return self.fetch_dataset("nrg_pc_204", params)

    def fetch_industrial_prices(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch non-household / industrial electricity prices in EUR/kWh (nrg_pc_205)."""
        params = {
            "currency": "EUR",
            "geo": TARGET_COUNTRIES
        }
        return self.fetch_dataset("nrg_pc_205", params)

    def fetch_emissions(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch greenhouse gas air emissions accounts for electricity sector D (env_ac_ainah_r2)."""
        params = {
            "nace_r2": "D",
            "airpol": "GHG",
            "unit": "THS_T",  # Thousand tonnes CO2 equivalent
            "geo": TARGET_COUNTRIES
        }
        return self.fetch_dataset("env_ac_ainah_r2", params)

    def fetch_population(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetch Eurostat official population count on 1 January (demo_pjan)."""
        params = {
            "unit": "NR",
            "sex": "T",
            "age": "TOTAL",
            "geo": TARGET_COUNTRIES
        }
        return self.fetch_dataset("demo_pjan", params)
