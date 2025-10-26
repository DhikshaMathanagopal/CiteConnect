# CiteConnect Embedding Service

Production-ready embedding service for processing research papers from GCS.

## 🏗️ Architecture
```
GCS Parquet Files → Text Cleaning → Chunking → Embedding → Weaviate
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Create virtual environment
python3 -m venv citeConnectEnv
source citeConnectEnv/bin/activate  # On Windows: citeConnectEnv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Weaviate
```bash
./start_weaviate.sh
```

### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 4. Run Embedding Service
```bash
# Process healthcare domain
python services/embedding_service.py healthcare

# Process with limits (for testing)
python services/embedding_service.py healthcare --max-papers 100 --batch-size 25
```

## 📁 Project Structure
```
CITECONNECT/
├── preprocessing/          # Text cleaning and chunking
├── embeddings/            # Embedding generation and vector store
├── services/              # Main embedding service
├── utils/                 # Helper utilities (GCS, storage)
├── tests/                 # Test suite
├── data/                  # Local data storage
├── ingestion.py          # Data ingestion script
└── .env                  # Configuration (not in git)
```

## 🧪 Testing
```bash
# Run all tests
./run_tests.sh

# Run specific test
pytest tests/test_preprocessing.py -v
```

## 📊 Data Flow

1. **Input**: Parquet files in `gs://citeconnect-processed-parquet/{domain}/`
2. **Process**: Clean → Chunk → Embed
3. **Output**: Searchable vectors in Weaviate

## 🔧 Configuration

Edit `.env` to configure:
- GCS bucket and credentials
- Weaviate connection
- Embedding provider (Weaviate/OpenAI)
- Chunk size and overlap
- Batch processing size

## 📖 Module Documentation

- [Preprocessing Module](preprocessing/README.md)
- [Embeddings Module](embeddings/README.md)
- [Services Module](services/README.md)

## 🐛 Troubleshooting

**Weaviate not starting:**
```bash
docker logs weaviate
./stop_weaviate.sh
./start_weaviate.sh
```

**GCS authentication error:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"
```

**Import errors:**
```bash
pip install -r requirements.txt --upgrade
```
