"""Job Ranker — scores jobs by personal preferences.
Tailored for legal/administrative/sales profiles in Italy.
"""

import json
import re
from datetime import datetime, date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

TARGET_SALARY_EUR = 40000
SALARY_ANNUAL_MULTIPLIERS = {
    "hour": 2000, "hr": 2000, "/h": 2000,
    "month": 12, "mth": 12,
    "week": 52,
    "day": 260,
}

LOW_STRESS_KEYWORDS = [
    "work-life balance", "flexible hours", "flexible working",
    "autonomous", "self-directed", "healthy work environment",
    "wellness", "supportive", "collaborative", "no bureaucracy",
    "flat hierarchy", "good benefits", "pension", "paid time off",
    "permanent contract", "indeterminato", "tempo indeterminato",
    "stable", "structured", "regular hours", "orario continuato",
    "turni flessibili", "employee wellbeing",
]

HIGH_STRESS_KEYWORDS = [
    "fast-paced", "deadline-driven", "high-pressure", "intense",
    "24/7", "on-call", "overtime required", "work under pressure",
    "tight deadlines", "high growth", "startup", "hustle",
    "always-on", "cut-throat", "commission-only", "provvigioni",
    "partita iva", "freelance", "target aggressivo",
]

INDUSTRY_SIGNALS = [
    "legal", "administrative", "sales", "customer service",
    "manager", "coordinator", "officer", "clerk", "assistant",
    "consultant", "account", "amministrativo", "commerciale",
    "impiegato", "funzionario", "back office", "segreteria",
    "direttore", "responsabile",
]

ACADEMIA_SIGNALS = [
    "research", "university", "professor", "lecturer",
    "phd", "postdoc", "ricercatore", "assegno",
    "teaching", "dipartimento",
]

SACROFANO_AREA = [
    "sacrofano", "rome", "roma", "lazio", "viterbo",
    "civitavecchia", "fiumicino", "ciampino", "tivoli",
    "frascati", "castelli romani", "guidonia", "cassia",
]

ITALY_REGIONS = [
    "rome", "roma", "lazio", "viterbo", "italy", "italia",
    "milan", "milano", "lombardy", "turin", "torino",
    "florence", "firenze", "tuscany", "toscana",
    "naples", "napoli", "campania", "bologna",
]

EUROPE_COUNTRIES = [
    "italy", "italia", "germany", "germania", "france", "francia",
    "spain", "spagna", "netherlands", "paesi bassi", "belgium",
    "belgio", "austria", "switzerland", "svizzera", "uk",
    "united kingdom", "regno unito", "ireland", "irlanda",
    "sweden", "svezia", "denmark", "danimarca", "norway",
    "norvegia", "finland", "finlandia", "portugal", "portogallo",
    "greece", "grecia", "poland", "polonia", "czech",
    "repubblica ceca", "hungary", "ungheria", "croatia",
    "croazia", "slovenia", "slovakia", "romania", "bulgaria",
    "estonia", "latvia", "lithuania", "luxembourg", "malta",
    "europe", "europa", "eu",
]

DEFAULT_PREFS = {
    "remote": True,
    "min_salary_eur": 35000,
    "eu_mobility": False,
    "location_flexibility": "europe_remote_or_sacrofano_100km",
    "work_life_balance": 4,
    "stress_tolerance": 3,
    "family_proximity": 4,
    "travel_opportunity": 3,
    "prefer_industry": True,
    "prefer_remote_first": True,
    "prefer_no_weekends": True,
    "prefer_flexible_hours": True,
    "max_commute_minutes": 90,
}


def _load_prefs() -> dict:
    try:
        from profile import get_preferences
        prefs = get_preferences()
        if prefs:
            return prefs
    except Exception:
        pass
    return dict(DEFAULT_PREFS)


def load_inventory() -> dict:
    path = DATA_DIR / "skill_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def score_remote(job: dict, prefs: dict = None) -> int:
    if prefs is None:
        prefs = _load_prefs()
    remote = job.get("remote", "").lower()
    loc = job.get("location", "").lower()
    title_desc = (job.get("title", "") + " " + job.get("description", "")).lower()

    is_remote = remote == "yes" or any(w in title_desc for w in
        ["remote", "fully remote", "100% remote", "work from home", "work from anywhere",
         "remote-first", "distributed", "telework", "home office", "da remoto",
         "smart working", "lavoro agile"])
    is_hybrid = remote == "maybe" or any(w in title_desc for w in
        ["hybrid", "partially remote", "flexible location", "ibrido"])
    is_near_sacrofano = any(r in loc for r in SACROFANO_AREA)
    in_europe = any(c in loc for c in EUROPE_COUNTRIES)

    if prefs.get("remote", True):
        if is_remote:
            return 30
        elif is_hybrid:
            if is_near_sacrofano:
                return 25
            else:
                return 5
        else:
            if is_near_sacrofano:
                return 15
            elif in_europe:
                return 8
            return 0
    else:
        if is_remote:
            return 10
        elif is_hybrid:
            return 15
        return 25


