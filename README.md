# 🧠 CiteConnect Research Paper Ingestion Pipeline

## 🌍 Overview

The **CiteConnect Ingestion Pipeline** is a production-grade research paper ingestion system that:

- Fetches academic papers from **Semantic Scholar’s Graph API**
- Extracts **abstracts, introductions, and full metadata (30+ fields)**
- Uses a **hybrid extraction strategy**  
  → ArXiv HTML → GROBID PDF → Regex PDF → Abstract + TLDR
- Supports **parallel ingestion** (multi-threaded for speed)
- Saves `.parquet` outputs by domain (`data/healthcare`, `data/quantum`, `data/finance`)
- Automatically uploads to **Google Cloud Storage (GCS)**

It powers the data layer of **CiteConnect**, the AI-based academic recommendation system.

---

## ⚙️ 1. Project Setup

### 🪄 Step 1 — Clone the Repository


git clone https://github.com/<your_repo>/CiteConnect-datapipeline.git
cd CiteConnect-datapipeline
🧰 Step 2 — Create and Activate a Virtual Environment

python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
🧩 Step 3 — Install Dependencies

pip install -r requirements.txt
If requirements.txt is not available:

pip install requests pandas beautifulsoup4 pymupdf pyarrow grobid-client-python google-cloud-storage
🧑‍🔬 Step 4 — Start the GROBID Server (for PDF Parsing)
GROBID is required for high-quality introduction extraction.

Run this (Docker required):


docker run -d -p 8070:8070 --name grobid-server lfoppiano/grobid:0.7.3
Verify it’s active:

curl http://localhost:8070/api/isalive
# Expected response: true
🔑 Step 5 — Set Up API Keys and Cloud Credentials
a. Semantic Scholar API Key (optional, for faster rate limits)

export SEMANTIC_SCHOLAR_KEY="your_api_key_here"
b. Google Cloud Storage Credentials
Provide your service account JSON key:

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account.json"
Example:
export GOOGLE_APPLICATION_CREDENTIALS="/Users/yourname/Downloads/citeconnect-key.json"
📂 2. Folder Structure
arduino

CiteConnect-datapipeline/
│
├── ingestion.py
├── utils/
│   └── storage_helpers.py          # contains upload_to_gcs()
├── data/
│   ├── healthcare/
│   ├── quantum/
│   ├── finance/
│   └── general/
└── venv/
🚀 3. How the Pipeline Works
Step 1 — Query Semantic Scholar
Each search term triggers a call to the Semantic Scholar Graph API:
https://api.semanticscholar.org/graph/v1/paper/search
It retrieves:
Metadata (title, year, authors, citations)
Abstract
PDF URLs (if open-access)
Step 2 — Hybrid Content Extraction
The system follows a 4-tier fallback for robust introduction extraction:
Priority	Strategy	Description	Quality
1️⃣	ArXiv HTML	Extracts directly from ArXiv’s clean HTML pages	High
2️⃣	GROBID PDF	ML-based extraction from PDFs via Docker	High
3️⃣	Regex PDF	Text pattern matching from PDF	Medium
4️⃣	Abstract + TLDR	Guaranteed fallback text	Low

Every paper has at least one extractable text segment.

Step 3 — Metadata Schema (30+ Fields)
Each record contains full metadata for downstream processing.

Category	Fields
Identifiers	paperId, externalIds
Core Content	title, abstract, introduction
Temporal	year, publicationDate
Authors	authors, authorIds
Venue	venue, publicationTypes, publicationVenue
Citation Metrics	citationCount, influentialCitationCount, referenceCount
Citation Network	citations, references
Topics	fieldsOfStudy, s2FieldsOfStudy
Access	isOpenAccess, pdf_url
Summary	tldr
Extraction Info	extraction_method, content_quality, intro_length
Pipeline Info	status, fail_reason, scraped_at, search_term

Step 4 — Save to .parquet
Each query result is saved as:

php-template
Copy code
data/<domain>/<search_term>_<timestamp>.parquet
Example:
data/finance/AI_in_finance_1761259310.parquet
Step 5 — Upload to Google Cloud Storage (GCS)
After saving locally, the file is uploaded automatically to your GCS bucket:
php-template

gs://citeconnect-processed-parquet/<domain>/<filename>.parquet
Example:
arduino
Copy code
gs://citeconnect-processed-parquet/finance/AI_in_finance_1761259310.parquet
🧪 4. Running the Pipeline
🩺 Healthcare Example
python ingestion.py "AI in healthcare" "Deep learning in radiology" --limit 100 --output data/healthcare
💰 Finance Example (for your teammate)
python ingestion.py \
"AI in finance" "Stock market prediction" "Financial forecasting" \
"Machine learning for trading" "Portfolio optimization" \
"Risk modeling" "Quantitative finance" "Cryptocurrency analytics" \
"Algorithmic trading" "Blockchain economics" \
--limit 100 --output data/finance
✅ This will:
Fetch ~100 papers per query
Save outputs under data/finance
Upload all .parquet files to your GCS bucket
Running multiple batches easily yields 3000+ total papers.

📊 5. Checking Outputs
a. View Parquet Files Locally
import pandas as pd
df = pd.read_parquet("data/finance/AI_in_finance_1761259310.parquet")
print(df.head(3))
b. Verify Uploads in GCS
gsutil ls gs://citeconnect-processed-parquet/finance/
⚡ 6. Advanced Options
Option	Description	Example
--limit	Papers per search term	--limit 200
--output	Output directory path	--output data/finance
Multiple terms	Process many queries at once	"AI in finance" "blockchain economics"
Threads	Parallelism (max 5)	Managed automatically

🧩 7. Error Handling
Error	Cause	Resolution
429 Too Many Requests	API limit exceeded	Add API key / wait for backoff
403 Forbidden (PDF)	Publisher restriction	Retries with different headers
GROBID not responding	Docker stopped	docker start grobid-server
Upload to GCS failed	No credentials	Set environment variable with JSON key
datetime.utcnow() warning	Python 3.13 deprecation	Safe to ignore

🧭 8. Summary Command (Finance Domain)
Use this one-liner to fetch large batches of Finance research papers:

python ingestion.py \
"AI in finance" "Stock market prediction" "Financial forecasting" \
"Machine learning for trading" "Portfolio optimization" \
"Risk modeling" "Quantitative finance" "Cryptocurrency analytics" \
"Algorithmic trading" "Blockchain economics" \
--limit 100 --output data/finance
💾 Local output: data/finance/*.parquet
☁️ GCS upload: gs://citeconnect-processed-parquet/finance/*.parquet

🔍 9. Example Log Output
[API] Query='AI in finance' Attempt=1 (waiting 5.0s)
[API] Retrieved 100 papers for 'AI in finance'
✅ GROBID server detected and ready
📄 Processing paper 1/100: Deep Learning for Financial Risk Prediction
✅ Regex extraction successful (8432 chars)
✅ Saved 100 records → data/finance/AI_in_finance_1761259310.parquet
📤 Uploaded → gs://citeconnect-processed-parquet/finance/AI_in_finance_1761259310.parquet
✅ Completed ingestion for: AI in finance
