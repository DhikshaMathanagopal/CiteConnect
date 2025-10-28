# CiteConnect: Research Paper Ingestion Pipeline

## Overview

This pipeline ingests academic research papers from Semantic Scholar, extracts comprehensive metadata and full-text content (abstracts and introductions), and stores the data in a structured format for downstream processing in the CiteConnect recommendation system.

## Features

### Multi-Strategy Content Extraction
The pipeline uses a **4-tier fallback approach** to maximize intro extraction success:

1. **ArXiv HTML** (Strategy 1) - Cleanest source, best quality
2. **GROBID PDF Parsing** (Strategy 2) - ML-based structured extraction
3. **Regex PDF Extraction** (Strategy 3) - Pattern-based fallback
4. **Abstract + TLDR** (Strategy 4) - Always available fallback

This ensures **100% content coverage** while maximizing the number of full introductions extracted.

### Comprehensive Metadata Collection

The pipeline collects **30 metadata fields** per paper:

#### Identifiers
- `paperId` - Semantic Scholar unique ID
- `externalIds` - DOI, ArXiv ID, PubMed ID, etc.

#### Core Content
- `title` - Paper title
- `abstract` - Paper abstract
- `introduction` - Extracted introduction section (when available)

#### Temporal Information
- `year` - Publication year
- `publicationDate` - Full publication date (YYYY-MM-DD)

#### Authorship
- `authors` - Comma-separated author names
- `authorIds` - List of Semantic Scholar author IDs

#### Venue & Publication Type
- `venue` - Journal or conference name
- `publicationTypes` - Type(s): Journal, Conference, Review, etc.
- `publicationVenue` - Detailed venue information

#### Citation Metrics
- `citationCount` - Total citations
- `influentialCitationCount` - High-impact citations
- `referenceCount` - Number of papers cited

#### Citation Network
- `citations` - Paper IDs of papers citing this work (max 50)
- `references` - Paper IDs of papers cited by this work (max 50)

#### Topic Classification
- `fieldsOfStudy` - Broad topics (e.g., "Computer Science", "Medicine")
- `s2FieldsOfStudy` - Granular AI-tagged topics

#### Access Information
- `isOpenAccess` - Whether paper is open access
- `pdf_url` - Direct PDF URL if available

#### AI-Generated Summary
- `tldr` - One-sentence summary from Semantic Scholar

#### Extraction Metadata
- `extraction_method` - How content was extracted (`arxiv_html`, `grobid_pdf`, `regex_pdf`, `abstract_tldr`)
- `content_quality` - Quality rating (`high`, `medium`, `low`)
- `has_intro` - Boolean: full introduction extracted?
- `intro_length` - Introduction length in characters

#### Pipeline Tracking
- `status` - Pipeline status
- `fail_reason` - Reason for failure (if any)
- `scraped_at` - Timestamp of scraping

---

## Installation

### Prerequisites
- Python 3.8+
- Docker (optional, for GROBID)

### Required Dependencies

```bash
pip install pymupdf pandas requests beautifulsoup4 pyarrow
```

### Optional Dependencies (for GROBID)

```bash
# Install GROBID client
pip install grobid-client-python

# Start GROBID server (Docker required)
docker run -d -p 8070:8070 --name grobid-server lfoppiano/grobid:0.7.3

# Wait for startup
sleep 60

# Verify GROBID is running
curl http://localhost:8070/api/isalive
# Should return: true
```

### Optional: Semantic Scholar API Key

For faster rate limits (1 req/sec vs 1 req/5sec):

1. Request API key at: https://www.semanticscholar.org/product/api
2. Set environment variable:
```bash
export SEMANTIC_SCHOLAR_KEY="your-api-key-here"
```

---

## Usage

### Basic Usage

```bash
# Single search term
python ingestion.py "machine learning" --limit 10

# Multiple search terms
python ingestion.py "AI in healthcare" "drug discovery" --limit 20

# Custom output directory
python ingestion.py "transformers" --limit 50 --output data/raw

# Debug mode
python ingestion.py "deep learning" --limit 5 --debug
```

