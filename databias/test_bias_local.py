"""
Test script to run bias analysis on local data
Simplified version without GCS dependencies
"""

import os
import pandas as pd
import numpy as np
from fairlearn.metrics import MetricFrame
import matplotlib.pyplot as plt
import seaborn as sns
import json
import ast

# ------------------------------------------------------
# 1️⃣ Helper to Parse JSON/List Columns
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
# 2️⃣ Load Local Data
# ------------------------------------------------------
DATA_PATH = "data/combined_gcs_data.parquet"
print(f"📂 Loading data from {DATA_PATH}...")

try:
    df = pd.read_parquet(DATA_PATH)
    print(f"✅ Loaded {len(df)} papers for bias analysis\n")
    print(f"📊 Columns available: {df.columns.tolist()}\n")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    exit(1)

# ------------------------------------------------------
# 3️⃣ Clean and Parse Data
# ------------------------------------------------------
print("🧹 Cleaning data...")

# Clean numeric fields
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["citationCount"] = pd.to_numeric(df["citationCount"], errors="coerce").fillna(0)

# Check if intro_length exists
if "intro_length" in df.columns:
    df["intro_length"] = pd.to_numeric(df["intro_length"], errors="coerce").fillna(0)
else:
    print("⚠️  'intro_length' column not found, skipping")

# Parse fieldsOfStudy as a list
if "fieldsOfStudy" in df.columns:
    df["fieldsOfStudy"] = df["fieldsOfStudy"].apply(parse_json_column)
    print("✅ Parsed fieldsOfStudy column")
else:
    print("❌ 'fieldsOfStudy' column not found!")
    exit(1)

# Check content_quality
if "content_quality" in df.columns:
    df["content_quality"] = df["content_quality"].astype(str)
else:
    print("⚠️  'content_quality' column not found, skipping")

os.makedirs("databias/slices", exist_ok=True)
os.makedirs("databias/plots", exist_ok=True)

# ------------------------------------------------------
# 4️⃣ Quick Data Overview
# ------------------------------------------------------
print("\n" + "="*60)
print("📊 DATA OVERVIEW")
print("="*60)
print(f"Total papers: {len(df)}")
print(f"Date range: {df['year'].min():.0f} - {df['year'].max():.0f}")
print(f"Citation count: avg={df['citationCount'].mean():.1f}, median={df['citationCount'].median():.1f}")
print(f"Max citations: {df['citationCount'].max():.0f}")

# ------------------------------------------------------
# 5️⃣ Explode fieldsOfStudy for Proper Multi-Field Analysis
# ------------------------------------------------------
print("\n" + "="*60)
print("💥 EXPLODING MULTI-FIELD PAPERS")
print("="*60)

df_exploded = df.explode("fieldsOfStudy").copy()

# Clean up fields: remove empty, NaN, and list-like strings
df_exploded["fieldsOfStudy"] = df_exploded["fieldsOfStudy"].astype(str)
df_exploded = df_exploded[df_exploded["fieldsOfStudy"].str.len() > 0]
df_exploded = df_exploded[df_exploded["fieldsOfStudy"] != "nan"]
df_exploded = df_exploded[df_exploded["fieldsOfStudy"] != "None"]
# Remove fields that start with '[' (these are unparsed list strings)
df_exploded = df_exploded[~df_exploded["fieldsOfStudy"].str.startswith("[")]

print(f"✅ Exploded to {len(df_exploded)} field-paper pairs (cleaned)")
print(f"   Before: {len(df)} papers")
print(f"   After:  {len(df_exploded)} field assignments")

# ------------------------------------------------------
# 6️⃣ Field Distribution Analysis
# ------------------------------------------------------
print("\n" + "="*60)
print("🎓 FIELD DISTRIBUTION ANALYSIS")
print("="*60)

field_counts = df_exploded["fieldsOfStudy"].value_counts()
print(f"\nTop 15 fields by paper count:")
print(field_counts.head(15))

plt.figure(figsize=(10, 6))
sns.barplot(
    x=field_counts.head(15).values,
    y=field_counts.head(15).index,
    palette="viridis"
)
plt.title("Top 15 Most Common Research Fields")
plt.xlabel("Number of Papers")
plt.ylabel("Field of Study")
plt.tight_layout()
plt.savefig("databias/plots/field_distribution.png", bbox_inches="tight", dpi=100)
print("\n📊 Saved field distribution plot → databias/plots/field_distribution.png")

# ------------------------------------------------------
# 7️⃣ Fairness Analysis with Fairlearn
# ------------------------------------------------------
print("\n" + "="*60)
print("⚖️  FAIRNESS ANALYSIS (Citation Equity by Field)")
print("="*60)

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
print(f"\n📈 Average citation count by field (Top 15):")
print(fairness_df.head(15))

# Visualization
plt.figure(figsize=(10, 6))
sns.barplot(
    x=fairness_df.head(15)["mean_citations"].values,
    y=fairness_df.head(15).index,
    palette="crest"
)
plt.title("Average Citation Count by Field of Study")
plt.xlabel("Mean Citations")
plt.ylabel("Field of Study")
plt.tight_layout()
plt.savefig("databias/slices/field_citation_fairness.png", bbox_inches="tight", dpi=100)
print("📊 Saved fairness plot → databias/slices/field_citation_fairness.png")

