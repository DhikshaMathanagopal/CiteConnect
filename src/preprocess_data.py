import json, pandas as pd, argparse
from pathlib import Path

def preprocess(inp, out_json, out_csv):
    data = json.load(open(inp))
    df = pd.json_normalize(data)
    df = df[df["abstract"].notna()]
    df = df.drop_duplicates(subset=["doi", "title"])
    df["text_length"] = df["abstract"].str.len()
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    df.to_json(out_json, orient="records", indent=2)
    df.to_csv(out_csv, index=False)
    print(f"✅ Cleaned {len(df)} rows")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inp", required=True)
    args = parser.parse_args()
    name = Path(args.inp).stem
    preprocess(args.inp, f"data/processed/{name}_processed.json",
                          f"data/processed/{name}_processed.csv")