def score_salary(job: dict, prefs: dict = None) -> float:
    if prefs is None:
        prefs = _load_prefs()
    target = prefs.get("min_salary_eur", TARGET_SALARY_EUR)

    low = job.get("salary_low", "")
    high = job.get("salary_high", "")
    currency = job.get("salary_currency", "")
    try:
        low = float(low) if low else 0
        high = float(high) if high else low
    except (ValueError, TypeError):
        return 0

    if currency == "USD":
        low *= 0.92
        high *= 0.92
    elif currency == "GBP":
        low *= 1.17

    avg = (low + high) / 2
    if avg == 0:
        return 10

    ratio = avg / target
    if ratio >= 1.5:
        return 30
    elif ratio >= 1.2:
        return 25
    elif ratio >= 1.0:
        return 20
    elif ratio >= 0.8:
        return 15
    elif ratio >= 0.6:
        return 5
    else:
        return -5


def score_lifestyle(job: dict) -> int:
    text = (job.get("title", "") + " " + job.get("organization", "") + " "
            + job.get("description", "")).lower()

    low_stress_hits = sum(1 for kw in LOW_STRESS_KEYWORDS if kw in text)
    high_stress_hits = sum(1 for kw in HIGH_STRESS_KEYWORDS if kw in text)

    score = (low_stress_hits * 5) - (high_stress_hits * 8)
    score = max(-20, min(30, score))

    if low_stress_hits == 0 and high_stress_hits == 0:
        score = 5

    return score


def score_location(job: dict, prefs: dict = None) -> int:
    if prefs is None:
        prefs = _load_prefs()

    loc = job.get("location", "").lower()
    org = job.get("organization", "").lower()
    remote = job.get("remote", "").lower()
    title_desc = (job.get("title", "") + " " + job.get("description", "")).lower()

    is_remote = remote == "yes" or "remote" in title_desc
    is_near_sacrofano = any(r in loc for r in SACROFANO_AREA)
    is_italy = any(i in loc for i in ITALY_REGIONS)
    in_europe = any(c in loc for c in EUROPE_COUNTRIES)

    if prefs.get("remote", True) and is_remote:
        # Full remote — location doesn't matter
        return 20
    if is_near_sacrofano:
        return 25
    if is_italy:
        return 18
    if in_europe:
        return 12
    if is_remote:
        return 15
    return 5


def score_sector(job: dict, prefs: dict = None) -> int:
    if prefs is None:
        prefs = _load_prefs()
    text = (job.get("title", "") + " " + job.get("organization", "") + " "
            + job.get("description", "")).lower()
    source = job.get("source", "").lower()
    org = job.get("organization", "").lower()

    industry_score = sum(1 for s in INDUSTRY_SIGNALS if s in text)
    academia_score = sum(1 for s in ACADEMIA_SIGNALS if s in text)

    if source in ("linkedin", "indeed"):
        industry_score += 2
    if source in ("euraxess", "mur"):
        academia_score += 3
    if any(s in org for s in ["university", "università", "cnr", "ingv"]):
        academia_score += 2

    if prefs.get("prefer_industry", True):
        return min(15, industry_score * 3 - academia_score * 2)
    else:
        return min(15, academia_score * 3 - industry_score * 2)


def score_skill_fit(job: dict, inv: dict = None) -> float:
    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    if inv is None:
        inv = load_inventory()
    if not inv:
        return 15
    matched = 0
    total = 0
    for skill_name, data in inv.items():
        if data.get("project_count", 0) == 0 and data.get("cv_count", 0) == 0:
            continue
        total += 1
        if skill_name.lower() in text:
            matched += 1
    if total == 0:
        return 15
    ratio = matched / total
    if ratio >= 0.5:
        return 25
    elif ratio >= 0.3:
        return 18
    elif ratio >= 0.1:
        return 10
    else:
        return 3


