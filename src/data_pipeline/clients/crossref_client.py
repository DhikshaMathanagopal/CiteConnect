import logging
from src.data_pipeline.utils.http_utils import safe_get

def fetch_from_crossref(doi):
    if not doi:
        return None
    url = f"https://api.crossref.org/works/{doi}"
    r = safe_get(url)
    if r and r.status_code == 200:
        try:
            data = r.json().get("message", {})
            for link in data.get("link", []):
                if link.get("content-type") == "application/pdf":
                    logging.info(f"Found via CrossRef: {link['URL']}")
                    return link["URL"]
        except Exception as e:
            logging.warning(f"Failed to parse CrossRef: {e}")
    return None
