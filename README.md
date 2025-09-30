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
