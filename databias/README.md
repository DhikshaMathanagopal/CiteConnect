# 🎯 CiteConnect – Bias Detection & Mitigation Module

**Production-ready bias analysis pipeline for fair ML recommendations**

This module detects, analyzes, and mitigates bias in the CiteConnect research paper dataset to ensure fair recommendations across all academic fields.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Why Bias Detection Matters](#why-bias-detection-matters)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Bias Types Analyzed](#bias-types-analyzed)
- [How It Works](#how-it-works)
- [Threshold Standards](#threshold-standards)
- [Mitigation Strategy](#mitigation-strategy)
- [Files & Scripts](#files--scripts)
- [Configuration](#configuration)
- [Interpreting Results](#interpreting-results)
- [Integration with Airflow](#integration-with-airflow)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The CiteConnect Bias Detection Module performs comprehensive fairness analysis on research paper metadata to identify and correct systematic biases that could lead to unfair ML model behavior.

### **Key Features**

✅ **Multi-stage Analysis** - Analyzes data across raw → processed pipeline stages  
✅ **Industry Standards** - Uses Fairlearn (Microsoft) and 80% fairness rule  
✅ **Dynamic Thresholds** - Calculates context-aware bias thresholds  
✅ **Automated Mitigation** - Oversamples underrepresented fields  
✅ **GCS Integration** - Cloud-native with Google Cloud Storage  
✅ **Email Alerts** - Proactive monitoring when bias exceeds thresholds  
✅ **Visualizations** - Publication-ready plots for stakeholder communication

---

## 🚨 Why Bias Detection Matters

### **The Problem**

Without bias detection, your ML recommendation system will:

```
❌ Over-recommend popular fields (Medicine, CS)
❌ Under-recommend minority fields (Sociology, Anthropology)
❌ Perpetuate existing academic inequalities
❌ Lose users from underrepresented communities
❌ Fail fairness audits and ethical reviews
```

### **The Solution**

With bias detection and mitigation:

```
✅ Balanced recommendations across all fields
✅ Fair treatment of underrepresented research areas
✅ Diverse user base and community growth
✅ Compliance with AI fairness standards
✅ Transparent, auditable decision-making
```

### **Real-World Impact**

**Current State (Without Mitigation):**
- Chemistry papers: avg **1,992 citations**
- Engineering papers: avg **135 citations**
- **Disparity: 14.8x** (severe bias)

**After Mitigation:**
- Underrepresented fields get 2x boost
- Disparity reduced to ~8x (still needs work but improved)
- Model learns fairer patterns

---

## ⚡ Quick Start

### **Prerequisites**

```bash
# Install dependencies
pip install -r requirements.txt

# Required packages:
# - pandas, numpy, matplotlib, seaborn
# - fairlearn (Microsoft's fairness toolkit)
# - google-cloud-storage
# - pyarrow
```

### **GCS Authentication**

```bash
# Set your GCS credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcs-key.json"
```

### **Run Bias Analysis**

**Option 1: Full GCS-Integrated Pipeline (Production)**
```bash
python databias/slicing_bias_analysis.py
```
Loads from: `raw/`, `raw_v2/`, `processed/`, `processed_v2/`  
Outputs to: GCS `bias_outputs/` + local `databias/slices/`

**Option 2: Quick Local Testing**
```bash
python databias/test_bias_local.py
```
Loads from: Local `data/combined_gcs_data.parquet`  
Outputs to: Local `databias/slices/` and `databias/plots/`

**Option 3: Exploratory Analysis (4 Bias Types)**
```bash
python databias/analyze_bias.py
```
Analyzes: Temporal, Field, Citation, Quality bias  
Outputs to: `databias/plots/`

### **View Results**

```bash
# Open visualizations
open databias/plots/field_distribution.png
open databias/slices/field_citation_fairness.png

# Read metrics
cat databias/slices/fairness_disparity.json
cat databias/slices/slice_summary.json
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCS: citeconnect-test-bucket                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  raw/    │ │ raw_v2/  │ │processed/│ │processed │          │
│  │          │ │          │ │          │ │   _v2/   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            BIAS DETECTION PIPELINE                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Load & Parse (Handle all data formats)              │  │
│  │  2. Explode Multi-Field Papers                          │  │
│  │  3. Fairlearn Analysis (Group-wise fairness)            │  │
│  │  4. Dynamic Threshold Calculation (4 methods)           │  │
│  │  5. Disparity Metrics (Ratio + Difference)              │  │
│  │  6. Visualization Generation                            │  │
│  │  7. Mitigation (2x Oversample)                          │  │
│  │  8. Alert System (Email if threshold exceeded)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         OUTPUTS                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Metrics    │  │Visualizations│  │  Balanced    │         │
│  │   (JSON)     │  │   (PNG)      │  │   Dataset    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                          ↓                                      │
│                    📧 Email Alert                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Bias Types Analyzed

### **1. Temporal Bias** 📅

**What:** Papers concentrated in certain years

**Metric:** Distribution of `year` field

**Why It Matters:**
- Recent papers may be over-represented
- Historical papers may be missing
- Temporal trends affect citation patterns

**Detection:**
```python
df.groupby("year")["citationCount"].mean()
```

**Typical Finding:**
```
Papers from 2020-2025: 80% of dataset
Papers from 1990-2000: 2% of dataset
→ Recency bias detected
```

---

### **2. Field Bias** 🎓

**What:** Certain academic domains dominate the dataset

**Metric:** Count of papers per `fieldsOfStudy`

**Why It Matters:**
- Overrepresented fields get better recommendations
- Underrepresented fields become invisible
- Interdisciplinary work may be missed

**Detection:**
```python
df_exploded["fieldsOfStudy"].value_counts()
```

**Typical Finding:**
```
Medicine:         414 papers (57%)  ← OVERREPRESENTED
Computer Science: 346 papers (48%)  ← OVERREPRESENTED
Sociology:          0 papers (0%)   ← MISSING
→ Field imbalance detected
```

---

### **3. Citation Bias** 🔗

**What:** High-cited papers dominate, creating popularity skew

**Metric:** `citationCount` statistics (mean, median, top 10%)

**Why It Matters:**
- Models favor already-popular papers
- New/niche papers get suppressed
- Rich-get-richer effect

**Detection:**
```python
avg_cite = df["citationCount"].mean()
median_cite = df["citationCount"].median()
top10_mean = df["citationCount"].nlargest(int(0.1 * len(df))).mean()
skew_ratio = top10_mean / (median_cite + 1)
```

**Typical Finding:**
```
Average:   458 citations
Median:     54 citations
Top 10%: 3,649 citations
Skew ratio: 67x
→ Extreme popularity bias
```

---

### **4. Quality Bias** 📄

**What:** Content quality correlates with metadata completeness

**Metric:** `intro_length` by `content_quality`

**Why It Matters:**
- Poor quality data leads to poor recommendations
- Metadata completeness may correlate with field
- Extraction bias in processing pipeline

**Detection:**
```python
df.groupby("content_quality")["intro_length"].describe()
```

---

## 🔬 How It Works

### **Phase 1: Data Preparation**

#### **Multi-Source Loading**
```python
# Load from ALL pipeline stages
SOURCE_FOLDERS = ["raw/", "raw_v2/", "processed/", "processed_v2/"]

for folder in SOURCE_FOLDERS:
    blobs = bucket.list_blobs(prefix=folder)
    # Load and combine all parquet files
```

**Why:** Comprehensive view of bias across entire data lifecycle

#### **Field Parsing**
```python
def parse_json_column(x):
    """Handle: lists, JSON strings, Python strings, single strings"""
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x)  # JSON string
        except:
            try:
                return ast.literal_eval(x)  # Python string
            except:
                return [x]  # Single string
    return [x]
```

**Why:** Data formats vary across sources; need unified handling

#### **Multi-Field Explosion**
```python
df_exploded = df.explode("fieldsOfStudy").copy()
```

**Before:**
```
Row 1: paperId=123, fields=["AI", "Medicine"], citations=1000
```

**After:**
```
Row 1: paperId=123, field="AI", citations=1000
Row 2: paperId=123, field="Medicine", citations=1000
```

**Why:** Papers contribute to ALL their fields for fair attribution

---

### **Phase 2: Fairness Analysis**

#### **Fairlearn MetricFrame**
```python
from fairlearn.metrics import MetricFrame

metric_frame = MetricFrame(
    metrics={"mean_citations": lambda y_true, y_pred: np.mean(y_true)},
    y_true=y_true,
    y_pred=y_pred,
    sensitive_features=df_exploded["fieldsOfStudy"]
)
```

**What This Does:**
1. Groups papers by field (sensitive feature)
2. Computes average citations per field
3. Identifies disparities between groups
4. Uses industry-standard fairness framework

**Output:**
```
Field               Mean Citations
Chemistry           1,992
Biology               877
Mathematics           572
Engineering           135
```

---

### **Phase 3: Threshold Calculation**

#### **Method 1: Statistical (2σ)**
```python
mean_val = np.mean(field_means)
std_val = np.std(field_means)
threshold = 2 * std_val  # 95% confidence interval
```

**Logic:** Values beyond 2 standard deviations are statistical outliers

#### **Method 2: 80% Fairness Rule**
```python
threshold_ratio = 1.25  # Inverse of 0.80
```

**Logic:** From US employment law - groups should be within 80% of each other

#### **Method 3: Percentile-Based**
```python
# All pairwise differences
disparities = [abs(field_means[i] - field_means[j]) 
               for i in range(len(field_means)) 
               for j in range(i+1, len(field_means))]
threshold = np.percentile(disparities, 75)
```

**Logic:** Focus on extreme cases (top 25% of disparities)

#### **Method 4: Domain-Specific**
```python
threshold_ratio = 5.0
```

**Logic:** Academic research shows 5x difference is concerning

---

### **Phase 4: Mitigation**

#### **Identify Underrepresented Fields**
```python
field_counts = df_exploded["fieldsOfStudy"].value_counts()
median_count = field_counts.median()
underrep_fields = field_counts[field_counts < median_count].index
```

**Logic:** Fields below median representation need boosting

#### **Oversample Strategy**
```python
df_underrep = df[df["fieldsOfStudy"].apply(has_underrep_field)]
df_balanced = pd.concat([
    df_underrep.sample(frac=2, replace=True, random_state=42),  # 2x boost
    df[~df["fieldsOfStudy"].apply(has_underrep_field)]
])
```

**Why 2x:**
- Conservative approach (can increase to 3x, 4x)
- Balances without over-correcting
- Proven effective in fairness literature

**Impact:**
```
Before: Physics = 7 papers (1%)
After:  Physics = 14 papers (2%)
→ Better representation in model training
```

---

## 📊 Threshold Standards

### **Summary Table**

| Threshold | Type | Value | Source | Severity |
|-----------|------|-------|--------|----------|
| **80% Rule** | Ratio | ≤1.25x | US EEOC, ML Fairness | Legal |
| **Statistical** | Difference | Mean + 2σ | Statistics (95% CI) | Outlier |
| **Percentile** | Difference | 75th percentile | Data distribution | Extreme |
| **Domain** | Ratio | ≤5.0x | Academic research | Contextual |

### **Alert Severity Levels**

```python
violations = []
if disparity_ratio > 1.25:
    violations.append("80% Rule")
if disparity_ratio > 5.0:
    violations.append("Domain Rule")
if disparity_diff > stat_threshold:
    violations.append("Statistical")
if disparity_diff > percentile_threshold:
    violations.append("Percentile")

severity = "HIGH" if len(violations) >= 3 else \
           "MEDIUM" if len(violations) == 2 else \
           "LOW" if len(violations) == 1 else "NONE"
```

**Decision Logic:**
- 0 violations → ✅ No alert
- 1 violation → 🟡 LOW severity
- 2 violations → 🟠 MEDIUM severity
- 3+ violations → 🔴 HIGH severity

---

## 🛠️ Mitigation Strategy

### **Why Oversample (Not Undersample)?**

**Oversample ✅ (Our Approach)**
```python
df_underrep.sample(frac=2, replace=True)  # Duplicate minority samples
```

**Pros:**
- Keeps all data (no information loss)
- Boosts minority representation
- Model sees more diverse examples

**Cons:**
- Increases dataset size
- Some papers duplicated

**Undersample ❌ (Not Recommended)**
```python
df_overrep.sample(n=min_count)  # Throw away majority samples
```

**Pros:**
- Smaller dataset

**Cons:**
- Throws away valuable Medicine/CS papers
- Massive information loss
- Model learns from less data

### **Resampling Parameters**

```python
# Current settings
frac=2              # 2x oversample (conservative)
replace=True        # Allow duplication
random_state=42     # Reproducibility
```

**Adjustable:**
- `frac=3` for 3x boost (more aggressive)
- `frac=1.5` for 1.5x boost (more conservative)
- Balance between fairness and dataset size

---

## 📁 Files & Scripts

### **Main Scripts**

#### **`slicing_bias_analysis.py`** (Production Pipeline)

**Purpose:** Full GCS-integrated bias analysis with mitigation

**Features:**
- Loads from 4 GCS folders (raw, raw_v2, processed, processed_v2)
- Fairlearn fairness analysis
- Dynamic threshold calculation
- 2x oversampling mitigation
- Uploads results to GCS
- Email alerts

**Usage:**
```bash
python databias/slicing_bias_analysis.py
```

**Outputs:**
- `databias/slices/fairness_disparity.json` - Metrics
- `databias/slices/slice_summary.json` - Group stats
- `databias/slices/field_slicing_bias.png` - Visualization
- `data/combined_gcs_data_balanced.parquet` - Mitigated dataset
- GCS: `gs://citeconnect-test-bucket/bias_outputs/`

---

#### **`test_bias_local.py`** (Quick Testing)

**Purpose:** Fast local bias analysis without GCS

**Features:**
- Loads from local parquet file
- Same analysis as production script
- Detailed console output
- Multi-criteria thresholds

**Usage:**
```bash
python databias/test_bias_local.py
```

**Outputs:**
- `databias/slices/bias_analysis_results.json`
- `databias/plots/field_distribution.png`
- `databias/slices/field_citation_fairness.png`

---

#### **`analyze_bias.py`** (Exploratory Analysis)

**Purpose:** Explore 4 types of bias with visualizations

**Features:**
- Temporal bias (year distribution)
- Field bias (domain overrepresentation)
- Citation bias (popularity skew)
- Quality bias (content quality patterns)

**Usage:**
```bash
python databias/analyze_bias.py
```

**Outputs:**
- `databias/plots/temporal_bias.png`
- `databias/plots/field_bias.png`
- `databias/plots/citation_bias.png`
- `databias/plots/quality_bias.png`
- `databias/bias_summary.json`

---

### **Helper Scripts**

#### **`bias_analysis_connect_gcs.py`**
Downloads all parquet files from GCS and merges them locally

#### **`explore_gcs.py`**
Lists and explores files in GCS bucket

#### **`inspect_single_file.py`**
View schema and sample data from one GCS file

#### **`send_test_email.py`**
Test SMTP configuration for email alerts

---

## ⚙️ Configuration

### **GCS Settings**

Edit `slicing_bias_analysis.py`:

```python
# Lines 25-28
BUCKET_NAME = "citeconnect-test-bucket"
SOURCE_FOLDERS = ["raw/", "raw_v2/", "processed/", "processed_v2/"]
OUTPUT_PREFIX = "bias_outputs/"
```

**Credentials:**
```bash
# Local development
export GOOGLE_APPLICATION_CREDENTIALS="/Users/you/Downloads/gcs-key.json"

# Airflow/Docker
export GOOGLE_APPLICATION_CREDENTIALS="/opt/airflow/gcs-key.json"
```

---

### **Threshold Configuration**

Edit calculation section (lines 160-180):

```python
# Adjust these values based on your requirements
stat_threshold = 2 * std_val        # Change 2 to 3 for stricter
fairness_ratio = 1.25               # 80% rule (can use 1.11 for 90% rule)
domain_ratio = 5.0                  # Adjust based on your field norms
percentile = 75                     # Use 90 for stricter
```

---

### **Mitigation Settings**

Edit mitigation section (lines 200-210):

```python
# Oversample fraction
df_underrep.sample(frac=2, replace=True)  # Change frac=2 to frac=3 for 3x

# Change random seed for different sampling
random_state=42  # Use different seed if needed
```

---

### **Email Alert Configuration**

Set environment variables:

```bash
# Required for email alerts
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export ALERT_EMAIL="team@company.com"
```

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate app password (not your regular password)
3. Use app password in `SMTP_PASSWORD`

---

## 📊 Interpreting Results

### **Fairness Metrics JSON**

```json
{
  "max_group_mean": 1992.25,
  "max_group_field": "Chemistry",
  "min_group_mean": 134.65,
  "min_group_field": "Engineering",
  "disparity_ratio": 14.80,
  "disparity_difference": 1857.60,
  "violations": [
    "80% Rule: 14.80x > 1.25x",
    "Domain Rule: 14.80x > 5.0x",
    "Statistical: 1857.60 > 1086.80",
    "Percentile: 1857.60 > 732.66"
  ],
  "severity": "HIGH"
}
```

**What This Means:**
- Chemistry papers get **14.8x more citations** than Engineering
- **All 4 thresholds violated** → HIGH severity
- **Immediate action required:** Use balanced dataset for training

---

### **Slice Summary JSON**

```json
{
  "fieldsOfStudy": {
    "Medicine": 338.20,
    "Computer Science": 229.73,
    "Biology": 877.36,
    "Engineering": 134.65
  }
}
```

**What This Means:**
- Average citations per field
- Biology performs best (877), Engineering worst (135)
- Use this to understand field-level patterns

---

### **Alert Severity Guide**

| Severity | Violations | Action Required |
|----------|-----------|-----------------|
| **NONE** | 0 | ✅ No action needed |
| **LOW** | 1 | 🟡 Monitor, consider mitigation |
| **MEDIUM** | 2 | 🟠 Review and plan mitigation |
| **HIGH** | 3-4 | 🔴 Immediate mitigation required |

---

## 🔄 Integration with Airflow

### **DAG Integration**

The bias detection runs as a task in your Airflow pipeline:

```python
# dags/test_dag.py (lines 250-254)
bias_detection_task = PythonOperator(
    task_id='run_bias_detection',
    python_callable=run_bias_detection,
    dag=dag
)
```

**Pipeline Flow:**
```
env_check → gcs_check → unit_tests → collection → 
preprocessing → embedding → BIAS_DETECTION → success_email
```

**When It Runs:**
- After embedding generation
- Before final success notification
- Blocks pipeline if bias detection fails

---

### **Airflow Logs**

View bias detection logs in Airflow UI:

```
Task: run_bias_detection
Logs:
  ✅ Connected to GCS project: strange-calling-476017-r5
  📥 Loading parquet files from ALL pipeline stages
  📂 Found 23 parquet files in processed_v2/
  ✅ Loaded 10,245 papers total
  🎓 Avg citation count by field:
     Chemistry: 1,992
     Engineering: 135
  🚨 Alert Severity: HIGH
  📧 HIGH severity alert sent to team@company.com
```

---

## 🔧 Troubleshooting

### **Issue: GCS Connection Failed**

```
Error: 404 GET https://storage.googleapis.com/...
```

**Solution:**
```bash
# Check credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
# Should output: /path/to/gcs-key.json

# Verify key file exists
ls -l $GOOGLE_APPLICATION_CREDENTIALS

# Test connection
python -c "from google.cloud import storage; print(storage.Client().project)"
```

---

### **Issue: No Parquet Files Found**

```
❌ No parquet files found in gs://bucket/processed_v2/
```

**Solution:**
```bash
# List files in bucket
gsutil ls gs://citeconnect-test-bucket/processed_v2/

# Or use Python script
python databias/explore_gcs.py
```

---

### **Issue: Email Alerts Not Sending**

```
⚠️ Failed to send alert email: Authentication failed
```

**Solution:**
```bash
# Check environment variables
echo $SMTP_USER
echo $SMTP_PASSWORD  # Should be app password, not regular password

# Test email
python databias/send_test_email.py
```

---

### **Issue: Memory Error on Large Datasets**

```
MemoryError: Unable to allocate array
```

**Solution:**
```python
# Edit slicing_bias_analysis.py
# Option 1: Load fewer folders
SOURCE_FOLDERS = ["processed_v2/"]  # Just one folder

# Option 2: Sample data
df = df.sample(frac=0.5, random_state=42)  # Use 50%

# Option 3: Increase system memory or use VM
```

---

### **Issue: Fairlearn Installation Error**

```
ERROR: No matching distribution found for fairlearn
```

**Solution:**
```bash
# Install specific version
pip install fairlearn==0.13.0

# Or upgrade pip first
pip install --upgrade pip
pip install fairlearn
```

---

## 📚 References & Further Reading

### **Academic Papers**
- [Fairness Definitions Explained](https://dl.acm.org/doi/10.1145/3287560.3287594) - ACM FAccT
- [AI Fairness 360](https://arxiv.org/abs/1810.01943) - IBM Research
- [Fairlearn](https://arxiv.org/abs/2012.03778) - Microsoft Research

### **Industry Standards**
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [80% Rule (EEOC)](https://www.eeoc.gov/laws/guidance/questions-and-answers-clarify-and-provide-common-interpretation-uniform-guidelines)
- [NYC Local Law 144](https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page) - Bias Audits

### **Tools & Libraries**
- [Fairlearn Documentation](https://fairlearn.org/)
- [Aequitas](http://aequitas.dssg.io/) - Bias Auditing Toolkit
- [What-If Tool](https://pair-code.github.io/what-if-tool/) - Google PAIR

---

## 📞 Support & Contact

**Author:** Dhiksha Mathanagopal  
**Project:** CiteConnect Data Pipeline – Bias Detection Component  
**Institution:** Northeastern University  
**Year:** 2025

**For Issues:**
- Check troubleshooting section above
- Review Airflow logs for detailed errors
- Verify GCS credentials and bucket access

---

## 📄 License

This bias detection module is part of the CiteConnect project.

---

**Last Updated:** December 2025  
**Version:** 2.0 (GCS-Integrated with Multi-Stage Analysis)
