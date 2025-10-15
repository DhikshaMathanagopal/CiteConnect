import time
import logging
import tls_client

session = tls_client.Session(client_identifier="chrome_120")

def safe_get(url, headers=None, stream=False, retries=3, sleep_base=2):
    headers = headers or {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/120.0 Safari/537.36"}
    for attempt in range(retries):
        try:
            r = session.get(url, headers=headers, timeout_seconds=40)
            if r.status_code == 200:
                time.sleep(0.5)
                return r
            elif r.status_code == 403:
                logging.warning(f"403 Forbidden, retrying with browser headers: {url}")
                time.sleep(sleep_base * (attempt + 1))
            elif r.status_code == 429:
                time.sleep(10 * (attempt + 1))
            else:
                time.sleep(2)
        except Exception as e:
            logging.warning(f"safe_get exception: {e}")
            time.sleep(sleep_base * (attempt + 1))
    logging.error(f"Giving up on {url} after {retries} retries.")
    return None
