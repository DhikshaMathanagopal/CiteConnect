import logging
import requests
import time
from bs4 import BeautifulSoup
from src.data_pipeline.utils.http_utils import safe_get

def parse_grobid_sections(tei_xml):
    soup = BeautifulSoup(tei_xml, "lxml-xml")
    sections = {}
    for div in soup.find_all("div"):
        head = div.find("head")
        if not head:
            continue
        name = head.get_text(strip=True).lower()
        body_text = " ".join(p.get_text(" ", strip=True) for p in div.find_all("p"))
        if "abstract" in name:
            sections["abstract"] = body_text
        elif "introduction" in name or "background" in name:
            sections["introduction"] = body_text
    return sections

def extract_with_grobid(pdf_url, grobid_url, retries=3):
    for attempt in range(retries):
        r = safe_get(pdf_url, stream=True)
        if not r:
            time.sleep(3)
            continue
        files = {"input": ("paper.pdf", r.content, "application/pdf")}
        resp = requests.post(f"{grobid_url}/api/processFulltextDocument", files=files, timeout=120)
        if resp.status_code == 200:
            sections = parse_grobid_sections(resp.text)
            if sections.get("introduction"):
                return sections, "ok"
            return sections, "no_intro"
        time.sleep(5 * (attempt + 1))
    return None, "grobid_failed"
