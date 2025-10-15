# src/data_pipeline/clients/pdf_resolver.py
import os
import io
import json
import time
import logging
from urllib.parse import urljoin, urlparse

from src.data_pipeline.utils.http_utils import safe_get

# Optional browser fallback (Playwright). Keep import lazy inside the function.
PLAYWRIGHT_TIMEOUT_MS = 60_000

UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "your_email@example.com")
CORE_KEY = os.getenv("CORE_API_KEY")

# Simple on-disk cache to avoid re-resolving the same DOI repeatedly
CACHE_PATH = os.getenv("PDF_CACHE_PATH", ".cache/pdf_cache.json")
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

def _load_cache():
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(cache):
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cache, f)
    os.replace(tmp, CACHE_PATH)

_CACHE = _load_cache()

# Shared headers; some publishers check UA/Referer aggressively
BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def _is_pdf_response(resp):
    ctype = (resp.headers or {}).get("Content-Type", "").lower()
    dispo = (resp.headers or {}).get("Content-Disposition", "").lower()
    return ("pdf" in ctype) or ("attachment" in dispo and ".pdf" in dispo)

def _try_get_pdf(url, referer=None, stream=True):
    headers = dict(BASE_HEADERS)
    if referer:
        headers["Referer"] = referer
    r = safe_get(url, headers=headers, stream=stream)
    if r and r.status_code == 200 and _is_pdf_response(r):
        return r
    return None

def _maybe_fix_biorxiv(url):
    # bioRxiv/medRxiv often require ?download=1/true on the "full.pdf"
    if "biorxiv.org" in url or "medrxiv.org" in url:
        if "full.pdf" in url and "download=" not in url:
            return url + ("&download=true" if "?" in url else "?download=true")
    return url

def _maybe_fix_mdpi(url):
    # MDPI frequently blocks without explicit download param; this sometimes helps.
    if "mdpi.com" in url and "pdf" in url and "download=" not in url:
        return url + ("&download=1" if "?" in url else "?download=1")
    return url

def _domain_referer_for(url):
    # Some hosts want a same-site Referer; provide a sensible default root referer.
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"

def _try_domain_hints(url):
    # Apply domain-specific tweaks and try again
    candidates = []
    # bioRxiv/medRxiv
    candidates.append(_maybe_fix_biorxiv(url))
    # MDPI
    candidates.append(_maybe_fix_mdpi(url))
    # De-dup
    cand_unique = []
    for c in candidates:
        if c and c not in cand_unique:
            cand_unique.append(c)
    for c in cand_unique:
        if c != url:
            ref = _domain_referer_for(c)
            r = _try_get_pdf(c, referer=ref)
            if r:
                return c
    return None

def _pmc_pdf_from_pmcid(pmc_id):
    # Try common PMC PDF endpoints
    paths = [
        f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/pdf/",
        f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/pdf/PMC{pmc_id}.pdf",
        f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/bin/PMC{pmc_id}.pdf",
    ]
    for p in paths:
        r = _try_get_pdf(p)
        if r:
            return p
    return None

def _unpaywall_pdf(doi):
    if not doi:
        return None
    url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    r = safe_get(url, headers=BASE_HEADERS)
    if r and r.status_code == 200:
        try:
            data = r.json()
            oa = (data.get("best_oa_location") or {}).get("url_for_pdf")
            if oa:
                # Some OA URLs still need the domain fixes
                fixed = _try_domain_hints(oa) or oa
                rr = _try_get_pdf(fixed, referer=_domain_referer_for(fixed))
                if rr:
                    logging.info(f"Found via Unpaywall: {fixed}")
                    return fixed
        except Exception:
            pass
    return None

def _core_pdf(doi):
    if not doi or not CORE_KEY:
        return None
    url = f"https://api.core.ac.uk/v3/search/works?query=doi:{doi}&apiKey={CORE_KEY}"
    r = safe_get(url, headers=BASE_HEADERS)
    if r and r.status_code == 200:
        try:
            data = r.json()
            if data.get("results"):
                dl = data["results"][0].get("downloadUrl") or data["results"][0].get("fullTextIdentifier")
                if dl:
                    fixed = _try_domain_hints(dl) or dl
                    rr = _try_get_pdf(fixed, referer=_domain_referer_for(fixed))
                    if rr:
                        logging.info(f"Found via CORE: {fixed}")
                        return fixed
        except Exception:
            pass
    return None

def _openalex_pdf(doi):
    if not doi:
        return None
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    r = safe_get(url, headers=BASE_HEADERS)
    if r and r.status_code == 200:
        try:
            data = r.json()
            primary = data.get("primary_location") or {}
            # Prefer explicit PDF URL if available
            pdf_url = primary.get("pdf_url")
            if not pdf_url:
                # Fall back to source URL (often a landing page; domain hints may still help)
                pdf_url = (primary.get("source") or {}).get("url")
            if pdf_url:
                fixed = _try_domain_hints(pdf_url) or pdf_url
                rr = _try_get_pdf(fixed, referer=_domain_referer_for(fixed))
                if rr:
                    logging.info(f"Found via OpenAlex: {fixed}")
                    return fixed
        except Exception:
            pass
    return None

