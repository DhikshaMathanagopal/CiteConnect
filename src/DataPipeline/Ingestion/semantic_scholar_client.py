# Clean semantic_scholar_client.py - No fallback, just proper rate limiting

import os
import sys
import json
import yaml
import requests
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '../../..')
sys.path.insert(0, project_root)

load_dotenv()


def load_params():
    """Load DVC parameters"""
    params_file = Path("params.yaml")
    if params_file.exists():
        with open(params_file, 'r') as f:
            return yaml.safe_load(f)
    return {}


class SemanticScholarClient:
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        
        self.headers = {'User-Agent': 'CiteConnect/1.0'}
        if self.api_key:
            self.headers['x-api-key'] = self.api_key
            
        # Rate limiting settings
        self.request_delay = 2.0  # Wait 2 seconds between requests
        self.last_request_time = 0
        
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f}s...")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def search_with_retry(self, query, limit=5, max_retries=3):
        """Search papers with retry logic for rate limiting"""
        url = f"{self.base_url}/paper/search"
        params = {
            'query': query,
            'limit': limit,
            'fields': 'paperId,title,authors,year,citationCount,abstract'
        }
        
        for attempt in range(max_retries):
            try:
                print(f"🔍 Searching: '{query}' (limit: {limit}) - Attempt {attempt + 1}")
                
                # Rate limiting
                self._wait_for_rate_limit()
                
                response = requests.get(url, params=params, headers=self.headers, timeout=30)
                
                if response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"⚠️ Rate limited! Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                elif response.status_code == 200:
                    papers = response.json().get('data', [])
                    print(f"✅ Successfully retrieved {len(papers)} papers")
                    return papers
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    # Exponential backoff for rate limiting
                    wait_time = min(60 * (2 ** attempt), 300)  # Max 5 minutes
                    print(f"⚠️ Rate limited! Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ HTTP Error {response.status_code}: {e}")
                    raise  # Re-raise non-rate-limit errors
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    print(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise  # Re-raise if all retries exhausted
        
        # If we get here, all retries failed
        raise Exception(f"Failed to retrieve papers after {max_retries} attempts due to rate limiting")
    
    def collect_papers(self):
        """Main collection function"""
        start_time = datetime.now()
        
        # Load parameters from DVC
        params = load_params()
        query = params.get('data_collection', {}).get('query', 'semiconductor')
        limit = params.get('data_collection', {}).get('limit', 5)
        
        print(f"📚 DVC Collection: {limit} papers about '{query}'")
        
        try:
            # Collect papers with retry logic
            papers = self.search_with_retry(query, limit)
            
            # Add collection metadata
            collection_time = datetime.now()
            for paper in papers:
                paper['collected_at'] = collection_time.isoformat()
                paper['collection_run'] = collection_time.strftime("%Y%m%d_%H%M%S")
                paper['parameters'] = {'query': query, 'limit': limit}
            
            # Save papers (DVC output)
            Path("data/raw").mkdir(parents=True, exist_ok=True)
            with open("data/raw/papers.json", 'w') as f:
                json.dump(papers, f, indent=2)
            
            # Save metrics (DVC metrics)
            processing_time = (datetime.now() - start_time).total_seconds()
            metrics = {
                "papers_collected": len(papers),
                "query": query,
                "limit_requested": limit,
                "collection_time_seconds": processing_time,
                "timestamp": collection_time.isoformat(),
                "run_id": collection_time.strftime("%Y%m%d_%H%M%S"),
                "success_rate": 1.0,
                "api_calls": 1
            }
            
            Path("metrics").mkdir(exist_ok=True)
            with open("metrics/stats.json", 'w') as f:
                json.dump(metrics, f, indent=2)
            
            print(f"✅ Successfully collected {len(papers)} papers")
            if papers:
                print(f"📄 First paper: {papers[0].get('title', '')[:60]}...")
            
            return papers
            
        except Exception as e:
            print(f"❌ Collection failed: {e}")
            
            # Save failure metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            metrics = {
                "papers_collected": 0,
                "query": query,
                "limit_requested": limit,
                "collection_time_seconds": processing_time,
                "error": str(e),
                "success_rate": 0.0,
                "timestamp": datetime.now().isoformat(),
                "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "api_calls": 0
            }
            
            Path("metrics").mkdir(exist_ok=True)
            with open("metrics/stats.json", 'w') as f:
                json.dump(metrics, f, indent=2)
            
            # Re-raise the exception so DVC knows it failed
            raise


def main():
    """Main function that DVC will call"""
    client = SemanticScholarClient()
    papers = client.collect_papers()
    print(f"🎯 Pipeline completed successfully with {len(papers)} papers")


if __name__ == "__main__":
    main()