def score_urgency(job: dict) -> int:
    deadline = job.get("deadline", "").strip().lower()
    if not deadline or deadline in ("check link", "apply directly", "apply now", "unknown", "apply on linkedin"):
        return 5
    try:
        dl = None
        formats = ["%d/%m/%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y",
                   "%d %B %Y - %H:%M", "%d %b %Y - %H:%M"]
        for fmt in formats:
            try:
                dl = datetime.strptime(deadline.split(" - ")[0].split(" (")[0], fmt).date()
                break
            except ValueError:
                continue
        if dl:
            days = (dl - date.today()).days
            if days < 0:
                return 0
            elif days <= 7:
                return 8
            elif days <= 30:
                return 6
            elif days <= 90:
                return 4
            else:
                return 2
    except Exception:
        pass
    return 5


def rank_job(job: dict, inv: dict = None, prefs: dict = None) -> dict:
    if inv is None:
        inv = load_inventory()
    if prefs is None:
        prefs = _load_prefs()

    remote_s = score_remote(job, prefs)
    salary_s = score_salary(job, prefs)
    lifestyle_s = score_lifestyle(job)
    location_s = score_location(job, prefs)
    sector_s = score_sector(job, prefs)
    skill_s = score_skill_fit(job, inv)
    urgency_s = score_urgency(job)

    wlb_weight = prefs.get("work_life_balance", 3) / 3
    lifestyle_weighted = int(lifestyle_s * wlb_weight)

    stress_sensitivity = 1 + (5 - prefs.get("stress_tolerance", 3)) / 2
    stress_penalty = min(0, lifestyle_weighted - lifestyle_s) if lifestyle_s < 0 else 0
    stress_penalty = int(stress_penalty * stress_sensitivity)

    total = remote_s + salary_s + lifestyle_weighted + stress_penalty + location_s + sector_s + skill_s + urgency_s

    scores = {
        "remote_score": remote_s,
        "salary_score": salary_s,
        "lifestyle_score": lifestyle_s,
        "lifestyle_weighted": lifestyle_weighted,
        "stress_penalty": stress_penalty,
        "location_score": location_s,
        "sector_score": sector_s,
        "skill_fit_score": skill_s,
        "urgency_score": urgency_s,
        "total_score": total,
    }
    return scores


def rank_jobs(jobs: list, inv: dict = None, prefs: dict = None) -> list:
    if inv is None:
        inv = load_inventory()
    if prefs is None:
        prefs = _load_prefs()
    ranked = []
    for j in jobs:
        scores = rank_job(j, inv, prefs)
        ranked.append({**j, "_scores": scores})
    return sorted(ranked, key=lambda x: x["_scores"]["total_score"], reverse=True)


def get_top_n(jobs: list, n: int = 15) -> list:
    ranked = rank_jobs(jobs)
    return ranked[:n]


def format_ranked(jobs: list) -> str:
    lines = []
    headers = f"{'#':>2} {'Score':>4} {'Title':<55} {'Remote':<7} {'Loc':<8} {'Sector':<8}"
    lines.append(headers)
    lines.append("-" * len(headers))
    for i, j in enumerate(jobs[:25], 1):
        s = j.get("_scores", {})
        total = s.get("total_score", 0)
        remote = j.get("remote", "?")
        loc = j.get("location", "?")[:8]
        org = j.get("organization", "?")[:22]
        sector_hint = "🏭" if s.get("sector_score", 0) > 0 else "🎓"

        color = ""
        if total >= 80:
            color = "🟢"
        elif total >= 50:
            color = "🟡"
        elif total >= 30:
            color = "🟠"
        else:
            color = "🔴"

        lines.append(
            f"{i:2d} {color}{total:4d} {j.get('title', '?')[:55]} "
            f"{remote:<7} {loc:<8} {sector_hint}"
        )
        lines.append(
            f"    {org} "
            f"R:{s.get('remote_score',0)} Sal:{s.get('salary_score',0)} "
            f"Life:{s.get('lifestyle_score',0)} Loc:{s.get('location_score',0)} "
            f"Sec:{s.get('sector_score',0)} Fit:{s.get('skill_fit_score',0)}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    from job_scanner import load_results
    jobs = load_results()
    valid = [j for j in jobs if j.get("title", "") and len(j["title"]) > 5]
    ranked = rank_jobs(valid)
    print(f"Ranked {len(ranked)} jobs by YOUR preferences:")
    print(format_ranked(ranked))

    print("\n--- Top Picks ---")
    for j in ranked[:3]:
        s = j["_scores"]
        print(f"\n{j['title'][:70]}")
        print(f"  @ {j.get('organization', '?')} — {j.get('location', '?')}")
        print(f"  Total: {s['total_score']} | Remote:{s['remote_score']} Salary:{s['salary_score']} "
              f"Lifestyle:{s['lifestyle_score']} Location:{s['location_score']} "
              f"Sector:{s['sector_score']} Skill:{s['skill_fit_score']}")
