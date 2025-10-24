# src/data_pipeline/ingestion/semantic_scholar_client.py
"""
Minimal Semantic Scholar API client
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add project root to path - go up 3 levels from current file
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '../../..')
sys.path.insert(0, project_root)

# Import storage helper
try:
    from src.DataPipeline.utils.storage_helpers import save_data
except ImportError:
    print("⚠️ Storage module not found, using fallback")
    def save_data(data, filename=None):
        import json
        from pathlib import Path
        Path("./data/raw").mkdir(parents=True, exist_ok=True)
        filename = filename or "papers.json"
        filepath = f"./data/raw/{filename}"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved to: {filepath}")
        return filepath

load_dotenv()


class SemanticScholarClient:
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        
        self.headers = {'User-Agent': 'CiteConnect/1.0'}
        if self.api_key:
            self.headers['x-api-key'] = self.api_key
    
    def search(self, query, limit=10):
        """Search papers."""
        url = f"{self.base_url}/paper/search"
        params = {
            'query': query,
            'limit': limit,
            'fields': 'paperId,title,authors,year,citationCount,abstract'
        }
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        
        return response.json().get('data', [])
    
    def collect_papers(self, query="semiconductor", limit=10):
        """Collect and save papers."""
        print(f"🔍 Searching: {query}")
        
        papers = self.search(query, limit)
        print(f"📄 Found: {len(papers)} papers")
        
        if papers:
            save_data(papers, "papers.json")
            
            # Show first paper
            first = papers[0]
            print(f"📄 First: {first.get('title', '')[:50]}...")
        
        return papers


def main():
    client = SemanticScholarClient()
    client.collect_papers("semiconductor", 5)


if __name__ == "__main__":
    main()