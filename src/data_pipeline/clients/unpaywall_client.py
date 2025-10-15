import os
import logging
from src.data_pipeline.utils.http_utils import safe_get

UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "your_email@example.com")

def fetch_from_unpaywall(doi):
    if not doi:
        return None
    url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    r = safe_get(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            oa = (data.get("best_oa_location") or {}).get("url_for_pdf")
            if oa:
                logging.info(f"Found via Unpaywall: {oa}")
                return oa
        except Exception as e:
            logging.warning(f"Failed to parse Unpaywall: {e}")
    return None
