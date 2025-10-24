import logging
import re
import time
import pandas as pd
from pathlib import Path

from DataPipeline.utils.logging_config import setup_logging
from DataPipeline.utils.constants import GCS_BUCKET
from .semantic_scholar_client import search_semantic_scholar
from .processor import process_papers
from .gcs_uploader import upload_to_gcs


def save_results(data, search_term, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\s-]", "", search_term).replace(" ", "_")
    filename = f"{output_dir}/{safe_name}_{int(time.time())}.parquet"

    pd.DataFrame(data).to_parquet(filename, index=False)
    logging.info(f"Saved: {filename}")

    upload_to_gcs(filename, GCS_BUCKET, f"raw/{safe_name}.parquet")


def ingest_papers(search_terms, limit=10, output_dir="data/raw"):
    setup_logging()
    for term in search_terms:
        logging.info(f"Starting: {term}")
        papers = search_semantic_scholar(term, limit)
        if not papers:
            logging.warning(f"No results for: {term}")
            continue

        processed = process_papers(papers, term)
        save_results(processed, term, output_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("terms", nargs="+", help="Search terms")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output", default="data/raw")

    args = parser.parse_args()
    ingest_papers(args.terms, args.limit, args.output)
