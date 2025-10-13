import json
import pandas as pd
from pathlib import Path
from src.preprocess_data import preprocess

def test_preprocess_creates_clean_output(tmp_path):
    # Create small fake data
    raw_data = [
        {"title": "Paper A", "abstract": "This is an abstract " * 3, "doi": "10.1/a"},
        {"title": "Paper A", "abstract": "This is an abstract " * 3, "doi": "10.1/a"},  # duplicate
        {"title": "Paper B", "abstract": None, "doi": "10.1/b"},                       # bad row
        {"title": "Paper C", "abstract": "Good content " * 3, "doi": None}
    ]

    # Write to a temp raw file
    raw_path = tmp_path / "raw.json"
    json.dump(raw_data, open(raw_path, "w"))

    out_json = tmp_path / "out.json"
    out_csv  = tmp_path / "out.csv"

    # Call your preprocess function
    preprocess(str(raw_path), str(out_json), str(out_csv))

    # Read the output CSV and verify
    df = pd.read_csv(out_csv)
    # Only 2 rows should remain (one duplicate removed, one bad row dropped)
    assert len(df) == 2
    # text_length column must exist
    assert "text_length" in df.columns
