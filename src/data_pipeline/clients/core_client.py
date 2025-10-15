import os
import logging
from src.data_pipeline.utils.http_utils import safe_get

CORE_KEY = os.getenv("CORE_API_KEY")

def fetch_from_core(doi):
    if not (doi and CORE_KEY):
        return None
    url = f"https://api.core.ac.uk/v3/search/works?query=doi:{doi}&apiKey={CORE_KEY}"
    r = safe_get(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            if data.get("results"):
                dl = data["results"][0].get("downloadUrl")
                if dl:
                    logging.info(f"Found via CORE: {dl}")
                    return dl
        except Exception as e:
            logging.warning(f"Failed to parse CORE response: {e}")
    return None