### Command-Line Arguments

```
positional arguments:
  search_terms          Search terms (space-separated)

optional arguments:
  --limit LIMIT         Papers per search term (default: 10)
  --output OUTPUT       Output directory (default: data/papers)
  --debug              Print debug information
```

---

## Pipeline Architecture

### Data Flow

```
User Query
    ↓
Semantic Scholar API (with rate limiting)
    ↓
Paper Metadata Extraction (30 fields)
    ↓
Multi-Strategy Content Extraction
    ├─→ Strategy 1: ArXiv HTML
    ├─→ Strategy 2: GROBID PDF
    ├─→ Strategy 3: Regex PDF
    └─→ Strategy 4: Abstract + TLDR
    ↓
Data Quality Validation
    ↓
Save to Parquet File
    ↓
Log Statistics & Metrics
```

### Rate Limiting

The pipeline implements intelligent rate limiting to avoid API blocks:

- **Semantic Scholar**: 1.5s (with key) or 5s (without key) between requests
- **ArXiv**: 2s between requests
- **PDF Downloads**: 2s between downloads
- **403 Retries**: 5s wait before retry with different user agent
- **Exponential Backoff**: Doubles wait time on repeated failures

---

## Output Format

### File Structure

```
data/
├── machine_learning_1729534520.parquet
├── AI_in_healthcare_1729534600.parquet
└── drug_discovery_1729534800.parquet
```

Each parquet file contains all papers from one search query with complete metadata.

### Example Output Record

```python
{
    'paperId': '204e3073870fae3d05bcbc2f6a8e263d9b72e776',
    'title': 'Attention Is All You Need',
    'abstract': 'The dominant sequence transduction models...',
    'introduction': 'Recurrent neural networks, long short-term memory...',
    'year': 2017,
    'citationCount': 89234,
    'influentialCitationCount': 12456,
    'extraction_method': 'arxiv_html',
    'content_quality': 'high',
    'has_intro': True,
    'intro_length': 3245,
    # ... 20+ more fields
}
```

---

## Performance Metrics

### Expected Success Rates

| Extraction Method | Success Rate | Quality |
|-------------------|--------------|---------|
| ArXiv HTML | 10-15% of papers | High |
| GROBID PDF | 20-30% of papers | High |
| Regex PDF | 15-25% of papers | Medium |
| Abstract + TLDR | 100% of papers | Low |

**Overall: 60-70% full intro extraction + 100% content coverage**

### Processing Time

| Papers | Without API Key | With API Key |
|--------|----------------|--------------|
| 10 papers | ~5-8 minutes | ~2-3 minutes |
| 50 papers | ~25-35 minutes | ~10-15 minutes |
| 100 papers | ~50-70 minutes | ~20-30 minutes |

---

## Known Limitations & Bias

### Data Bias

1. **Open Access Bias**: Only includes freely available papers (~30-40% of all research)
2. **Publisher Bias**: Some publishers block automated access (HTTP 403)
3. **Extraction Bias**: Papers with non-standard formats may fail intro extraction
4. **Temporal Bias**: Recent papers (2015+) have better availability
5. **Field Bias**: ArXiv-heavy topics (CS, Physics, Math) have higher success rates

### Technical Limitations

1. **GROBID**: Requires Docker service, may fail on ~30% of PDFs
2. **PDF Parsing**: Quality varies by publisher formatting
3. **Rate Limits**: Without API key, processing is slower
4. **No Paywall Access**: Cannot access subscription-only papers

All limitations are tracked via metadata fields for transparency and downstream analysis.

---

## Troubleshooting

### GROBID Not Working

```bash
# Check if GROBID is running
curl http://localhost:8070/api/isalive

# Restart GROBID
docker restart grobid-server

# Or start fresh
docker run -d -p 8070:8070 --name grobid-server lfoppiano/grobid:0.7.3
```

