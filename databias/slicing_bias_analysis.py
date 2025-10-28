"""
databias/slicing_bias_analysis.py
--------------------------------
Performs data slicing on CiteConnect dataset using Fairlearn + Pandas.
Detects subgroup bias by year, field, and content quality.
"""

import pandas as pd
import numpy as np
from fairlearn.metrics import MetricFrame
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

# ======================================================
# 1. Load data
# ======================================================
df = pd.read_parquet("data/combined_gcs_data.parquet")
print(f"✅ Loaded {len(df)} papers for slicing analysis")

# Clean numeric + categorical columns
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["citationCount"] = pd.to_numeric(df["citationCount"], errors="coerce").fillna(0)
df["intro_length"] = pd.to_numeric(df["intro_length"], errors="coerce").fillna(0)
df["fieldsOfStudy"] = df["fieldsOfStudy"].astype(str)
df["content_quality"] = df["content_quality"].astype(str)

os.makedirs("databias/slices", exist_ok=True)

# ======================================================
# 2. Group-wise slicing summaries
# ======================================================
slices = {
    "year": df.groupby("year")["citationCount"].mean().to_dict(),
    "fieldsOfStudy": df.groupby("fieldsOfStudy")["citationCount"].mean().to_dict(),
    "content_quality": df.groupby("content_quality")["intro_length"].mean().to_dict(),
}

with open("databias/slices/slice_summary.json", "w") as f:
    json.dump(slices, f, indent=2)
print("📊 Saved slice summaries → databias/slices/slice_summary.json")

# ======================================================
# 3. Fairlearn MetricFrame – group fairness view
# ======================================================
# Clean numeric target
df["citationCount"] = pd.to_numeric(df["citationCount"], errors="coerce").fillna(0)
df["fieldsOfStudy"] = df["fieldsOfStudy"].astype(str)

# MetricFrame requires numeric arrays
y_true = df["citationCount"].to_numpy().astype(float)
y_pred = df["citationCount"].to_numpy().astype(float)
sensitive = df["fieldsOfStudy"].to_numpy()

metric_frame = MetricFrame(
    metrics={"mean_citations": lambda y_true, y_pred: np.mean(y_true)},
    y_true=y_true,
    y_pred=y_pred,
    sensitive_features=sensitive
)

fairness_df = metric_frame.by_group.sort_values("mean_citations", ascending=False)
print("\n🎓 Avg citation count by field:")
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
plt.savefig("databias/slices/field_slicing_bias.png")
plt.close()


# ======================================================
# 4. Simple mitigation: re-sample low-representation fields
# ======================================================
field_counts = df["fieldsOfStudy"].value_counts()
median_count = field_counts.median()
underrep = field_counts[field_counts < median_count].index

df_balanced = pd.concat([
    df[df["fieldsOfStudy"].isin(underrep)].sample(frac=2, replace=True, random_state=42),
    df[~df["fieldsOfStudy"].isin(underrep)]
])

print(f"\n⚖️ After mitigation: {len(df_balanced)} samples (was {len(df)})")
df_balanced.to_parquet("data/combined_gcs_data_balanced.parquet", index=False)
print("💾 Saved mitigated dataset → data/combined_gcs_data_balanced.parquet")

# ======================================================
# 5. Compute Fairness Disparity Metrics
# ======================================================
max_group = fairness_df["mean_citations"].max()
min_group = fairness_df["mean_citations"].min()
disparity_ratio = max_group / (min_group + 1e-6)
disparity_diff = max_group - min_group

bias_report = {
    "max_group_mean": float(max_group),
    "min_group_mean": float(min_group),
    "disparity_ratio": float(disparity_ratio),
    "disparity_difference": float(disparity_diff)
}

with open("databias/slices/fairness_disparity.json", "w") as f:
    json.dump(bias_report, f, indent=2)

print("\n📈 Fairness disparity metrics saved → databias/slices/fairness_disparity.json")
print(json.dumps(bias_report, indent=2))
