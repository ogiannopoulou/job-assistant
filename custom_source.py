"""Custom job sources — users can define their own scrapers."""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent / "data"
CUSTOM_SOURCES_PATH = DATA_DIR / "custom_sources.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

SOURCE_FIELDS = [
    "id", "name", "url_template", "type",
    "card_selector", "title_selector", "company_selector",
    "location_selector", "link_selector", "link_attr",
    "description_selector", "date_selector",
    "json_results_path", "json_title_key", "json_company_key",
    "json_location_key", "json_link_key", "json_description_key",
    "headers", "enabled",
]

DEFAULT_TEMPLATE = {
    "id": "",
    "name": "",
    "url_template": "https://example.com/jobs?q={keywords}",
    "type": "html",
    "card_selector": ".job-card",
    "title_selector": "h2 a",
    "company_selector": ".company",
    "location_selector": ".location",
    "link_selector": "h2 a",
    "link_attr": "href",
    "description_selector": ".description",
    "date_selector": "",
    "json_results_path": "$.jobs",
    "json_title_key": "title",
    "json_company_key": "company",
    "json_location_key": "location",
    "json_link_key": "url",
    "json_description_key": "description",
    "headers": {},
    "enabled": True,
}


def _generate_id(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not base:
        base = "custom"
    existing = {s.get("id") for s in list_sources()}
    n = 1
    candidate = base
    while candidate in existing:
        candidate = f"{base}_{n}"
        n += 1
    return candidate


def list_sources() -> list:
    if CUSTOM_SOURCES_PATH.exists():
        with open(CUSTOM_SOURCES_PATH) as f:
            try:
                return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return []
    return []


def save_sources(sources: list):
    CUSTOM_SOURCES_PATH.parent.mkdir(exist_ok=True)
    with open(CUSTOM_SOURCES_PATH, "w") as f:
        json.dump(sources, f, indent=2)


def add_source(source_def: dict) -> str:
    sources = list_sources()
    sid = source_def.get("id") or _generate_id(source_def.get("name", "custom"))
    source_def["id"] = sid
    clean = {k: source_def.get(k, DEFAULT_TEMPLATE.get(k)) for k in SOURCE_FIELDS}
    clean["enabled"] = source_def.get("enabled", True)
    sources.append(clean)
    save_sources(sources)
    return sid


def update_source(source_id: str, updates: dict) -> bool:
    sources = list_sources()
    for s in sources:
        if s.get("id") == source_id:
            for k, v in updates.items():
                if k in SOURCE_FIELDS:
                    s[k] = v
            save_sources(sources)
            return True
    return False


def delete_source(source_id: str) -> bool:
    sources = list_sources()
    new_sources = [s for s in sources if s.get("id") != source_id]
    if len(new_sources) < len(sources):
        save_sources(new_sources)
        return True
    return False


def scan_custom_source(source_def: dict, keywords: list = None, limit: int = 50) -> list:
    from datetime import date

    if keywords is None:
        try:
            from profile import get_search_config
            keywords = get_search_config().get("keywords", ["software engineer"])
        except Exception:
            keywords = ["software engineer"]

    results = []
    seen_links = set()
    url_template = source_def.get("url_template", "")
    source_type = source_def.get("type", "html")
    custom_headers = source_def.get("headers", {})

    for kw in keywords[:5]:
        if len(results) >= limit:
            break
        try:
            import urllib.parse
            encoded_kw = urllib.parse.quote(kw)
            url = url_template.replace("{keywords}", encoded_kw).replace("{keyword}", encoded_kw)
            headers = {**HEADERS, **custom_headers}
            resp = SESSION.get(url, timeout=15, headers=headers)
            if resp.status_code != 200:
                continue

            if source_type == "json":
                jobs = _parse_json_source(resp.json(), source_def, kw)
            else:
                soup = BeautifulSoup(resp.text, "html.parser")
                jobs = _parse_html_source(soup, source_def, kw)

            for j in jobs:
                link = j.get("link", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    results.append(j)
            time.sleep(0.5)
        except Exception:
            continue

    return results


def _parse_html_source(soup, source_def: dict, keyword: str) -> list:
    from datetime import date
    results = []
    card_sel = source_def.get("card_selector", "")
    if not card_sel:
        return results

    cards = soup.select(card_sel)[:20]
    for card in cards:
        title = _select_text(card, source_def.get("title_selector", ""))
        company = _select_text(card, source_def.get("company_selector", ""))
        location = _select_text(card, source_def.get("location_selector", ""))
        link = _select_attr(card, source_def.get("link_selector", ""), source_def.get("link_attr", "href"))
        desc = _select_text(card, source_def.get("description_selector", "")) or title
        date_str_val = _select_text(card, source_def.get("date_selector", ""))

        if not title:
            continue
        if link and link.startswith("/"):
            link = _abs_url(source_def.get("url_template", ""), link)

        is_remote = "remote" in (title + " " + location + " " + company).lower()
        results.append({
            "source": source_def.get("name", "Custom"),
            "title": title.strip()[:200],
            "organization": company.strip()[:200],
            "location": location.strip()[:100],
            "deadline": "Check site",
            "link": link,
            "date_found": str(date.today()),
            "remote": "yes" if is_remote else "no",
            "salary_low": "",
            "salary_high": "",
            "salary_currency": "",
            "description": (desc.strip()[:500] if desc else title),
        })
    return results


def _parse_json_source(data, source_def: dict, keyword: str) -> list:
    from datetime import date
    results = []
    results_path = source_def.get("json_results_path", "$.jobs")
    items = _navigate_json(data, results_path)
    if not isinstance(items, list):
        return results

    for item in items[:20]:
        if not isinstance(item, dict):
            continue
        title = _json_get(item, source_def.get("json_title_key", "title"))
        company = _json_get(item, source_def.get("json_company_key", "company"))
        location = _json_get(item, source_def.get("json_location_key", "location"))
        link = _json_get(item, source_def.get("json_link_key", "url"))
        desc = _json_get(item, source_def.get("json_description_key", "description")) or ""

        if not title:
            continue

        is_remote = "remote" in (str(title) + " " + str(location) + " " + str(company)).lower()
        results.append({
            "source": source_def.get("name", "Custom"),
            "title": str(title)[:200],
            "organization": str(company)[:200] if company else "",
            "location": str(location)[:100] if location else "",
            "deadline": "Check site",
            "link": str(link) if link else "",
            "date_found": str(date.today()),
            "remote": "yes" if is_remote else "no",
            "salary_low": "",
            "salary_high": "",
            "salary_currency": "",
            "description": str(desc)[:500],
        })
    return results


def _select_text(element, selector: str) -> str:
    if not selector:
        return ""
    els = element.select(selector)
    return els[0].get_text(strip=True) if els else ""


def _select_attr(element, selector: str, attr: str) -> str:
    if not selector:
        return ""
    els = element.select(selector)
    return els[0].get(attr, "") if els else ""


def _abs_url(base_url: str, path: str) -> str:
    if path.startswith("http"):
        return path
    import urllib.parse
    base = re.match(r"https?://[^/]+", base_url)
    return base.group(0) + path if base else path


def _navigate_json(data, path: str):
    if not path or path == "$":
        return data
    parts = path.replace("$.", "").split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part, {})
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx] if idx < len(current) else {}
            except ValueError:
                return []
        else:
            return []
    return current


def _json_get(item: dict, key: str) -> str:
    if not key:
        return ""
    parts = key.split(".")
    current = item
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part, "")
        else:
            return ""
    return str(current) if current else ""
