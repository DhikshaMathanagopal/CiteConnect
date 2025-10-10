## CiteConnect - Research Paper Recommendation System
### Project Overview
CiteConnect is an intelligent research paper recommendation system that transforms how researchers discover and explore academic literature. By leveraging retrieval-augmented generation (RAG), vector search, and citation graph analysis, the platform provides personalized, explainable recommendations beyond traditional keyword-based searches.

### Key Features

- Semantic Search: Understands concepts, not just keywords
- AI-Powered Explanations: Each recommendation includes why it's relevant
- Interactive Citation Graphs: Visualize paper connections and research lineage
- Personalized Recommendations: Adapts to individual research interests
- Unified Platform: Search, read, and analyze papers in one place
- Citation Graph: Interactive visualization of how papers are connected via citations.
- End-to-End MLOps: Containerized pipelines, CI/CD workflows, monitoring, and drift detection.

### Technical Highlights

- Microservices architecture deployed on Kubernetes
- RAG pipeline with OpenAI/Vertex AI integration
- Vector database for semantic similarity search
- Graph database for citation network analysis
- MLOps best practices with CI/CD and monitoring

### Tech Stack
- Data Sources: arXiv API, Semantic Scholar API, Unpaywall API
- ML/NLP: OpenAI embeddings / Sentence-Transformers, spaCy
- Databases: Vector DB (FAISS/Pinecone), Neo4j (citations), GCS (storage)
- Backend: FastAPI
- Frontend: Streamlit or Next.js
- MLOps: Docker, Kubernetes (GKE), Airflow, DVC, MLflow, GitHub Actions, Prometheus/Grafana

## Installation
```bash
Clone the Repository
git clone https://github.com/<your-username>/CiteConnect.git
cd CiteConnect
```

