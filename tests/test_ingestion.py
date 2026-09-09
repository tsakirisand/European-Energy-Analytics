import pytest
import pandas as pd
from src.ingestion.eurostat_ingestor import EurostatIngestor

def test_eurostat_json_decoding():
    ingestor = EurostatIngestor()
    dummy_data = {
        "version": "2.0",
        "class": "dataset",
        "id": ["geo", "time"],
        "size": [2, 2],
        "dimension": {
            "geo": {"category": {"index": {"GR": 0, "DE": 1}, "label": {"GR": "Greece", "DE": "Germany"}}},
            "time": {"category": {"index": {"2022": 0, "2023": 1}, "label": {"2022": "2022", "2023": "2023"}}}
        },
        "value": {"0": 100.0, "1": 110.0, "2": 500.0, "3": 520.0}
    }
    df = ingestor.decode_eurostat_json(dummy_data)
    assert not df.empty
    assert len(df) == 4
    assert "geo" in df.columns
    assert df[df["geo"] == "GR"]["value"].tolist() == [100.0, 110.0]
