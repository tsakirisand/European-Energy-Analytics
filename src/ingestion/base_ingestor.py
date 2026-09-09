import os
import json
import ssl
import time
import urllib.request
from typing import Dict, Any, Optional

class BaseIngestor:
    """Base class for official API data ingestion with provenance tracking."""

    def __init__(self, raw_data_dir: str = "data/raw"):
        self.raw_data_dir = os.path.abspath(raw_data_dir)
        os.makedirs(self.raw_data_dir, exist_ok=True)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _fetch_url(self, url: str, headers: Optional[Dict[str, str]] = None, retries: int = 3, delay: float = 2.0) -> Dict[str, Any]:
        """Fetch URL content with retry logic and unverified SSL context for Eurostat/official APIs."""
        default_headers = {"User-Agent": "EuropeanEnergyAnalytics/1.0 (Official Data Extraction)"}
        if headers:
            default_headers.update(headers)

        req = urllib.request.Request(url, headers=default_headers)
        
        last_error = None
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=30) as resp:
                    raw_bytes = resp.read()
                    data = json.loads(raw_bytes.decode("utf-8"))
                    return data
            except Exception as e:
                last_error = e
                print(f"[BaseIngestor] Warning: Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                time.sleep(delay * (attempt + 1))
        
        raise RuntimeError(f"Failed to fetch data from {url} after {retries} attempts. Error: {last_error}")

    def save_raw_json(self, filename: str, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Save raw JSON payload and associated provenance metadata to data/raw/."""
        filepath = os.path.join(self.raw_data_dir, filename)
        meta_filepath = os.path.join(self.raw_data_dir, f"{filename}.meta.json")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        with open(meta_filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return filepath
