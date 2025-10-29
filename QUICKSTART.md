# CiteConnect: Preprocessing and Embedding Documentation

**Version**: 1.0.0  
**Last Updated**: November 2024  
**Module**: Data Preprocessing & Embedding Generation Pipeline

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Preprocessing Pipeline](#3-preprocessing-pipeline)
4. [Embedding Generation](#4-embedding-generation)
5. [Supported Providers](#5-supported-providers)
6. [Configuration](#6-configuration)
7. [Quick Start Guide](#7-quick-start-guide)
8. [API Reference](#8-api-reference)
9. [Usage Examples](#9-usage-examples)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

### 1.1 Purpose

The preprocessing and embedding pipeline transforms raw academic paper text into searchable vector embeddings for semantic similarity search and intelligent recommendations.

### 1.2 Pipeline Stages

1. **Text Cleaning**: Normalize and clean raw paper text
2. **Chunking**: Split text into semantic segments with overlap
3. **Metadata Enrichment**: Add paper-level metadata to chunks
4. **Embedding Generation**: Create vector representations
5. **Storage & Indexing**: Save embeddings for fast retrieval

### 1.3 Key Features

- **Multi-Provider Support**: Local (Sentence-Transformers), Weaviate, OpenAI
- **Intelligent Chunking**: 512 tokens with 50-token overlap
- **Batch Processing**: Configurable batch sizes for optimal performance
- **Automatic Persistence**: Auto-save embeddings after generation
- **Production Ready**: 85%+ test coverage, comprehensive error handling

---

## 2. System Architecture

### 2.1 Data Flow
```
┌─────────────┐
│  Raw Papers │ (GCS Parquet)
└──────┬──────┘
       │
       ↓
┌─────────────────────┐
│  Text Preprocessing │
│  • Clean text       │
│  • Normalize        │
│  • Remove noise     │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│   Text Chunking     │
│  • Split 512 tokens │
│  • 50 token overlap │
│  • Keep sentences   │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Metadata Enrichment │
│  • Paper metadata   │
│  • Citation info    │
│  • Author data      │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ Embedding Generation│
│  • Local/Weaviate   │
│  • OpenAI           │
│  • Batch process    │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│  Vector Storage     │
│  • Local pickle     │
│  • Weaviate DB      │
│  • Search index     │
└─────────────────────┘
```

### 2.2 Component Structure
```
src/DataPipeline/
├── preprocessing/
│   ├── text_cleaner.py         # Text normalization
│   ├── chunker.py              # Text segmentation
│   └── metadata_enricher.py    # Metadata addition
│
└── embeddings/
    ├── config.py               # Configuration management
    ├── embed_generator.py      # Provider abstraction
    ├── local_embedder.py       # Local implementation
    ├── openai_embedder.py      # OpenAI implementation
    └── vector_store.py         # Weaviate integration
```

---

## 3. Preprocessing Pipeline

### 3.1 Text Cleaner

**Purpose**: Normalize and clean academic paper text for optimal embedding quality.

**Operations**:
- Remove extra whitespace and newlines
- Normalize unicode characters
- Fix common OCR errors
- Remove special characters
- Preserve LaTeX equations

**Usage**:
```python
from src.DataPipeline.preprocessing.text_cleaner import TextCleaner

cleaner = TextCleaner()
clean_text = cleaner.clean(raw_text)
```

### 3.2 Chunker

**Purpose**: Split long documents into semantic chunks with overlap for context preservation.

**Parameters**:
- `chunk_size`: 512 tokens (default)
- `chunk_overlap`: 50 tokens (default)
- `preserve_sentences`: True (keeps sentences intact)

**Chunking Strategy**:
```
Original: [--------------------100 tokens--------------------]

chunk_size=40, overlap=10:

Chunk 0: [--------40--------]
                    [overlap]
Chunk 1:              [--------40--------]
                                [overlap]
Chunk 2:                        [--------40--------]
```

**Usage**:
```python
from src.DataPipeline.preprocessing.chunker import Chunker

chunker = Chunker(chunk_size=512, chunk_overlap=50)
chunks = chunker.chunk_text(text, paper_id="paper1")
```

**Output Format**:
```python
{
    'chunk_id': 'paper1_chunk_0',
    'paper_id': 'paper1',
    'text': 'chunk content...',
    'position': 0,
    'token_count': 512
}
```

### 3.3 Metadata Enricher

**Purpose**: Add paper-level metadata to each chunk for enhanced search and filtering.

**Enriched Fields**:
```python
{
    # Chunk-specific
    'chunk_id': 'paper1_chunk_0',
    'position': 0,
    'token_count': 512,
    'text': 'chunk content...',
    
    # Paper metadata
    'paper_id': 'paper1',
    'paper_title': 'Deep Learning Survey',
    'paper_year': 2023,
    'citation_count': 45,
    'authors': ['Smith, J.', 'Doe, A.'],
    'venue': 'NeurIPS'
}
```

**Usage**:
```python
from src.DataPipeline.preprocessing.metadata_enricher import MetadataEnricher

enricher = MetadataEnricher()
enriched_chunks = enricher.enrich_chunks(chunks, paper_metadata)
```

### 3.4 Complete Preprocessing Example
```python
from src.DataPipeline.preprocessing.text_cleaner import TextCleaner
from src.DataPipeline.preprocessing.chunker import Chunker
from src.DataPipeline.preprocessing.metadata_enricher import MetadataEnricher

# Initialize
cleaner = TextCleaner()
chunker = Chunker(chunk_size=512, chunk_overlap=50)
enricher = MetadataEnricher()

# Step 1: Clean
clean_text = cleaner.clean(raw_paper_text)

# Step 2: Chunk
chunks = chunker.chunk_text(clean_text, paper_id="paper1")

# Step 3: Enrich
enriched_chunks = enricher.enrich_chunks(chunks, paper_metadata)

# Result: Ready for embedding
print(f"Created {len(enriched_chunks)} enriched chunks")
```

---

## 4. Embedding Generation

### 4.1 Embedding Generator

**Purpose**: Provider-agnostic embedding generation with automatic batching.

**Features**:
- Supports multiple providers (local/weaviate/openai)
- Automatic batch processing
- Progress tracking and logging
- Comprehensive error handling

**Usage**:
```python
from src.DataPipeline.embeddings.embed_generator import EmbeddingGenerator

generator = EmbeddingGenerator(provider='local')
results = generator.embed_chunks(chunks, show_progress=True)
```

**Methods**:

| Method | Description | Returns |
|--------|-------------|---------|
| `embed_chunks()` | Generate embeddings for chunk list | `List[EmbeddingResult]` |
| `embed_single()` | Generate embedding for single text | `List[float]` or `None` |
| `search()` | Find similar chunks | `List[Dict]` |

### 4.2 Local Embedder

**Purpose**: Sentence-transformers implementation for local embedding generation.

**Features**:
- No external dependencies (no Docker/API)
- Automatic model download and caching
- In-memory cosine similarity search
- Pickle-based persistence
- GPU acceleration support

**Usage**:
```python
from src.DataPipeline.embeddings.local_embedder import LocalEmbedder

# Initialize
embedder = LocalEmbedder()

# Generate embeddings
results = embedder.embed_chunks(chunks, show_progress=True)

# Search
matches = embedder.search("machine learning", limit=5)

# Get statistics
stats = embedder.get_stats()
```

**Methods**:

| Method | Description | Returns |
|--------|-------------|---------|
| `embed_chunks()` | Generate and store embeddings | `List[Dict]` |
| `search()` | Cosine similarity search | `List[Dict]` |
| `save()` | Save embeddings to disk | `None` |
| `load()` | Load embeddings from disk | `None` |
| `get_stats()` | Get database statistics | `Dict` |

**Search Result Format**:
```python
{
    "chunk_id": "paper1_chunk_0",
    "paper_id": "paper1",
    "text": "Machine learning is...",
    "paper_title": "Deep Learning Survey",
    "paper_year": 2023,
    "citation_count": 45,
    "similarity": 0.867,      # 0.0 to 1.0
    "distance": 0.133,        # 1 - similarity
    "position": 0
}
```

### 4.3 Weaviate Vector Store

**Purpose**: Production-grade vector database integration with automatic vectorization.

**Features**:
- Built-in text2vec-transformers
- Automatic schema management
- Batch insertion with error handling
- Advanced filtering capabilities
- Real-time updates

**Usage**:
```python
from src.DataPipeline.embeddings.vector_store import WeaviateStore

# Initialize
store = WeaviateStore()

# Add chunks
store.add_chunks(chunks)

# Search
results = store.search("deep learning", limit=10)

# Search with filters
results = store.search(
    query="machine learning",
    limit=10,
    filters={'paper_year': 2023}
)
```

**Schema**:
```python
Collection: PaperChunks
Properties:
  - chunk_id: TEXT
  - paper_id: TEXT
  - text: TEXT
  - position: INT
  - token_count: INT
  - paper_title: TEXT
  - paper_year: INT
  - citation_count: INT
```

---

## 5. Supported Providers

### 5.1 Provider Comparison

| Feature | Local | Weaviate | OpenAI |
|---------|-------|----------|--------|
| **Setup** | Easy | Medium | Easy |
| **Cost** | Free | Free/Paid | Paid ($0.02/1M tokens) |
| **Scale** | <100K papers | 100K+ papers | Unlimited |
| **Privacy** | Complete | Complete | Limited |
| **Speed** | Fast | Very Fast | Medium |
| **Dimensions** | 384-768 | 768 | 1536 |
| **Offline** | Yes | Yes | No |

### 5.2 Provider Details

#### Local Provider (Default)
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Storage**: Local pickle file
- **Best For**: Development, testing, small datasets
- **Pros**: Free, private, no API keys
- **Cons**: Limited scaling, single machine

#### Weaviate Provider
- **Model**: Built-in text2vec-transformers
- **Storage**: Weaviate vector database
- **Best For**: Production, large datasets
- **Pros**: Scalable, advanced filtering, production-ready
- **Cons**: Requires Docker, more complex setup

#### OpenAI Provider
- **Model**: text-embedding-3-small (1536 dimensions)
- **Storage**: External (custom implementation)
- **Best For**: High quality, low volume
- **Pros**: High quality, no local compute
- **Cons**: API costs, rate limits, requires internet

### 5.3 Selection Guide

**Choose Local if**:
- Development or testing
- Dataset < 100K papers
- Privacy is critical
- No budget for infrastructure

**Choose Weaviate if**:
- Production deployment
- Dataset > 100K papers
- Need advanced filtering
- High availability required

**Choose OpenAI if**:
- Need highest quality
- Low volume usage
- Limited local compute
- Rapid prototyping

---

## 6. Configuration

### 6.1 Environment Variables
```bash
# Provider Selection
EMBEDDING_PROVIDER=local              # local, weaviate, openai

# Local Provider Settings
SENTENCE_TRANSFORMERS_MODEL=all-MiniLM-L6-v2
LOCAL_EMBEDDINGS_PATH=working_data/embeddings_db.pkl

# Weaviate Settings
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=                     # Optional
WEAVIATE_COLLECTION=PaperChunks

# OpenAI Settings
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536

# Chunking Parameters
CHUNK_SIZE=512                        # Tokens per chunk
CHUNK_OVERLAP=50                      # Overlap between chunks

# Processing Parameters
EMBEDDING_BATCH_SIZE=32               # Chunks per batch

# GCS Settings
GOOGLE_APPLICATION_CREDENTIALS=config/gcp-credentials.json
GCS_BUCKET_NAME=citeconnect-test-bucket
GCS_PROJECT_ID=your-gcp-project-id
```

### 6.2 Model Options
```bash
# Fast, efficient (384 dim) - Default
SENTENCE_TRANSFORMERS_MODEL=all-MiniLM-L6-v2

# Higher quality (768 dim)
SENTENCE_TRANSFORMERS_MODEL=all-mpnet-base-v2

# Multilingual support (768 dim)
SENTENCE_TRANSFORMERS_MODEL=paraphrase-multilingual-mpnet-base-v2

# Domain-specific: Biomedical
SENTENCE_TRANSFORMERS_MODEL=pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb
```

### 6.3 Performance Tuning
```bash
# Fast processing (less memory)
EMBEDDING_BATCH_SIZE=64
CHUNK_SIZE=256
CHUNK_OVERLAP=25

# High quality (more memory)
EMBEDDING_BATCH_SIZE=16
CHUNK_SIZE=1024
CHUNK_OVERLAP=128
SENTENCE_TRANSFORMERS_MODEL=all-mpnet-base-v2

# Balanced (recommended)
EMBEDDING_BATCH_SIZE=32
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

---

## 7. Quick Start Guide

### 7.1 Installation
```bash
# Clone repository
git clone https://github.com/DhikshaMathanagopal/CiteConnect.git
cd CiteConnect

# Create virtual environment
python3.9 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 7.2 Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimal Configuration**:
```bash
EMBEDDING_PROVIDER=local
SENTENCE_TRANSFORMERS_MODEL=all-MiniLM-L6-v2
LOCAL_EMBEDDINGS_PATH=working_data/embeddings_db.pkl
CHUNK_SIZE=512
CHUNK_OVERLAP=50
EMBEDDING_BATCH_SIZE=32
```

### 7.3 Generate Embeddings

**Option 1: Using Service Script**
```bash
python services/embedding_service.py \
    --domain healthcare \
    --batch-size 32 \
    --max-papers 10
```

**Option 2: Using Python**
```python
from src.DataPipeline.embeddings.local_embedder import LocalEmbedder

# Initialize
embedder = LocalEmbedder()

# Prepare chunks
chunks = [{
    "chunk_id": "p1_c0",
    "paper_id": "paper1",
    "text": "Machine learning enables computers to learn from data.",
    "paper_title": "ML Survey",
    "paper_year": 2023,
    "citation_count": 10
}]

# Generate embeddings
results = embedder.embed_chunks(chunks, show_progress=True)
print(f"Embedded {len(results)} chunks")
```

### 7.4 Search
```python
from src.DataPipeline.embeddings.local_embedder import LocalEmbedder

# Load embeddings
embedder = LocalEmbedder(save_path='working_data/embeddings_db.pkl')

# Search
results = embedder.search("machine learning healthcare", limit=5)

# Display results
for result in results:
    print(f"{result['paper_title']}: {result['similarity']:.3f}")
```

### 7.5 Weaviate Setup
```bash
# Start Weaviate with Docker
docker run -d -p 8080:8080 \
  -e ENABLE_MODULES='text2vec-transformers' \
  -e DEFAULT_VECTORIZER_MODULE='text2vec-transformers' \
  semitechnologies/weaviate:latest
```
```python
from src.DataPipeline.embeddings.vector_store import WeaviateStore

store = WeaviateStore()
store.add_chunks(chunks)
results = store.search("deep learning", limit=10)
```

---

## 8. API Reference

### 8.1 Preprocessing Classes

#### TextCleaner
```python
class TextCleaner:
    def clean(text: str) -> str
```

#### Chunker
```python
class Chunker:
    def __init__(chunk_size: int = 512, chunk_overlap: int = 50, preserve_sentences: bool = True)
    def chunk_text(text: str, paper_id: str, metadata: Optional[Dict] = None) -> List[Dict]
```

#### MetadataEnricher
```python
class MetadataEnricher:
    def enrich_chunks(chunks: List[Dict], paper_metadata: Dict) -> List[Dict]
    def enrich_batch(papers: List[Dict]) -> List[Dict]
```

### 8.2 Embedding Classes

#### EmbeddingGenerator
```python
class EmbeddingGenerator:
    def __init__(provider: Optional[str] = None)
    def embed_chunks(chunks: List[Dict], show_progress: bool = True) -> List[EmbeddingResult]
    def embed_single(text: str) -> Optional[List[float]]
    def search(query: str, limit: int = 10) -> List[Dict]
```

#### LocalEmbedder
```python
class LocalEmbedder:
    def __init__(model_name: Optional[str] = None, save_path: Optional[str] = None)
    def embed_chunks(chunks: List[Dict], show_progress: bool = False) -> List[Dict]
    def search(query: str, limit: int = 10) -> List[Dict]
    def save(filepath: Optional[str] = None)
    def load(filepath: Optional[str] = None)
    def get_stats() -> Dict
```

#### WeaviateStore
```python
class WeaviateStore:
    def __init__()
    def add_chunks(chunks: List[Dict]) -> bool
    def search(query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict]
    def delete_collection()
    def close()
```

### 8.3 Configuration

#### EmbeddingConfig
```python
@dataclass
class EmbeddingConfig:
    provider: str = 'local'
    local_model: str = 'all-MiniLM-L6-v2'
    local_db_path: str = 'working_data/embeddings_db.pkl'
    weaviate_url: str = 'http://localhost:8080'
    weaviate_api_key: Optional[str] = None
    collection_name: str = 'PaperChunks'
    openai_api_key: Optional[str] = None
    openai_model: str = 'text-embedding-3-small'
    embedding_dim: int = 384
    batch_size: int = 32
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    def validate() -> bool
```

### 8.4 Data Structures

**Chunk Format**:
```python
{
    "chunk_id": str,              # Unique identifier
    "paper_id": str,              # Paper reference
    "text": str,                  # Chunk content
    "position": int,              # Position in paper
    "token_count": int,           # Number of tokens
    "paper_title": str,           # Paper title
    "paper_year": int,            # Publication year
    "citation_count": int         # Citation count
}
```

**Search Result Format**:
```python
{
    "chunk_id": str,
    "paper_id": str,
    "text": str,
    "paper_title": str,
    "similarity": float,          # 0.0 to 1.0 (local)
    "distance": float,            # Lower is better (weaviate)
    "position": int,
    "paper_year": int,
    "citation_count": int
}
```

**EmbeddingResult Format**:
```python
@dataclass
class EmbeddingResult:
    chunk_id: str
    embedding: List[float]
    success: bool
    error: Optional[str] = None
```

---

## 9. Usage Examples

### 9.1 Complete Preprocessing Pipeline
```python
from src.DataPipeline.preprocessing.text_cleaner import TextCleaner
from src.DataPipeline.preprocessing.chunker import Chunker
from src.DataPipeline.preprocessing.metadata_enricher import MetadataEnricher

# Initialize components
cleaner = TextCleaner()
chunker = Chunker(chunk_size=512, chunk_overlap=50)
enricher = MetadataEnricher()

# Paper data
paper = {
    'paper_id': 'paper1',
    'title': 'Machine Learning in Healthcare',
    'abstract': 'This paper surveys...',
    'introduction': 'Machine learning has revolutionized...',
    'year': 2023,
    'citation_count': 45,
    'authors': ['Smith, J.']
}

# Step 1: Clean text
raw_text = paper['abstract'] + "\n\n" + paper['introduction']
clean_text = cleaner.clean(raw_text)

# Step 2: Create chunks
chunks = chunker.chunk_text(clean_text, paper_id=paper['paper_id'])

# Step 3: Enrich with metadata
enriched_chunks = enricher.enrich_chunks(chunks, paper)

print(f"Created {len(enriched_chunks)} enriched chunks")
```

### 9.2 Local Embedding Generation
```python
from src.DataPipeline.embeddings.local_embedder import LocalEmbedder

# Initialize
embedder = LocalEmbedder()

# Prepare chunks
chunks = [{
    "chunk_id": "p1_c0",
    "paper_id": "paper1",
    "text": "Machine learning enables automated learning from data.",
    "paper_title": "ML Survey",
    "paper_year": 2023,
    "citation_count": 10
}]

# Generate embeddings
results = embedder.embed_chunks(chunks, show_progress=True)

# Check success
for result in results:
    print(f"Chunk {result['chunk_id']}: {result['success']}")

# Get statistics
stats = embedder.get_stats()
print(f"Total chunks: {stats['total_chunks']}")
print(f"Embedding dimension: {stats['embedding_dimension']}")
```

### 9.3 Search and Retrieval
```python
from src.DataPipeline.embeddings.local_embedder import LocalEmbedder

# Load existing embeddings
embedder = LocalEmbedder(save_path='working_data/embeddings_db.pkl')

# Search
query = "deep learning for medical image analysis"
results = embedder.search(query, limit=5)

# Display results
for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['paper_title']} ({result['paper_year']})")
    print(f"   Similarity: {result['similarity']:.3f}")
    print(f"   Citations: {result['citation_count']}")
    print(f"   Preview: {result['text'][:100]}...")
```

### 9.4 Weaviate Integration
```python
from src.DataPipeline.embeddings.vector_store import WeaviateStore

# Initialize
store = WeaviateStore()

# Add chunks
chunks = [{
    "chunk_id": "p1_c0",
    "paper_id": "paper1",
    "text": "Machine learning enables automated decision making.",
    "position": 0,
    "token_count": 150,
    "paper_title": "ML Survey",
    "paper_year": 2023,
    "citation_count": 45
}]

success = store.add_chunks(chunks)
print(f"Added chunks: {success}")

# Search
results = store.search("machine learning", limit=5)

for result in results:
    print(f"{result['paper_title']}: {result['distance']:.3f}")

# Search with filters
results_2023 = store.search(
    query="deep learning",
    limit=5,
    filters={'paper_year': 2023}
)
```

### 9.5 Using Service Script
```bash
# Generate embeddings for specific domain
python services/embedding_service.py \
    --domain "machine learning" \
    --batch-size 32 \
    --max-papers 50

# Generate embeddings for all papers
python services/embedding_service.py \
    --batch-size 32

# Use specific provider
EMBEDDING_PROVIDER=weaviate python services/embedding_service.py \
    --domain healthcare \
    --max-papers 100
```

### 9.6 Complete End-to-End Example
```python
# Complete pipeline: Load → Preprocess → Embed → Search

from src.DataPipeline.preprocessing import TextCleaner, Chunker, MetadataEnricher
from src.DataPipeline.embeddings import LocalEmbedder

# Initialize all components
cleaner = TextCleaner()
chunker = Chunker(chunk_size=512, chunk_overlap=50)
enricher = MetadataEnricher()
embedder = LocalEmbedder()

# Load paper data (example)
papers = [
    {
        'paper_id': 'paper1',
        'title': 'Deep Learning in Healthcare',
        'text': 'Deep learning has transformed medical diagnostics...',
        'year': 2023,
        'citation_count': 67
    }
]

# Process each paper
all_chunks = []
for paper in papers:
    # Clean
    clean_text = cleaner.clean(paper['text'])
    
    # Chunk
    chunks = chunker.chunk_text(clean_text, paper['paper_id'])
    
    # Enrich
    enriched = enricher.enrich_chunks(chunks, paper)
    all_chunks.extend(enriched)

# Generate embeddings
print(f"Generating embeddings for {len(all_chunks)} chunks...")
results = embedder.embed_chunks(all_chunks, show_progress=True)

# Search
query = "machine learning healthcare diagnostics"
matches = embedder.search(query, limit=5)

# Display results
for match in matches:
    print(f"{match['paper_title']}: {match['similarity']:.3f}")
```

---

## 10. Troubleshooting

### 10.1 Common Issues

#### Issue: Model Download Fails

**Problem**: Sentence-transformers model download timeout or network error

**Solution**:
```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Or set cache directory
export SENTENCE_TRANSFORMERS_HOME=/path/to/cache
```

#### Issue: Weaviate Connection Failed

**Problem**: Cannot connect to Weaviate at localhost:8080

**Solution**:
```bash
# Check if Weaviate is running
curl http://localhost:8080/v1/meta

# Start Weaviate
docker run -d -p 8080:8080 \
  -e ENABLE_MODULES='text2vec-transformers' \
  semitechnologies/weaviate:latest

# Check Docker logs
docker logs <container_id>
```

#### Issue: Out of Memory During Embedding

**Problem**: Process killed during large batch embedding

**Solution**:
```bash
# Reduce batch size in .env
EMBEDDING_BATCH_SIZE=16

# Or reduce chunk size
CHUNK_SIZE=256

# Or process in smaller batches
python services/embedding_service.py --batch-size 10 --max-papers 50
```

#### Issue: Embeddings Not Persisting

**Problem**: Embeddings disappear after restart

**Solution**:
```python
# Explicitly save after generation
from src.DataPipeline.embeddings.local_embedder import LocalEmbedder

embedder = LocalEmbedder()
embedder.embed_chunks(chunks)
embedder.save('working_data/embeddings_db.pkl')

# Verify save location
print(f"Saved to: {embedder.save_path}")
```

#### Issue: Search Returns No Results

**Problem**: Search always returns empty list

**Solution**:
```python
# Check if embeddings exist
embedder = LocalEmbedder()
stats = embedder.get_stats()
print(f"Total chunks: {stats['total_chunks']}")

# If 0, generate embeddings first
if stats['total_chunks'] == 0:
    print("No embeddings found - run embedding generation first")
```

#### Issue: OpenAI Rate Limit Exceeded

**Problem**: `RateLimitError` from OpenAI API

**Solution**:
```bash
# Reduce batch size
EMBEDDING_BATCH_SIZE=20

# Or switch to local provider
EMBEDDING_PROVIDER=local
```

#### Issue: Import Errors

**Problem**: `ModuleNotFoundError` when importing modules

**Solution**:
```bash
# Install package in editable mode
pip install -e .

# Verify installation
pip show citeconnect

# Add to PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### 10.2 Performance Optimization
```bash
# Fast processing (less accurate)
EMBEDDING_BATCH_SIZE=64
CHUNK_SIZE=256
CHUNK_OVERLAP=25

# High quality (slower)
EMBEDDING_BATCH_SIZE=16
CHUNK_SIZE=1024
CHUNK_OVERLAP=128
SENTENCE_TRANSFORMERS_MODEL=all-mpnet-base-v2

# Balanced (recommended)
EMBEDDING_BATCH_SIZE=32
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### 10.3 Validation Commands
```bash
# Test imports
python -c "from src.DataPipeline.embeddings.local_embedder import LocalEmbedder; print('✅ OK')"

# Test configuration
python -c "from src.DataPipeline.embeddings.config import config; config.validate(); print('✅ OK')"

# Test preprocessing
python -c "from src.DataPipeline.preprocessing.chunker import Chunker; print('✅ OK')"

# Run unit tests
pytest tests/unit/test_embeddings.py -v

# Run integration tests
pytest tests/integration/ -v

# Test complete pipeline
python services/embedding_service.py --domain test --max-papers 5
```

### 10.4 Debugging Tips
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check GPU availability
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Verify model loading
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f"Model dimension: {model.get_sentence_embedding_dimension()}")

# Test chunking
from src.DataPipeline.preprocessing.chunker import Chunker
chunker = Chunker(chunk_size=512, chunk_overlap=50)
chunks = chunker.chunk_text("Test text" * 100, "test_paper")
print(f"Generated {len(chunks)} chunks")
```

---

## Additional Resources

- **Sentence-Transformers Documentation**: https://www.sbert.net/
- **Weaviate Documentation**: https://weaviate.io/developers/weaviate
- **OpenAI Embeddings Guide**: https://platform.openai.com/docs/guides/embeddings
- **Project Repository**: https://github.com/DhikshaMathanagopal/CiteConnect
- **Full Documentation**: https://github.com/DhikshaMathanagopal/CiteConnect/tree/main/documentation

---

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**License**: MIT  
**Maintainers**: CiteConnect Team, Northeastern University
