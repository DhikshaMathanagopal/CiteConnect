# src/ingest_data.py
import os, json, argparse, datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# --- Load env (.env) and check keys ---
load_dotenv()
API_KEY = os.getenv("SEMANTIC_SCHOLAR_KEY", "")
UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "")

print("🔑 Semantic Scholar Key loaded:", bool(API_KEY))
if not API_KEY:
    raise SystemExit(
        "Missing SEMANTIC_SCHOLAR_KEY. Put it in .env or export it in your terminal."
    )
if not UNPAYWALL_EMAIL:
    print("⚠️  UNPAYWALL_EMAIL not set — will skip Unpaywall PDF enrichment.")

S2_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

# IMPORTANT: remove 'doi' from the fields list — DOI is inside externalIds.DOI
S2_FIELDS = (
    "paperId,title,abstract,authors,year,venue,"
    "isOpenAccess,openAccessPdf,externalIds,citationCount,influentialCitationCount"
)

def s2_search(query: str, limit: int = 4, offset: int = 0):
    """Call Semantic Scholar search with proper headers and diagnostics."""
    headers = {
        "x-api-key": API_KEY,
        "User-Agent": "CiteConnect-Mini/1.0 (student project)",
        "Accept": "application/json",
    }
    params = {
        "query": query,
        "limit": min(100, limit),
        "offset": offset,
        "fields": S2_FIELDS,
    }
    r = requests.get(S2_URL, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        print("❌ S2 request failed")
        print("   URL:", r.url)
        print("   Status:", r.status_code)
        try:
            print("   Body:", r.json())
        except Exception:
            print("   Body (text):", r.text[:500])
        r.raise_for_status()
    return r.json().get("data", [])

def unpaywall_pdf(doi: str):
    """Return (is_oa, pdf_url) from Unpaywall if email is provided."""
    if not UNPAYWALL_EMAIL or not doi:
        return None, None
    url = f"https://api.unpaywall.org/v2/{doi}"
    r = requests.get(url, params={"email": UNPAYWALL_EMAIL}, timeout=30)
    if r.status_code != 200:
        return None, None
    d = r.json()
    is_oa = d.get("is_oa")
    pdf = (d.get("best_oa_location") or {}).get("url_for_pdf")
    return is_oa, pdf

def main():
    ap = argparse.ArgumentParser(description="Ingest 3–4 papers from Semantic Scholar + Unpaywall enrichment")
    ap.add_argument("--query", default="transformer language models", help="search query")
    ap.add_argument("--limit", type=int, default=4, help="number of papers to fetch")
    ap.add_argument("--topic", default="NLP", help="topic label to store")
    args = ap.parse_args()

    papers = s2_search(args.query, limit=args.limit, offset=0)

    # Enrich with Unpaywall; DOI comes from externalIds.DOI
    for p in papers:
        ext = p.get("externalIds") or {}
        doi = ext.get("DOI")  # ← correct place to read DOI
        s2_pdf = (p.get("openAccessPdf") or {}).get("url")
        is_oa, up_pdf = unpaywall_pdf(doi)
        p["doi"] = doi
        p["pdf_url"] = s2_pdf or up_pdf
        p["isOpenAccess"] = p.get("isOpenAccess") or bool(up_pdf or s2_pdf)
        p["topic_label"] = args.topic

    # Save to data/raw_metadata/<slug>_<timestamp>.json
    slug = args.query.lower().replace(" ", "_")
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = Path("data/raw_metadata") / f"{slug}_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(papers, f, indent=2)

    print(f"✅ Saved {len(papers)} papers → {out_path}")

if __name__ == "__main__":
    main()