# ------------------------------------------------------
# 8️⃣ Disparity Metrics
# ------------------------------------------------------
print("\n" + "="*60)
print("📊 FAIRNESS DISPARITY METRICS")
print("="*60)

max_mean = fairness_df["mean_citations"].max()
min_mean = fairness_df["mean_citations"].min()
disparity_ratio = (max_mean / (min_mean + 1e-6)) if min_mean > 0 else np.inf
disparity_diff = max_mean - min_mean

print(f"\n🔝 Highest-cited field: {fairness_df.index[0]}")
print(f"   Average citations: {max_mean:.2f}")
print(f"\n🔻 Lowest-cited field: {fairness_df.index[-1]}")
print(f"   Average citations: {min_mean:.2f}")
print(f"\n⚠️  DISPARITY METRICS:")
print(f"   Ratio:      {disparity_ratio:.2f}x")
print(f"   Difference: {disparity_diff:.2f} citations")

# Calculate thresholds
field_means = fairness_df["mean_citations"].values
mean_val = np.mean(field_means)
std_val = np.std(field_means)
stat_threshold = 2 * std_val

Q1 = np.percentile(field_means, 25)
Q3 = np.percentile(field_means, 75)
IQR = Q3 - Q1

# All pairwise disparities
disparities = []
for i in range(len(field_means)):
    for j in range(i+1, len(field_means)):
        disparities.append(abs(field_means[i] - field_means[j]))
percentile_threshold = np.percentile(disparities, 75) if disparities else 100

print(f"\n📐 CALCULATED THRESHOLDS:")
print(f"   Statistical (2σ):        {stat_threshold:.2f} citations")
print(f"   80% Fairness Rule:       1.25x ratio")
print(f"   Percentile (75th):       {percentile_threshold:.2f} citations")
print(f"   Domain-specific:         5.0x ratio")

# Check violations
violations = []
if disparity_ratio > 1.25:
    violations.append(f"80% Rule: {disparity_ratio:.2f}x > 1.25x")
if disparity_ratio > 5.0:
    violations.append(f"Domain Rule: {disparity_ratio:.2f}x > 5.0x")
if disparity_diff > stat_threshold:
    violations.append(f"Statistical: {disparity_diff:.2f} > {stat_threshold:.2f}")
if disparity_diff > percentile_threshold:
    violations.append(f"Percentile: {disparity_diff:.2f} > {percentile_threshold:.2f}")

severity = "HIGH" if len(violations) >= 3 else "MEDIUM" if len(violations) == 2 else "LOW" if len(violations) == 1 else "NONE"

print(f"\n🚨 ALERT STATUS: {severity}")
if violations:
    print(f"   Violations ({len(violations)}):")
    for v in violations:
        print(f"   • {v}")
else:
    print("   ✅ All fairness thresholds within acceptable range")

# ------------------------------------------------------
# 9️⃣ Mitigation Analysis
# ------------------------------------------------------
print("\n" + "="*60)
print("🛠️  BIAS MITIGATION RECOMMENDATIONS")
print("="*60)

median_count = field_counts.median()
underrep_fields = set(field_counts[field_counts < median_count].index)
overrep_fields = set(field_counts[field_counts >= median_count].index)

print(f"\n📊 Field representation (median: {median_count:.0f} papers):")
print(f"   Overrepresented fields:   {len(overrep_fields)}")
print(f"   Underrepresented fields:  {len(underrep_fields)}")

print(f"\n🔻 Most underrepresented fields:")
for field in field_counts.tail(10).index[::-1]:
    count = field_counts[field]
    print(f"   {field:30s} {count:3.0f} papers")

# ------------------------------------------------------
# 🔟 Save Results
# ------------------------------------------------------
print("\n" + "="*60)
print("💾 SAVING RESULTS")
print("="*60)

results = {
    "dataset_summary": {
        "total_papers": int(len(df)),
        "total_field_assignments": int(len(df_exploded)),
        "unique_fields": int(len(field_counts)),
        "year_range": [int(df["year"].min()), int(df["year"].max())],
        "avg_citations": float(df["citationCount"].mean()),
        "median_citations": float(df["citationCount"].median())
    },
    "fairness_metrics": {
        "max_group_mean": float(max_mean),
        "max_group_field": str(fairness_df.index[0]),
        "min_group_mean": float(min_mean),
        "min_group_field": str(fairness_df.index[-1]),
        "disparity_ratio": float(disparity_ratio),
        "disparity_difference": float(disparity_diff)
    },
    "thresholds": {
        "statistical_2sigma": float(stat_threshold),
        "fairness_80_rule": 1.25,
        "percentile_75th": float(percentile_threshold),
        "domain_specific": 5.0
    },
    "alert": {
        "severity": severity,
        "violations": violations,
        "triggered": len(violations) > 0
    },
    "mitigation": {
        "underrepresented_fields": len(underrep_fields),
        "overrepresented_fields": len(overrep_fields),
        "median_field_count": float(median_count)
    }
}

output_path = "databias/slices/bias_analysis_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ Results saved → {output_path}")
print(f"✅ Visualizations saved → databias/plots/ and databias/slices/")

print("\n" + "="*60)
print("✅ BIAS ANALYSIS COMPLETE!")
print("="*60)