### Rate Limit Errors (429)

```bash
# Set API key
export SEMANTIC_SCHOLAR_KEY="your-key"

# Or reduce batch size
python ingestion.py "query" --limit 5
```

### Import Errors

```bash
# Install missing dependencies
pip install pymupdf pandas requests beautifulsoup4 pyarrow
```

---

## Data Quality Assurance

### Automated Validation

The pipeline automatically validates:
- All papers have `paperId`, `title`, and `abstract`
- Years are between 1950-2025
- Citation counts are non-negative
- Introduction length is between 200-15,000 characters

### Monitoring Metrics

Each run logs:
- Total papers processed
- Extraction success rate by method
- Content quality distribution
- Average introduction length
- Failure reasons breakdown

---

## Integration with CiteConnect Pipeline

### Next Steps After Ingestion

1. **Data Preprocessing** (`preprocessing.py`)
   - Text cleaning and normalization
   - Feature engineering (temporal, citation-based)
   - Data quality validation

2. **Embedding Generation** (`embedding_generation.py`)
   - Generate vector embeddings using sentence-transformers
   - Create combined text (title + abstract + intro)
   - Store embeddings for similarity search

3. **Vector Store Creation** (`vector_store.py`)
   - Build FAISS index for fast retrieval
   - Upload to Pinecone/Weaviate for production

4. **Citation Graph** (`graph_builder.py`)
   - Build Neo4j graph from citations/references
   - Enable network-based recommendations

---

## File Structure

```
CiteConnect/
├── ingestion.py              # Main ingestion script
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── data/
    └── papers/              # Output parquet files
        ├── machine_learning_*.parquet
        └── AI_healthcare_*.parquet
```

---

## API Documentation

### Semantic Scholar API

**Endpoint**: `https://api.semanticscholar.org/graph/v1/paper/search`

**Fields Requested**:
```
paperId, externalIds, title, abstract, year, publicationDate,
venue, publicationVenue, publicationTypes, authors,
citationCount, influentialCitationCount, referenceCount,
citations, references, fieldsOfStudy, s2FieldsOfStudy,
isOpenAccess, openAccessPdf, tldr
```

**Rate Limits**:
- Without key: 100 requests per 5 minutes
- With key: 1 request per second
---
### Notes
1. Open-access PDFs are stored and parsed; restricted PDFs are linked via metadata only.
2. This project is for academic purposes and aligns with the MLOps IE7305 course objectives.

# CiteConnect Project Structure

