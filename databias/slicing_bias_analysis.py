"""
databias/slicing_bias_analysis.py
--------------------------------
Performs bias slicing and fairness analysis on CiteConnect papers.
Now fully cloud-ready: loads from GCS, saves mitigated data and bias metrics
back to GCS, and triggers an email alert if thresholds are exceeded.
"""

import os
import pandas as pd
import numpy as np
from fairlearn.metrics import MetricFrame
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import storage
from io import BytesIO
import json
import ast
import smtplib
from email.mime.text import MIMEText

# ------------------------------------------------------
# 1️⃣ GCS Configuration (Auto-detect environment)
# ------------------------------------------------------
BUCKET_NAME = "citeconnect-test-bucket"
# Load from ALL pipeline stages for comprehensive analysis
SOURCE_FOLDERS = ["raw/", "raw_v2/", "processed/", "processed_v2/"]
OUTPUT_PREFIX = "bias_outputs/"

# Auto-detect credentials: local vs Airflow
if os.path.exists("/Users/dhikshamathan/Downloads/gcs-key.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/dhikshamathan/Downloads/gcs-key.json"
elif os.path.exists("/opt/airflow/gcs-key.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/gcs-key.json"

client = storage.Client()
bucket = client.bucket(BUCKET_NAME)
print(f"✅ Connected to project: {client.project}")

# ------------------------------------------------------
# 2️⃣ Helper to Upload Results to GCS
# ------------------------------------------------------
def upload_to_gcs(local_path, dest_blob):
    blob = bucket.blob(OUTPUT_PREFIX + dest_blob)
    blob.upload_from_filename(local_path)
    print(f"📤 Uploaded {local_path} → gs://{BUCKET_NAME}/{OUTPUT_PREFIX}{dest_blob}")

# ------------------------------------------------------
# 3️⃣ Helper to Parse JSON/List Columns
# ------------------------------------------------------
def parse_json_column(x):
    """Convert JSON strings or lists into Python lists for proper analysis"""
    if pd.isna(x):
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            try:
                return ast.literal_eval(x)
            except Exception:
                return [x]
    return [x]

# ------------------------------------------------------
# 4️⃣ Load ALL data from ALL pipeline stages
# ------------------------------------------------------
print(f"📥 Loading parquet files from ALL pipeline stages:")
print(f"   • gs://{BUCKET_NAME}/raw/")
print(f"   • gs://{BUCKET_NAME}/raw_v2/")
print(f"   • gs://{BUCKET_NAME}/processed/")
print(f"   • gs://{BUCKET_NAME}/processed_v2/")
print()

all_dfs = []
total_files = 0

for folder in SOURCE_FOLDERS:
    print(f"📂 Scanning {folder}...")
    
    # List all parquet files in this folder
    blobs = list(bucket.list_blobs(prefix=folder))
    parquet_files = [b for b in blobs if b.name.endswith('.parquet')]
    
    if not parquet_files:
        print(f"  ⚠️  No parquet files found in {folder}")
        continue
    
    print(f"  Found {len(parquet_files)} parquet files")
    
    # Load files from this folder
    for i, blob in enumerate(parquet_files, 1):
        filename = blob.name.split('/')[-1]
        size_mb = blob.size / (1024 * 1024)
        print(f"    [{i}/{len(parquet_files)}] {filename} ({size_mb:.1f} MB)...", end="")
        
        try:
            data = blob.download_as_bytes()
            temp_df = pd.read_parquet(BytesIO(data))
            temp_df['source_folder'] = folder  # Track which folder it came from
            temp_df['source_file'] = blob.name
            all_dfs.append(temp_df)
            print(f" ✅ {len(temp_df)} papers")
            total_files += 1
        except Exception as e:
            print(f" ❌ Failed: {e}")
    
    print()

if not all_dfs:
    print("❌ No data loaded successfully from any folder")
    exit(1)

# Combine all dataframes
print("🔗 Combining all datasets...")
df = pd.concat(all_dfs, ignore_index=True)
print(f"✅ Loaded {len(df):,} papers total from {total_files} files across {len(SOURCE_FOLDERS)} folders")
print(f"   Breakdown by folder:")
for folder in SOURCE_FOLDERS:
    count = len(df[df['source_folder'] == folder])
    if count > 0:
        print(f"   • {folder:20s} {count:,} papers")
print()

# Clean numeric & categorical fields
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["citationCount"] = pd.to_numeric(df["citationCount"], errors="coerce").fillna(0)
df["intro_length"] = pd.to_numeric(df["intro_length"], errors="coerce").fillna(0)

# Parse fieldsOfStudy as a list (handles both strings and actual lists)
df["fieldsOfStudy"] = df["fieldsOfStudy"].apply(parse_json_column)

df["content_quality"] = df["content_quality"].astype(str)

os.makedirs("databias/slices", exist_ok=True)

# ------------------------------------------------------
# 5️⃣ Explode fieldsOfStudy for Proper Multi-Field Analysis
# ------------------------------------------------------
# Create exploded version: each paper contributes to ALL its fields
df_exploded = df.explode("fieldsOfStudy").copy()
# Remove empty fields
df_exploded = df_exploded[df_exploded["fieldsOfStudy"].str.len() > 0]
print(f"✅ Exploded to {len(df_exploded)} field-paper pairs for fairness analysis")

# ------------------------------------------------------
# 6️⃣ Slice Summaries
# ------------------------------------------------------
slices = {
    "year": df.groupby("year")["citationCount"].mean().to_dict(),
    "fieldsOfStudy": df_exploded.groupby("fieldsOfStudy")["citationCount"].mean().to_dict(),
    "content_quality": df.groupby("content_quality")["intro_length"].mean().to_dict(),
}
with open("databias/slices/slice_summary.json", "w") as f:
    json.dump(slices, f, indent=2)
upload_to_gcs("databias/slices/slice_summary.json", "slice_summary.json")

# ------------------------------------------------------
# 7️⃣ Fairlearn MetricFrame (Using Exploded Data)
# ------------------------------------------------------
y_true = df_exploded["citationCount"].to_numpy()
y_pred = df_exploded["citationCount"].to_numpy()
sensitive = df_exploded["fieldsOfStudy"].to_numpy()

metric_frame = MetricFrame(
    metrics={"mean_citations": lambda y_true, y_pred: np.mean(y_true)},
    y_true=y_true,
    y_pred=y_pred,
    sensitive_features=sensitive
)
fairness_df = metric_frame.by_group.sort_values("mean_citations", ascending=False)
print("\n🎓 Avg citation count by field (exploded):")
print(fairness_df.head(10))

plt.figure(figsize=(10,6))
sns.barplot(
    x=fairness_df.head(10)["mean_citations"].values,
    y=fairness_df.head(10).index,
    palette="crest"
)
plt.title("Average Citation Count by Field")
plt.xlabel("Mean Citations")
plt.ylabel("Field of Study")
plt.tight_layout()
plt.savefig("databias/slices/field_slicing_bias.png", bbox_inches="tight")
upload_to_gcs("databias/slices/field_slicing_bias.png", "field_slicing_bias.png")

# ------------------------------------------------------
# 8️⃣ Mitigation: Re-sample underrepresented fields
# ------------------------------------------------------
# Use exploded data to identify underrepresented fields
field_counts = df_exploded["fieldsOfStudy"].value_counts()
median_count = field_counts.median()
underrep_fields = set(field_counts[field_counts < median_count].index)

# Function to check if any field in a paper's list is underrepresented
def has_underrep_field(fields):
    if isinstance(fields, list):
        return any(f in underrep_fields for f in fields)
    return fields in underrep_fields

# Apply mitigation on original df (before explosion)
df_underrep = df[df["fieldsOfStudy"].apply(has_underrep_field)]
df_overrep = df[~df["fieldsOfStudy"].apply(has_underrep_field)]

df_balanced = pd.concat([
    df_underrep.sample(frac=2, replace=True, random_state=42),
    df_overrep
])

# Save balanced data with proper list serialization
df_balanced_save = df_balanced.copy()
df_balanced_save["fieldsOfStudy"] = df_balanced_save["fieldsOfStudy"].apply(json.dumps)
df_balanced_save.to_parquet("data/combined_gcs_data_balanced.parquet", index=False)
upload_to_gcs("data/combined_gcs_data_balanced.parquet", "combined_gcs_data_balanced.parquet")

print(f"\n⚖️ After mitigation: {len(df_balanced)} samples (was {len(df)})")
print(f"   Underrepresented fields: {len(underrep_fields)}")

# ------------------------------------------------------
# 9️⃣ Fairness Disparity Check
# ------------------------------------------------------
max_mean = fairness_df["mean_citations"].max()
min_mean = fairness_df["mean_citations"].min()
disparity_ratio = (max_mean / (min_mean + 1e-6)) if min_mean > 0 else np.inf
disparity_diff = max_mean - min_mean

fairness_stats = {
    "max_group_mean": float(max_mean),
    "min_group_mean": float(min_mean),
    "disparity_ratio": float(disparity_ratio),
    "disparity_difference": float(disparity_diff),
    "analysis_note": "Computed on exploded field data - each paper contributes to all its fields"
}
with open("databias/slices/fairness_disparity.json", "w") as f:
    json.dump(fairness_stats, f, indent=2)
upload_to_gcs("databias/slices/fairness_disparity.json", "fairness_disparity.json")

print("📈 Fairness disparity metrics saved → GCS")
print(f"   Max group mean: {max_mean:.2f} | Min group mean: {min_mean:.2f}")
print(f"   Disparity ratio: {disparity_ratio:.2f}x | Difference: {disparity_diff:.2f}")

# ------------------------------------------------------
# 🔟 Alert Email if Bias Exceeds Threshold
# ------------------------------------------------------
THRESHOLD = 50.0  # you can tune this
if disparity_diff > THRESHOLD:
    msg = MIMEText(
        f"⚠️ CiteConnect Bias Alert:\n\n"
        f"Disparity Difference: {disparity_diff:.2f}\n"
        f"Disparity Ratio: {disparity_ratio:.2f}\n\n"
        f"Bias mitigation is recommended.\n"
        f"View details in: gs://{BUCKET_NAME}/{OUTPUT_PREFIX}"
    )
    msg["Subject"] = "⚠️ CiteConnect Bias Threshold Exceeded"
    msg["From"] = os.getenv("SMTP_USER", "noreply@citeconnect.ai")
    msg["To"] = os.getenv("ALERT_EMAIL", "dhikshamathan@gmail.com")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            server.send_message(msg)
        print(f"📧 Alert sent to {msg['To']}")
    except Exception as e:
        print(f"❌ Failed to send alert email: {e}")
else:
    print("✅ Fairness disparity within threshold — no alert sent.")
