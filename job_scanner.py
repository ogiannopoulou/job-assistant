"""Multi-source job scanner — tailored for legal/admin/sales profiles in Italy + remote EU."""

import json
import time
import re
import csv
from datetime import date
from urllib.parse import urljoin, urlencode
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

_BASE_FIELDS = ["source", "title", "organization", "location", "deadline", "link",
                "date_found", "remote", "salary_low", "salary_high", "salary_currency",
                "description"]

SALARY_PATTERNS = [
    (r'€\s*(\d+[.,]\d*)\s*[-–to]+\s*€?\s*(\d+[.,]\d*)\s*K?\s*/?\s*(year|yr|annum|annual|p\.?a\.?)', "EUR"),
    (r'€\s*(\d+[.,]\d*)\s*K?\s*/?\s*(year|yr|annum|annual|p\.?a\.?)', "EUR"),
    (r'(\d+[.,]\d*)\s*[-–to]+\s*(\d+[.,]\d*)\s*K?\s*€', "EUR"),
    (r'\$\s*(\d+[.,]\d*)\s*[-–to]+\s*\$?\s*(\d+[.,]\d*)\s*K?\s*/?\s*(year|yr|annum)', "USD"),
    (r'\$\s*(\d+[.,]\d*)\s*K?\s*/?\s*(year|yr|annum)', "USD"),
    (r'GBP\s*(\d+[.,]\d*)\s*[-–to]+\s*GBP?\s*(\d+[.,]\d*)', "GBP"),
    (r'(\d+[.,]\d*)\s*k\s*[-–to]\s*(\d+[.,]\d*)\s*k', "EUR"),
]

SALARY_MULTIPLIERS = {"year": 1, "yr": 1, "annum": 1, "annual": 1, "p.a.": 1, "p.a": 1, "": 1}


def parse_salary(text: str) -> dict:
    if not text:
        return {}
    for pattern, currency in SALARY_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            groups = m.groups()
            if len(groups) >= 2 and groups[1] and any(c in str(groups[1]) for c in "year"):
                low = float(groups[0].replace(",", ".")) * 1000 if "K" in text.upper() else float(groups[0].replace(",", "."))
                high = float(groups[2].replace(",", ".")) * 1000 if len(groups) > 2 and groups[2] and "K" in text.upper() else (float(groups[2].replace(",", ".")) if len(groups) > 2 and groups[2] else low)
                return {"low": low, "high": high, "currency": currency}
            elif len(groups) >= 2:
                low_val = groups[0]
                high_val = groups[1] if len(groups) > 1 else low_val
                if isinstance(high_val, str) and any(c in high_val for c in "year"):
                    continue
                low = float(str(low_val).replace(",", "."))
                high = float(str(high_val).replace(",", "."))
                if "k" in text.lower():
                    low *= 1000
                    high *= 1000
                return {"low": low, "high": high, "currency": currency}
    return {}


