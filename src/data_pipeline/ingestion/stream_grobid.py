import os
import logging
import argparse
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.data_pipeline.clients.semantic_scholar_client import search_semantic_scholar
from src.data_pipeline.clients.pdf_resolver import resolve_pdf_url
from src.data_pipeline.clients.grobid_client import extract_with_grobid

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def process_paper(paper, grobid_url):
    pdf_url = resolve_pdf_url(paper,use_browser_fallback=True)
    if not pdf_url:
        return {**paper, "status": "no_pdf"}
    sections, status = extract_with_grobid(pdf_url, grobid_url)
    return {**paper, **(sections or {}), "pdf_url": pdf_url, "status": status}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--grobid", default="http://localhost:8070")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    query_slug = args.query.lower().replace(" ", "_")

    papers = search_semantic_scholar(args.query, args.limit)
    logging.info(f"Deduplicated {len(papers)} papers")

    titles = set()
    unique = [p for p in papers if not (p.get("title", "").lower() in titles or titles.add(p.get("title", "").lower()))]

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(process_paper, p, args.grobid): p for p in unique}
        for fut in as_completed(futures):
            results.append(fut.result())

    df = pd.DataFrame(results)
    keep_cols = ["paperId", "title", "year", "venue", "abstract", "introduction", "authors", "citationCount", "pdf_url", "status"]
    for c in keep_cols:
        if c not in df.columns:
            df[c] = None
    df = df[keep_cols]

    parquet_path = os.path.join(args.out_dir, f"{query_slug}.parquet")
    df.to_parquet(parquet_path)
    logging.info(f"Saved Parquet → {parquet_path}")

    failed = df[df["status"] != "ok"]
    if not failed.empty:
        fail_path = os.path.join(args.out_dir, f"failures_{query_slug}.json")
        failed.to_json(fail_path, orient="records", indent=2)
        logging.info(f"Saved {len(failed)} failed papers → {fail_path}")

    logging.info(f"Done | total={len(df)} | success={(df.status=='ok').sum()} | failed={(df.status!='ok').sum()}")

if __name__ == "__main__":
    main()