## Set up Virtual Environment
```
python3 -m venv venv
source venv/bin/activate   # Mac
venv\Scripts\activate      # Windows
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure API Keys
```bash
Create a .env file in the root directory.
Add credentials (arXiv, Semantic Scholar, OpenAI, Neo4j, etc.).
```

### Usage
```bash
Run Backend (FastAPI)
uvicorn src.api.main:app --reload
```

```bash
Run Frontend (Streamlit)
streamlit run src/frontend/app.py
```

```bash
Run Ingestion Pipeline (Manual / Scheduled)
python src/ingestion/fetch_papers.py
```

## Contributors

1. Abhinav Aditya
2. Anusha Srinivasan 
3. Dennis Jose 
4. Dhiksha Mathanagopal
5. Sahil Mohanty 

### Notes
1. Open-access PDFs are stored and parsed; restricted PDFs are linked via metadata only.
2. This project is for academic purposes and aligns with the MLOps IE7305 course objectives.

# CiteConnect Project Folder Structure

## Complete Project Layout

citeconnect/
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 docker-compose.yaml
├── 📄 .env.example
├── 📄 .gitignore
├── 📄 pyproject.toml
│
├── 📁 dags/                          # Airflow DAGs (mounted to container)
│   ├── 📄 __init__.py
│   ├── 📄 simple_data_ingestion_dag.py
│   ├── 📄 complete_mlops_pipeline_dag.py
│   └── 📁 dag_utils/
│       ├── 📄 __init__.py
│       ├── 📄 notification_helpers.py
│       └── 📄 task_groups.py
│
├── 📁 src/                           # Source code
│   ├── 📄 __init__.py
│   │
│   ├── 📁 data_pipeline/             # Data ingestion & processing
│   │   ├── 📄 __init__.py
│   │   ├── 📁 ingestion/             
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 arxiv_client.py
│   │   │   ├── 📄 semantic_scholar_client.py
│   │   │   ├── 📄 paper_selector.py
│   │   │   └── 📄 batch_downloader.py
│   │   │
│   │   ├── 📁 processing/            
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 pdf_processor.py
│   │   │   ├── 📄 text_extractor.py
│   │   │   ├── 📄 chunking_engine.py
│   │   │   └── 📄 preprocessing_utils.py
│   │   │
│   │   ├── 📁 validation/            
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 quality_checker.py
│   │   │   ├── 📄 validation_rules.py
│   │   │   ├── 📄 data_profiler.py
│   │   │   └── 📄 batch_validator.py
│   │   │
│   │   └── 📁 utils/                 # Shared utilities
│   │       ├── 📄 __init__.py
│   │       ├── 📄 storage_helpers.py
│   │       ├── 📄 logging_config.py
│   │       └── 📄 error_handlers.py
│   │
│   ├── 📁 model_pipeline/            # ML model components
│   │   ├── 📄 __init__.py
│   │   ├── 📁 embeddings/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 embedding_generator.py
│   │   │   ├── 📄 vector_store.py
│   │   │   └── 📄 similarity_search.py
│   │   │
│   │   ├── 📁 training/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 model_trainer.py
│   │   │   ├── 📄 recommendation_engine.py
│   │   │   └── 📄 evaluation_metrics.py
│   │   │
│   │   └── 📁 serving/
│   │       ├── 📄 __init__.py
│   │       ├── 📄 model_server.py
│   │       └── 📄 api_endpoints.py
│   │
│   ├── 📁 deployment/                
│   │   ├── 📄 __init__.py
│   │   ├── 📁 infrastructure/
│   │   │   ├── 📄 gcp_setup.py
│   │   │   ├── 📄 k8s_deployer.py
│   │   │   └── 📄 terraform_configs.py
│   │   │
│   │   ├── 📁 containers/
│   │   │   ├── 📄 Dockerfile.data_pipeline
│   │   │   ├── 📄 Dockerfile.model_server
│   │   │   └── 📄 Dockerfile.api
│   │   │
│   │   └── 📁 monitoring/
│   │       ├── 📄 prometheus_config.py
│   │       ├── 📄 grafana_dashboards.py
│   │       └── 📄 alerting_rules.py
│   │
│   └── 📁 web_app/                   # Frontend application
│       ├── 📄 __init__.py
│       ├── 📄 app.py                 # FastAPI/Flask app
│       ├── 📁 static/
│       ├── 📁 templates/
│       └── 📁 components/
│
├── 📁 tests/                         
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py                # pytest configuration
│   │
│   ├── 📁 unit/                      # Unit tests
│   │   ├── 📄 test_arxiv_client.py
│   │   ├── 📄 test_pdf_processor.py
│   │   ├── 📄 test_quality_checker.py
│   │   └── 📄 test_embedding_generator.py
│   │
│   ├── 📁 integration/               # Integration tests
│   │   ├── 📄 test_data_pipeline.py
│   │   ├── 📄 test_end_to_end.py
│   │   └── 📄 test_api_endpoints.py
│   │
│   └── 📁 fixtures/                  # Test data
│       ├── 📄 sample_papers.json
│       ├── 📄 test_pdfs/
│       └── 📄 mock_responses/
│
├── 📁 configs/                       # Configuration files
│   ├── 📄 __init__.py
│   ├── 📄 config.yaml                # Main configuration
│   ├── 📄 selection_criteria.yaml    # Paper selection rules
│   ├── 📄 model_config.yaml          # ML model parameters
│   ├── 📄 logging.yaml               # Logging configuration
│   └── 📄 deployment_config.yaml     # Infrastructure settings
│
├── 📁 scripts/                       # Utility scripts
│   ├── 📄 setup_environment.sh       # Environment setup
│   ├── 📄 install_dependencies.sh    # Package installation
│   ├── 📄 generate_fernet_key.py     # Security setup
│   ├── 📄 data_backup.py             # Data management
│   └── 📄 health_check.py            # System health monitoring
│
├── 📁 docs/                          # Documentation
│   ├── 📄 README.md
│   ├── 📄 SETUP.md                   # Setup instructions
│   ├── 📄 API_DOCUMENTATION.md       # API docs
│   ├── 📄 ARCHITECTURE.md            # System architecture
│   ├── 📁 diagrams/                  # Architecture diagrams
│   └── 📁 presentations/             # For MLOps Expo
│
├── 📁 infrastructure/                # Infrastructure as Code
│   ├── 📁 terraform/                 # GCP infrastructure
│   │   ├── 📄 main.tf
│   │   ├── 📄 variables.tf
│   │   └── 📄 outputs.tf
│   │
│   ├── 📁 kubernetes/                # K8s manifests
│   │   ├── 📄 deployment.yaml
│   │   ├── 📄 service.yaml
│   │   └── 📄 ingress.yaml
│   │
│   └── 📁 monitoring/                # Monitoring configs
│       ├── 📄 prometheus.yaml
│       ├── 📄 grafana-dashboard.json
│       └── 📄 alerts.yaml
│
├── 📁 notebooks/                     # Jupyter notebooks (analysis/prototyping)
│   ├── 📄 01_data_exploration.ipynb
│   ├── 📄 02_pdf_processing_analysis.ipynb
│   ├── 📄 03_embedding_experiments.ipynb
│   └── 📄 04_model_evaluation.ipynb
│
├── 📁 data/                          # Local data (gitignored, for development)
│   ├── 📁 raw/                       # Downloaded papers
│   ├── 📁 processed/                 # Processed data
│   ├── 📁 embeddings/                # Generated embeddings
│   └── 📁 models/                    # Trained models
│
├── 📁 logs/                          # Airflow logs (mounted from container)
│   └── 📄 .gitkeep
│
├── 📁 working_data/                  # Temporary processing data (mounted to container)
│   ├── 📁 temp_pdfs/
│   ├── 📁 processing_cache/
│   └── 📄 .gitkeep
│
├── 📁 config/                        # Airflow configs & credentials (mounted to container)
│   ├── 📄 .gitkeep
│   ├── 📄 gcp-credentials.json       # (gitignored)
│   └── 📄 api_keys.env               # (gitignored)
│
└── 📁 plugins/                       # Airflow plugins (mounted to container)
    ├── 📄 __init__.py
    ├── 📁 operators/
    │   ├── 📄 citeconnect_operators.py
    │   └── 📄 gcs_operators.py
    └── 📁 hooks/
        └── 📄 semantic_scholar_hook.py