def _crossref_pdf(doi):
    if not doi:
        return None
    url = f"https://api.crossref.org/works/{doi}"
    r = safe_get(url, headers=BASE_HEADERS)
    if r and r.status_code == 200:
        try:
            data = r.json().get("message", {})
            for link in data.get("link", []):
                if link.get("content-type", "").lower() == "application/pdf":
                    pdf = link.get("URL")
                    if pdf:
                        fixed = _try_domain_hints(pdf) or pdf
                        rr = _try_get_pdf(fixed, referer=_domain_referer_for(fixed))
                        if rr:
                            logging.info(f"Found via CrossRef: {fixed}")
                            return fixed
        except Exception:
            pass
    return None

def _fetch_pdf_via_browser(url):
    """
    Use Playwright to visit a landing page (e.g., DOI), sniff a direct .pdf link,
    and return an absolute URL if found. We do not download the PDF here.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logging.warning("Browser fallback skipped: Playwright not installed.")
        return None

    try:
        logging.info(f"Using Playwright to probe: {url}")
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT_MS)

            # Try to find an <a> that looks like a direct PDF
            anchors = page.query_selector_all("a[href]")
            pdf_href = None
            for a in anchors:
                href = a.get_attribute("href") or ""
                if href.lower().endswith(".pdf") or "pdf" in href.lower():
                    pdf_href = href
                    break

            # Try <meta> tags as well
            if not pdf_href:
                metas = page.query_selector_all("meta[content]")
                for m in metas:
                    content = (m.get_attribute("content") or "").lower()
                    if content.endswith(".pdf") or ("pdf" in content and "http" in content):
                        pdf_href = m.get_attribute("content")
                        break

            final = None
            if pdf_href:
                final = urljoin(page.url, pdf_href)

            browser.close()

        if final:
            # Validate it looks retrievable as PDF
            rr = _try_get_pdf(final, referer=_domain_referer_for(final))
            if rr:
                logging.info(f"Found via browser: {final}")
                return final
            # Domain hints on the discovered URL
            fixed = _try_domain_hints(final) or final
            rr2 = _try_get_pdf(fixed, referer=_domain_referer_for(fixed))
            if rr2:
                logging.info(f"Found via browser (fixed): {fixed}")
                return fixed
        return None
    except Exception as e:
        logging.warning(f"Browser fallback failed: {e}")
        return None

def resolve_pdf_url(paper, use_browser_fallback=True):
    """
    Return a direct, fetchable PDF URL for the given paper metadata dict.
    Resolution order:
      1) Provided openAccessPdf.url (with domain-specific fixes)
      2) PubMed Central by PMCID
      3) Unpaywall
      4) CORE
      5) OpenAlex
      6) CrossRef
      7) Playwright browser fallback on DOI landing page (optional)
    All successful resolutions are cached by DOI.
    """
    external = (paper.get("externalIds") or {})
    doi = external.get("DOI")
    pmcid = external.get("PubMedCentral")
    direct = (paper.get("openAccessPdf") or {}).get("url")

    # Cache lookup
    if doi and doi in _CACHE:
        return _CACHE[doi]

    # 1) Direct openAccessPdf.url, with domain tweaks
    if direct:
        ref = _domain_referer_for(direct)
        # Try raw
        r = _try_get_pdf(direct, referer=ref)
        if r:
            if doi:
                _CACHE[doi] = direct
                _save_cache(_CACHE)
            return direct
        # Try domain-specific alternates
        fixed = _try_domain_hints(direct)
        if fixed:
            if doi:
                _CACHE[doi] = fixed
                _save_cache(_CACHE)
            return fixed

    # 2) PubMed Central by PMCID
    if pmcid:
        pmc_pdf = _pmc_pdf_from_pmcid(pmcid)
        if pmc_pdf:
            if doi:
                _CACHE[doi] = pmc_pdf
                _save_cache(_CACHE)
            return pmc_pdf

    # 3) Unpaywall
    up = _unpaywall_pdf(doi)
    if up:
        if doi:
            _CACHE[doi] = up
            _save_cache(_CACHE)
        return up

    # 4) CORE
    core = _core_pdf(doi)
    if core:
        if doi:
            _CACHE[doi] = core
            _save_cache(_CACHE)
        return core

    # 5) OpenAlex
    oa = _openalex_pdf(doi)
    if oa:
        if doi:
            _CACHE[doi] = oa
            _save_cache(_CACHE)
        return oa

    # 6) CrossRef
    cr = _crossref_pdf(doi)
    if cr:
        if doi:
            _CACHE[doi] = cr
            _save_cache(_CACHE)
        return cr

    # 7) Playwright browser fallback on DOI landing page
    if use_browser_fallback and doi:
        landing = f"https://doi.org/{doi}"
        via_browser = _fetch_pdf_via_browser(landing)
        if via_browser:
            if doi:
                _CACHE[doi] = via_browser
                _save_cache(_CACHE)
            return via_browser

    logging.warning(f"No PDF found for {paper.get('title', '(untitled)')}")
    return None
