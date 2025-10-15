# CiteConnect: Research Paper Metadata & Introduction Extraction Pipeline

This repository contains the **CiteConnect data pipeline** — a modular ingestion system that fetches research papers from open sources (Semantic Scholar, CORE, OpenAlex, Unpaywall, PubMed Central), resolves open-access PDFs, and extracts structured text sections (Abstract, Introduction) using **GROBID** for downstream retrieval and RAG applications.

## Overview

CiteConnect automates:
1. **Metadata Collection** — using the [Semantic Scholar API](https://api.semanticscholar.org/), [CORE API](https://core.ac.uk/services/api/), and [OpenAlex API](https://docs.openalex.org/).
2. **PDF Resolution** — via Unpaywall, PMC mirrors, CORE, OpenAlex, CrossRef, and direct open-access URLs.
3. **Text Extraction** — using [GROBID](https://github.com/ourresearch/grobid) to parse PDFs into structured TEI XML and extract Introduction and Abstract.
4. **Data Storage** — saving results to compressed `.parquet` files, ready for vector database ingestion and retrieval.

## Project Structure

```
src/
└── data_pipeline/
    ├── ingestion/
    │   ├── stream_grobid.py             # Main continuous ingestion pipeline
    ├── clients/
    │   ├── semantic_scholar_client.py   # Metadata fetcher (Semantic Scholar)
    │   ├── pdf_resolver.py              # Robust PDF URL resolver (Unpaywall, OpenAlex, CORE, etc.)
    │   ├── grobid_client.py             # Handles PDF → TEI XML → Section extraction
    └── utils/
        ├── http_utils.py                # Shared safe_get with retry, rate limit, and logging
        ├── deduplication.py             # Title-based deduplication utilities
data/
└── parquet_corpus/                      # Output folder for .parquet results
```

## Prerequisites

- **Python 3.10+**
- **Docker** (for running GROBID)
- Required environment variables:

```
# .env file
SEMANTIC_SCHOLAR_KEY=<your_semantic_key>
CORE_API_KEY=<your_core_key>
UNPAYWALL_EMAIL=yourname@northeastern.edu
PDF_CACHE_PATH=.cache/pdf_cache.json
```

You can also set them inline before running:
```
export SEMANTIC_SCHOLAR_KEY="your_key"
export UNPAYWALL_EMAIL="yourname@northeastern.edu"
```

## Setup

```
git clone https://github.com/DhikshaMathanagopal/CiteConnect.git
cd CiteConnect
pip install -r requirements.txt

docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0

curl -I http://localhost:8070/api/isalive
```

## Run the Pipeline

```
python -m src.data_pipeline.ingestion.stream_grobid   --query "Drug response prediction"   --grobid http://localhost:8070   --limit 20   --workers 4   --out_dir data/parquet_corpus
```

### Output:
- `data/parquet_corpus/drug_response_prediction.parquet` → structured metadata + intro text  
- `data/parquet_corpus/failures_drug_response_prediction.json` → diagnostic logs for failed papers  

## How PDF Resolution Works

The pipeline attempts multiple resolution strategies:
1. Direct `openAccessPdf.url` from Semantic Scholar  
2. PubMed Central (by PMCID)  
3. [Unpaywall](https://unpaywall.org/products/api)  
4. [CORE API](https://core.ac.uk/services/api/)  
5. [OpenAlex](https://docs.openalex.org/)  
6. [CrossRef](https://api.crossref.org/)  
7. Headless browser fallback (via Playwright, if installed)

It also includes special handling for:
- **bioRxiv/medRxiv** (`?download=true`)
- **MDPI** PDFs (`?download=1`)
- **OUP, PeerJ** domain-specific restrictions
- **Caching** of successful DOI → PDF mappings in `.cache/pdf_cache.json`

## Data for Retrieval

Each `.parquet` file can be directly loaded into a vector database such as FAISS, Chroma, or Milvus for downstream **RAG pipelines**.

Example:

```python
import pandas as pd
df = pd.read_parquet("data/parquet_corpus/drug_response_prediction.parquet")
df = df[df.status == "ok"]
texts = df["introduction"].dropna().tolist()
```

## Common Issues

| Problem | Cause | Solution |
|----------|--------|-----------|
| `403 Forbidden` | Publisher blocks non-browser requests | Enable browser fallback |
| `429 Too Many Requests` | API rate limit | Add delay or rotate API key |
| `500 BAD_INPUT_DATA` | Broken PDF | Skip automatically |