# ── LinkedIn ─────────────────────────────────────────
def scan_linkedin(keywords=None, limit=100):
    """LinkedIn — legal/admin/sales keywords targeting Italy + remote EU."""
    if keywords is None:
        keywords = [
            "funzionario+amministrativo", "impiegato+amministrativo",
            "amministrativo", "segreteria", "back+office",
            "legal+officer", "consulente+legale", "paralegal",
            "cancelliere", "giuridico",
            "sales+manager", "account+manager", "commerciale",
            "vendite", "sales+representative",
            "customer+service", "servizio+clienti",
            "responsabile+amministrativo",
            "HR+coordinator", "risorse+umane",
            "compliance+officer", "privacy+officer",
            "concorso+pubblico", "pubblica+amministrazione",
            "export+manager", "logistics+coordinator",
            "office+manager", "operations+manager",
            "customer+success", "key+account",
            "amministrazione+personale",
        ]
    results = []
    seen_jids = set()
    geo_id = "103350119"
    base_url = "https://it.linkedin.com/jobs/search/"
    it_headers = {**HEADERS, "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"}

    for kw in keywords:
        if len(results) >= limit:
            break
        for page in range(3):
            if len(results) >= limit:
                break
            try:
                start = page * 25
                url = f"{base_url}?keywords={kw}&geoId={geo_id}&start={start}"
                resp = SESSION.get(url, timeout=15, headers=it_headers)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("div", class_=re.compile(r"job-search-card"))
                if not cards:
                    break
                for card in cards:
                    jid_match = re.search(r'jobPosting:(\d+)',
                                          card.get("data-entity-urn", ""))
                    jid = jid_match.group(1) if jid_match else ""
                    if not jid or jid in seen_jids:
                        continue
                    seen_jids.add(jid)

                    link_el = card.find("a", class_=re.compile(r"base-card__full-link"))
                    href = link_el.get("href", "").split("?")[0] if link_el else ""

                    title_el = card.find("h3", class_=re.compile(r"base-search-card__title"))
                    title = title_el.get_text(strip=True) if title_el else ""

                    company_el = card.find("h4", class_=re.compile(r"base-search-card__subtitle"))
                    company = company_el.get_text(strip=True) if company_el else ""

                    loc_el = card.find("span", class_=re.compile(r"job-search-card__location"))
                    location = loc_el.get_text(strip=True) if loc_el else ""

                    date_el = card.find("time", class_=re.compile(r"job-search-card__listdate"))
                    date_str = date_el.get("datetime", "") if date_el else ""

                    is_remote = "remote" in location.lower() or "da remoto" in location.lower()
                    results.append({
                        "source": "LinkedIn",
                        "title": title,
                        "organization": company,
                        "location": location,
                        "deadline": "Apply on LinkedIn",
                        "link": href,
                        "date_found": str(date.today()),
                        "remote": "yes" if is_remote else "no",
                        "salary_low": "",
                        "salary_high": "",
                        "salary_currency": "",
                        "description": f"LinkedIn job: {title} at {company} — {location} ({date_str})",
                    })
                time.sleep(0.5)
            except Exception:
                break
    return results


