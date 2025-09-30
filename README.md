CiteConnect: A Research Paper Recommendation System

CiteConnect is a complete end-to-end MLOps pipeline project that helps researchers discover relevant academic papers. The system integrates data ingestion, embeddings, retrieval-augmented generation (RAG), citation graph visualization, and personalization, all deployed with modern cloud-native MLOps practices.

Features
Semantic Search: Retrieve papers using embeddings for contextual relevance.
Citation Graph: Interactive visualization of how papers are connected via citations.
Summarized Explanations: LLM-based summaries describing why papers are recommended.
User Personalization: Accounts and saved research interests.
End-to-End MLOps: Containerized pipelines, CI/CD workflows, monitoring, and drift detection.

Tech Stack
Data Sources: arXiv API, Semantic Scholar API, Unpaywall API
ML/NLP: OpenAI embeddings / Sentence-Transformers, spaCy
Databases: Vector DB (FAISS/Pinecone), Neo4j (citations), GCS (storage)
Backend: FastAPI
Frontend: Streamlit or Next.js
MLOps: Docker, Kubernetes (GKE), Airflow, DVC, MLflow, GitHub Actions, Prometheus/Grafana

Installation
Clone the Repository
git clone https://github.com/<your-username>/CiteConnect.git
cd CiteConnect

Set up Virtual Environment
python3 -m venv venv
source venv/bin/activate   # Mac
venv\Scripts\activate      # Windows

Install Dependencies
pip install -r requirements.txt

Configure API Keys
Create a .env file in the root directory.
Add credentials (arXiv, Semantic Scholar, OpenAI, Neo4j, etc.).

Usage
Run Backend (FastAPI)
uvicorn src.api.main:app --reload

Run Frontend (Streamlit)
streamlit run src/frontend/app.py

Run Ingestion Pipeline (Manual / Scheduled)
python src/ingestion/fetch_papers.py

Contributors

1. Abhinav Aditya
2. Anusha Srinivasan 
3. Dennis Jose 
4. Dhiksha Mathanagopal
5. Sahil Mohanty 

Notes
1.Open-access PDFs are stored and parsed; restricted PDFs are linked via metadata only.
2.This project is for academic purposes and aligns with the MLOps IE7305 course objectives.