```
citeconnect/
├── README.md
├── requirements.txt
├── requirements-test.txt           # NEW: Testing dependencies
├── pytest.ini                      # NEW: Test configuration
├── setup.py                        # NEW: Package setup for testing
├── TESTING_PIPELINE.md            # NEW: Testing documentation
├── docker-compose.yaml
├── .env.example
├── .gitignore
├── pyproject.toml
├── dags/
│   ├── __init__.py
│   ├── simple_data_ingestion_dag.py
│   ├── complete_mlops_pipeline_dag.py
│   └── dag_utils/
│       ├── __init__.py
│       ├── notification_helpers.py
│       └── task_groups.py
├── src/
│   ├── __init__.py
│   ├── data_pipeline/
│   │   ├── __init__.py
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── semantic_scholar_client.py
│   │   │   ├── content_extractor.py
│   │   │   ├── metadata_utils.py
│   │   │   ├── processor.py
│   │   │   ├── gcs_uploader.py
│   │   │   ├── batch_ingestion.py
│   │   │   ├── arxiv_client.py
│   │   │   ├── paper_selector.py
│   │   │   └── batch_downloader.py
│   │   ├── processing/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_processor.py
│   │   │   ├── text_extractor.py
│   │   │   ├── chunking_engine.py
│   │   │   └── preprocessing_utils.py
│   │   ├── validation/
│   │   │   ├── __init__.py
│   │   │   ├── quality_checker.py
│   │   │   ├── validation_rules.py
│   │   │   ├── data_profiler.py
│   │   │   └── batch_validator.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── constants.py
│   │       ├── storage_helpers.py
│   │       ├── logging_config.py
│   │       └── error_handlers.py
│   ├── model_pipeline/
│   │   ├── __init__.py
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   ├── embedding_generator.py
│   │   │   ├── vector_store.py
│   │   │   └── similarity_search.py
│   │   ├── training/
│   │   │   ├── __init__.py
│   │   │   ├── model_trainer.py
│   │   │   ├── recommendation_engine.py
│   │   │   └── evaluation_metrics.py
│   │   └── serving/
│   │       ├── __init__.py
│   │       ├── model_server.py
│   │       └── api_endpoints.py
│   ├── deployment/
│   │   ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── gcp_setup.py
│   │   │   ├── k8s_deployer.py
│   │   │   └── terraform_configs.py
│   │   ├── containers/
│   │   │   ├── Dockerfile.data_pipeline
│   │   │   ├── Dockerfile.model_server
│   │   │   └── Dockerfile.api
│   │   └── monitoring/
│   │       ├── prometheus_config.py
│   │       ├── grafana_dashboards.py
│   │       └── alerting_rules.py
│   └── web_app/
│       ├── __init__.py
│       ├── app.py
│       ├── static/
│       ├── templates/
│       └── components/
├── tests/                          # UPDATED: Complete test structure
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures and test configuration
│   │
│   ├── unit/                      # Unit tests (147 tests)
│   │   ├── __init__.py
│   │   ├── test_semantic_scholar_client.py    # 35 tests
│   │   ├── test_content_extractor.py          # 32 tests
│   │   ├── test_metadata_utils.py             # 44 tests
│   │   ├── test_processor.py                  # 18 tests
│   │   ├── test_gcs_uploader.py              # 23 tests
│   │   └── test_setup.py                      # Setup validation tests
│   │
│   ├── integration/               # Integration tests (12 tests)
│   │   ├── __init__.py
│   │   └── test_end_to_end_pipeline.py       # Complete pipeline tests
│   │
│   ├── data_quality/              # Data quality tests (future)
│   │   ├── __init__.py
│   │   ├── test_schema_validation.py
│   │   ├── test_data_completeness.py
│   │   └── test_anomaly_detection.py
│   │
│   └── fixtures/                  # Test data and mocks
│       ├── __init__.py
│       ├── sample_papers.json
│       └── mock_responses.py
│
├── configs/
│   ├── __init__.py
│   ├── config.yaml
│   ├── selection_criteria.yaml
│   ├── model_config.yaml
│   ├── logging.yaml
│   └── deployment_config.yaml
├── scripts/
│   ├── setup_environment.sh
│   ├── install_dependencies.sh
│   ├── generate_fernet_key.py
│   ├── data_backup.py
│   └── health_check.py
├── docs/
│   ├── README.md
│   ├── SETUP.md
│   ├── API_DOCUMENTATION.md
│   ├── ARCHITECTURE.md
│   ├── diagrams/
│   └── presentations/
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── monitoring/
│       ├── prometheus.yaml
│       ├── grafana-dashboard.json
│       └── alerts.yaml
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_pdf_processing_analysis.ipynb
│   ├── 03_embedding_experiments.ipynb
│   └── 04_model_evaluation.ipynb
├── data/
│   ├── raw/
│   ├── processed/
│   ├── embeddings/
│   └── models/
├── logs/
│   └── .gitkeep
├── working_data/
│   ├── temp_pdfs/
│   ├── processing_cache/
│   └── .gitkeep
├── config/
│   ├── .gitkeep
│   ├── gcp-credentials.json
│   └── api_keys.env
└── plugins/
    ├── __init__.py
    ├── operators/
    │   ├── citeconnect_operators.py
    │   └── gcs_operators.py
    └── hooks/
        └── semantic_scholar_hook.py
```
