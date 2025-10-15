import os
import time
import logging
import requests

SEM_KEY = os.getenv("SEMANTIC_SCHOLAR_KEY")
HEADERS = {"User-Agent": "CiteConnect/1.0"}
if SEM_KEY:
    HEADERS["x-api-key"] = SEM_KEY

def search_semantic_scholar(query, limit=10, retries=3):
    url = (
        "https://api.semanticscholar.org/graph/v1/paper/search?"
        f"query={query}&limit={limit}&fields="
        "paperId,title,year,venue,externalIds,abstract,authors,"
        "citationCount,influentialCitationCount,referenceCount,"
        "isOpenAccess,openAccessPdf,publicationDate"
    )
    for attempt in range(retries):
        logging.info(f"Semantic Scholar: {query} | attempt {attempt+1}")
        time.sleep(0.7)
        r = requests.get(url, headers=HEADERS, timeout=40)
        if r.status_code == 200:
            data = r.json().get("data", [])
            logging.info(f"Retrieved {len(data)} results.")
            return data
        elif r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", 10))
            wait = retry_after * (attempt + 1)
            logging.warning(f"Rate limited (429). Waiting {wait}s before retry.")
            time.sleep(wait)
        else:
            logging.warning(f"Error {r.status_code}: {r.text[:200]}")
            time.sleep(2)
    return []
