# Quick Start Guide

## Step 1: Setup
```bash
# Run setup script
bash setup.sh

# Activate virtual environment
source citeConnectEnv/bin/activate
```

## Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 3: Copy Code Files

Copy the code I provided into these files:

### Preprocessing Module
1. `preprocessing/text_cleaner.py`
2. `preprocessing/chunker.py`
3. `preprocessing/metadata_enricher.py`

### Embeddings Module
1. `embeddings/config.py`
2. `embeddings/embed_generator.py`
3. `embeddings/vector_store.py`

### Services
1. `services/embedding_service.py`

### Utils
1. `utils/gcs_reader.py`

## Step 4: Configure
```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

## Step 5: Start Weaviate
```bash
./start_weaviate.sh
```

## Step 6: Run Service
```bash
# Test with small dataset
python services/embedding_service.py healthcare --max-papers 10

# Process full domain
python services/embedding_service.py healthcare
```

## Step 7: Verify
```python
# Test in Python
from embeddings import WeaviateStore

store = WeaviateStore()
results = store.search("machine learning in healthcare", limit=5)
print(results)
```

Done! 🎉
