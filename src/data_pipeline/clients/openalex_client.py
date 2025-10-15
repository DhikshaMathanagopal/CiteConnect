import logging
from src.data_pipeline.utils.http_utils import safe_get

def fetch_from_openalex(doi):
    """
    Fetches a PDF URL using the OpenAlex API.
    """
    if not doi:
        return None
    # OpenAlex uses the DOI as part of the identifier
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    r = safe_get(url)
    if r and r.status_code == 200:
        try:
            data = r.json()
            primary = data.get("primary_location", {})
            pdf_url = primary.get("pdf_url") or primary.get("source", {}).get("url")
            if pdf_url:
                logging.info(f"Found via OpenAlex: {pdf_url}")
                return pdf_url
        except Exception as e:
            logging.warning(f"Failed to parse OpenAlex response for {doi}: {e}")
    return None
