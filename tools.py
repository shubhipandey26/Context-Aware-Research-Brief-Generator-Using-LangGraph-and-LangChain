
from typing import List, Dict
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

def web_search(query: str, k: int = 6) -> List[Dict]:
    out = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=k):
            out.append({
                "title": r.get("title",""),
                "url": r.get("href",""),
                "snippet": r.get("body","")
            })
    return out

def fetch_page_text(url: str, timeout: int = 10) -> str:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        return "\n".join(paras)[:18000]
    except Exception:
        return ""