# ── Indeed ───────────────────────────────────────────
def scan_indeed(keywords=None, location="Italy"):
    """Indeed — legal/admin/sales keywords in Italy."""
    if keywords is None:
        keywords = [
            "funzionario amministrativo", "impiegato amministrativo",
            "amministrativo", "segreteria", "back office",
            "consulente legale", "addetto legale",
            "sales manager", "account manager", "commerciale",
            "vendite", "customer service",
            "responsabile amministrativo",
            "HR", "risorse umane",
            "compliance", "privacy",
            "office manager", "operations",
            "export manager",
        ]
    results = []
    for kw in keywords:
        try:
            params = {"q": kw, "l": location, "sort": "date"}
            url = f"https://it.indeed.com/jobs?{urlencode(params)}"
            resp = SESSION.get(url, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.select("[class*='job'], .result")[:15]:
                title_el = card.select_one("a[class*='title'], h2 a, a[data-jk]")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                link = f"https://it.indeed.com{href}" if href.startswith("/") else href
                company_el = card.select_one("[class*='company'], [class*='org']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                is_remote = "remote" in (title + company).lower() or "da remoto" in (title + company).lower()
                desc = card.get_text(" ", strip=True)[:500]
                salary = parse_salary(desc)
                results.append({
                    "source": "Indeed", "title": title, "organization": company,
                    "location": location, "deadline": "Apply directly", "link": link,
                    "date_found": str(date.today()),
                    "remote": "yes" if is_remote else "no",
                    "salary_low": salary.get("low", ""),
                    "salary_high": salary.get("high", ""),
                    "salary_currency": salary.get("currency", ""),
                    "description": desc[:500],
                })
            time.sleep(0.5)
        except Exception:
            pass
    return results


# ── RemoteOK ─────────────────────────────────────────
def scan_remoteok(keywords=None, limit=30):
    """RemoteOK — business/admin/sales keywords for remote EU roles."""
    if keywords is None:
        keywords = ["sales", "account+manager", "customer+service",
                    "customer+success", "administrative", "legal",
                    "compliance", "hr", "operations", "office+manager",
                    "export", "business+development"]
    results = []
    seen = set()
    for kw in keywords:
        if len(results) >= limit:
            break
        try:
            url = f"https://remoteok.com/api?action=search&term={kw}"
            resp = SESSION.get(url, timeout=15,
                               headers={**HEADERS, "Accept": "application/json"})
            if resp.status_code != 200:
                continue
            data = resp.json()
            for job in data[:limit]:
                jid = job.get("id", "")
                if jid in seen:
                    continue
                seen.add(jid)
                title = job.get("position", "")
                company = job.get("company", "")
                desc = (job.get("description", "") or "")[:1000]
                salary = parse_salary((job.get("salary", "") or "") + " " + desc)
                results.append({
                    "source": "RemoteOK", "title": title,
                    "organization": company, "location": "Remote",
                    "deadline": "Apply now", "link": job.get("url", ""),
                    "date_found": str(date.today()), "remote": "yes",
                    "salary_low": salary.get("low", ""),
                    "salary_high": salary.get("high", ""),
                    "salary_currency": salary.get("currency", ""),
                    "description": desc[:500],
                })
            time.sleep(0.5)
        except Exception:
            pass
    return results


# ── Himalayas (EU remote jobs) ──────────────────────
def scan_himalayas(queries=None, limit=30):
    """Himalayas — remote job board with strong EU employer presence."""
    if queries is None:
        queries = ["sales", "customer+support", "administrative", "legal",
                   "hr", "operations", "compliance", "account+manager",
                   "office+manager", "business+development"]
    results = []
    seen = set()
    for q in queries:
        if len(results) >= limit:
            break
        try:
            url = f"https://himalayas.app/jobs/api?query={q}"
            resp = SESSION.get(url, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            for job in data.get("jobs", []):
                jid = job.get("guid", "")
                if not jid or jid in seen:
                    continue
                seen.add(jid)
                title = job.get("title", "")
                company = job.get("companyName", "")
                desc = (job.get("description", "") or "")[:1000]
                location = job.get("candidate_required_location", "") or ""
                loc_restrictions = job.get("locationRestrictions", [])
                loc_str = ", ".join(loc_restrictions) if loc_restrictions else location
                salary_low = job.get("minSalary")
                salary_high = job.get("maxSalary")
                currency = job.get("currency", "")
                is_remote = True
                results.append({
                    "source": "Himalayas", "title": title,
                    "organization": company, "location": loc_str,
                    "deadline": "Apply now", "link": job.get("applicationLink", ""),
                    "date_found": str(date.today()),
                    "remote": "yes" if is_remote else "maybe",
                    "salary_low": salary_low if salary_low else "",
                    "salary_high": salary_high if salary_high else "",
                    "salary_currency": currency if currency else "",
                    "description": desc[:500],
                })
            time.sleep(0.5)
        except Exception:
            pass
    return results


# ── INPA (Italian public administration concorsi) ──
def scan_inpa(keywords=None, limit=50):
    """INPA — Portale Unico del Reclutamento (PA concorsi pubblici)."""
    if keywords is None:
        keywords = ["amministrativo", "funzionario", "istruttore",
                     "amministrazione", "segreteria", "cancelliere",
                     "impiegato", "collaboratore", "contabile",
                     "giuridico", "legale", "compliance"]
    results = []
    seen_ids = set()
    url = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.inpa.gov.it",
        "Referer": "https://www.inpa.gov.it/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    for kw in keywords[:5]:
        if len(results) >= limit:
            break
        for page in range(3):
            if len(results) >= limit:
                break
            try:
                body = {
                    "text": kw,
                    "categoriaId": None,
                    "regioneId": None,
                    "status": ["OPEN"],
                    "settoreId": None,
                    "provinciaCodice": None,
                    "dateFrom": None,
                    "dateTo": None,
                    "livelliAnzianitaIds": None,
                    "tipoImpiegoId": None,
                    "salaryMin": None,
                    "salaryMax": None,
                    "enteRiferimentoName": "",
                }
                resp = requests.post(f"{url}?page={page}&size=4",
                                     json=body, headers=headers, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                items = data.get("content", [])
                if not items:
                    break
                for item in items:
                    item_id = item.get("id", "")
                    if not item_id or item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)
                    title = item.get("titolo", "")
                    enti = item.get("entiRiferimento", [])
                    organization = enti[0] if enti else "PA"
                    sedi = item.get("sedi", [])
                    location = ", ".join(sedi) if sedi else "Italy"
                    scadenza = item.get("dataScadenza", "")
                    desc = item.get("descrizioneBreve", "") or ""
                    fig = item.get("figuraRicercata", "")
                    n_posti = item.get("numPosti", "")
                    deadline = scadenza[:10] if scadenza else "Vedi bando"
                    is_remote = "remote" in (title + desc + fig).lower() or "da remoto" in (title + desc + fig).lower()
                    link = f"https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id={item_id}"
                    results.append({
                        "source": "INPA",
                        "title": (fig or title)[:150],
                        "organization": organization,
                        "location": location,
                        "deadline": deadline,
                        "link": link,
                        "date_found": str(date.today()),
                        "remote": "yes" if is_remote else "maybe",
                        "salary_low": item.get("salaryMin") or "",
                        "salary_high": item.get("salaryMax") or "",
                        "salary_currency": "EUR",
                        "description": BeautifulSoup(desc, "html.parser").get_text(strip=True)[:500] if desc else title[:500],
                        "num_posti": n_posti,
                        "figura_ricercata": fig,
                    })
                time.sleep(0.5)
            except Exception:
                break
    return results


# ── Remotive ─────────────────────────────────────────
def scan_remotive(limit=30):
    """Remotive — remote job board with strong EU presence."""
    results = []
    seen = set()
    categories = ["admin", "customer-service", "sales", "accounting",
                   "hr", "operations", "legal"]
    for cat in categories:
        if len(results) >= limit:
            break
        try:
            url = f"https://remotive.com/api/remote-jobs?category={cat}&limit=20"
            resp = SESSION.get(url, timeout=15,
                               headers={**HEADERS, "Accept": "application/json"})
            if resp.status_code != 200:
                continue
            data = resp.json()
            jobs_data = data.get("jobs", []) if isinstance(data, dict) else data
            if isinstance(data, list):
                jobs_data = data
            for job in jobs_data[:limit]:
                jid = job.get("id", "")
                if jid in seen:
                    continue
                seen.add(jid)
                title = job.get("title", "")
                company = job.get("company_name", "")
                location = job.get("candidate_required_location", "Remote")
                desc = (job.get("description", "") or "")[:1000]
                salary = job.get("salary", "")
                salary_parsed = parse_salary(salary) if salary else {}
                is_remote = True
                results.append({
                    "source": "Remotive", "title": title,
                    "organization": company, "location": location,
                    "deadline": "Apply now", "link": job.get("url", ""),
                    "date_found": str(date.today()),
                    "remote": "yes" if is_remote else "maybe",
                    "salary_low": salary_parsed.get("low", ""),
                    "salary_high": salary_parsed.get("high", ""),
                    "salary_currency": salary_parsed.get("currency", ""),
                    "description": desc[:500],
                })
            time.sleep(0.3)
        except Exception:
            pass
    return results


# ── Aggregator ──────────────────────────────────────
def scan_all(sources=None):
    if sources is None:
        sources = ["linkedin", "indeed", "remoteok", "himalayas", "remotive", "inpa"]
    all_jobs = []
    seen_links = set()

    scanners = {
        "linkedin": lambda: scan_linkedin(),
        "indeed": lambda: scan_indeed(),
        "remoteok": lambda: scan_remoteok(),
        "remotive": lambda: scan_remotive(),
        "himalayas": lambda: scan_himalayas(),
        "inpa": lambda: scan_inpa(),
    }

    for src in sources:
        if src in scanners:
            try:
                jobs = scanners[src]()
                for j in jobs:
                    link = j.get("link", "")
                    if link and link not in seen_links:
                        seen_links.add(link)
                        all_jobs.append(j)
            except Exception:
                pass
    return all_jobs


def get_search_terms():
    try:
        from profile import load_profile
        p = load_profile()
        skills = p["technical_skills"]
        keywords = set()
        for cat in ["legal_administrative", "sales_customer_service", "it_tools", "soft_skills"]:
            for s in skills.get(cat, []):
                keywords.add(s.lower())
        extra = [
            "funzionario amministrativo", "impiegato amministrativo",
            "sales manager", "account manager", "commerciale",
            "customer service", "consulente legale", "legal officer",
            "back office", "segreteria", "amministrazione",
            "compliance", "risorse umane", "HR",
            "office manager", "operations", "export manager",
            "vendite", "concorso pubblico", "pubblica amministrazione",
        ]
        keywords.update(extra)
        return sorted(keywords)
    except Exception:
        return ["amministrativo", "sales", "customer service", "legal"]


def _normalize(jobs):
    normalized = []
    for j in jobs:
        n = {k: j.get(k, "") for k in _BASE_FIELDS}
        for k, v in j.items():
            if k not in n:
                n[k] = v
        normalized.append(n)
    return normalized


def save_results(jobs, filename=None):
    if filename is None:
        filename = DATA_DIR / f"jobs_{date.today()}.csv"
    if not jobs:
        with open(filename, "w") as f:
            f.write("No jobs found\n")
        return filename
    jobs = _normalize(jobs)
    fieldnames = sorted({k for j in jobs for k in j.keys()})
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for j in jobs:
            writer.writerow({k: j.get(k, "") for k in fieldnames})
    return filename


def load_results(filename=None):
    if filename is None:
        files = sorted(DATA_DIR.glob("jobs_*.csv"))
        if not files:
            return []
        filename = files[-1]
    with open(filename, encoding="utf-8") as f:
        return list(csv.DictReader(f))


_EXCLUDED_TITLES = [
    "software engineer", "software developer", "data scientist", "data engineer",
    "machine learning", "devops", "backend", "frontend", "full-stack", "full stack",
    "site reliability", "ios developer", "android developer", "qa engineer",
    "quality engineer", "product engineer", "staff engineer", "principal engineer",
    "tech lead", "engineering manager", "head of engineering", "cloud engineer",
    "security engineer", "ai engineer", "gen-ai", "data engineer", "platform engineer",
    "ruby on rails", "react", "rust", "golang", "python developer", "c++",
    "php developer", "java developer", "infrastructure engineer", "sre",
    "kubernetes", "k8s", "test automation", "manual tester",
]


def is_valid_job(j):
    title = j.get("title", "") or ""
    if len(title) < 5:
        return False
    title_lower = title.lower()

    noisy = ["newest offers first", "sectorhigher education", "countryaustria",
             "countrybelgium", "countrybulgaria", "oldest offers first",
             "filter by", "deadline"]
    if any(n in title_lower for n in noisy):
        return False

    internships = ["stage", "tirocinio", "internship", "intern", "apprendistato",
                   "trainee", "stagiaire", "praktikum"]
    if any(w in title_lower for w in internships):
        return False

    # Exclude irrelevant tech/engineering titles
    if any(excl in title_lower for excl in _EXCLUDED_TITLES):
        return False

    remote = (j.get("remote", "") or "").lower()
    location = (j.get("location", "") or "").lower()
    source = (j.get("source", "") or "")

    if remote == "yes":
        return True

    # INPA = Italian PA concorsi, keep all regardless of location
    if source == "INPA":
        return True

    sacrofano_area = ["sacrofano", "rome", "roma", "lazio", "viterbo",
                      "civitavecchia", "fiumicino", "ciampino", "tivoli",
                      "frascati", "guidonia", "cassia"]
    is_near = any(r in location for r in sacrofano_area)
    if is_near:
        return True

    return False


if __name__ == "__main__":
    import sys
    srcs = sys.argv[1:] if len(sys.argv) > 1 else ["remoteok", "himalayas", "remotive", "inpa"]
    print(f"Scanning: {srcs}")
    jobs = scan_all(srcs)
    valid = [j for j in jobs if is_valid_job(j)]
    print(f"Found {len(jobs)} jobs ({len(valid)} valid)")
    path = save_results(valid)
    print(f"Saved to {path}")
