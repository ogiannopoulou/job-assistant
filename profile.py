"""Profile — dynamically loads from profile_data.json, falls back to RAW_PROFILE."""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PROFILE_PATH = Path(__file__).parent / "profile_data.json"
PORTFOLIO_BASE = Path(os.path.expanduser("~/Documents/p9_portfolgio"))

RAW_PROFILE = {
    "name": "Demo User",
    "email": "user@example.com",
    "phone": "+39 389 122 9284",
    "location": "Rome, Italy",
    "languages": {"Italian": "native", "English": "B2", "German": "B2"},
    "education": [
        {"degree": "Master's Degree in Law (LMG/01)", "institution": "Sapienza University of Rome", "year": 2015,
         "thesis": "Local Public Transport and Sustainable Mobility"},
        {"degree": "Academic Exchange Year", "institution": "Humboldt Universität Berlin (Germany)", "year": 2013,
         "thesis": ""},
        {"degree": "High School Diploma (Classical Studies)", "institution": "Liceo T.L. Caro, Rome", "year": 2002,
         "thesis": ""},
    ],
    "experience": [
        {"role": "Legal-Administrative Officer", "institution": "Ministry of Justice - Court of Viterbo",
         "period": "2025 – Present",
         "topics": ["Legal procedures", "Certification", "Public records", "Trial office management",
                    "Document analysis", "Administrative law"],
         "collaborators": []},
        {"role": "Sales and Customer Service Manager", "institution": "Archegonia Flowers, Rome",
         "period": "2015 – 2023",
         "topics": ["Sales management", "Customer relationship management", "Negotiation",
                    "Order management", "Supplier relations", "After-sales support",
                    "Sales targets", "Customer loyalty"],
         "collaborators": []},
        {"role": "Sales Representative", "institution": "Free Way s.r.l.",
         "period": "2010 – 2012",
         "topics": ["Product promotion", "Customer experience", "Sales goals",
                    "Communication", "Product presentations"],
         "collaborators": []},
        {"role": "Sales Assistant", "institution": "Unieuro s.p.a.",
         "period": "2009",
         "topics": ["Customer assistance", "Product specifications", "IT/Home Entertainment sales",
                    "Retail sales"],
         "collaborators": []},
    ],
    "technical_skills": {
        "legal_administrative": ["Legal procedures", "Certification services", "Public records",
                                  "Administrative law", "Document analysis", "Trial office operations"],
        "sales_customer_service": ["Sales management", "CRM", "Negotiation", "Customer loyalty",
                                   "After-sales support", "Supplier relations", "Order management",
                                   "Sales targets achievement"],
        "it_tools": ["Microsoft Office", "Windows", "Mac OS", "Electronic invoicing"],
        "soft_skills": ["Communication", "Problem-solving", "Organization", "Time management",
                        "Multitasking", "Teamwork"],
        "languages": ["Italian (native)", "English (B2)", "German (B2)"],
        "other": ["Cycling tour guide", "Driving license B", "Boating license"],
    },
    "publications": [],
    "target_roles": [
        "Legal-Administrative Officer / Civil Servant",
        "Sales Manager / Account Manager",
        "Customer Service Manager",
        "Legal Consultant / Paralegal",
        "Administrative Coordinator",
        "Public Administration Specialist",
    ],
    "target_companies_institutions": [
        "Ministry of Justice", "Italian Public Administration",
        "Law firms", "Consulting firms (legal/admin)",
        "Private companies (sales, admin, customer service)",
        "EU institutions",
    ],
    "preferences": {
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
    },
}


def load_projects_inventory():
    path = DATA_DIR / "projects_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def load_skill_inventory():
    path = DATA_DIR / "skill_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def load_cv_inventory():
    path = DATA_DIR / "cv_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def load_github():
    path = DATA_DIR / "github_repos.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def load_profile() -> dict:
    if PROFILE_PATH.exists():
        with open(PROFILE_PATH) as f:
            profile = json.load(f)
    else:
        profile = dict(RAW_PROFILE)
    profile["_projects"] = load_projects_inventory()
    profile["_skills"] = load_skill_inventory()
    profile["_cvs"] = load_cv_inventory()
    profile["_github"] = load_github()
    resolved = []
    for proj in profile.get("portfolio_projects", []):
        proj_path = proj.get("path", "")
        abs_path = str(PORTFOLIO_BASE / proj_path) if not proj_path.startswith("/") else proj_path
        exists = os.path.exists(abs_path)
        resolved.append({**proj, "path": abs_path, "exists": exists})
    profile["portfolio_projects"] = resolved
    if "cv_files" not in profile:
        cached_cvs = load_cv_inventory()
        if cached_cvs:
            profile["cv_files"] = {cv["cv_key"]: cv["path"] for cv in cached_cvs}
        else:
            from cv_parser import scan_all_cvs, save_results
            cvs = scan_all_cvs()
            save_results(cvs)
            profile["cv_files"] = {cv["cv_key"]: cv["path"] for cv in cvs}
        save_profile(profile)
    return profile


def save_profile(profile: dict):
    core = {k: v for k, v in profile.items() if not k.startswith("_")}
    with open(PROFILE_PATH, "w") as f:
        json.dump(core, f, indent=2)


def update_profile(fields: dict) -> dict:
    p = load_profile()
    for key, value in fields.items():
        if key in ("_projects", "_skills", "_cvs", "_github"):
            continue
        p[key] = value
    save_profile(p)
    return load_profile()


def summarize() -> str:
    p = load_profile()
    cv_keys = list(p.get('cv_files', {}).keys())
    projects = p.get("_projects", [])
    skills = p.get("_skills", {})
    github = p.get("_github", [])

    lines = [
        f"Name: {p['name']}",
        f"Location: {p['location']}",
        f"Email: {p['email']}",
        "",
        "Education:",
        *[f"  - {e['degree']}, {e['institution']} ({e['year']})" for e in p['education']],
        "",
        "Experience:",
        *[f"  - {e['role']} @ {e['institution']} ({e['period']})" for e in p['experience']],
        "",
        "Core Skills:",
        f"  Legal/Admin: {', '.join(p['technical_skills']['legal_administrative'][:4])}",
        f"  Sales/CS: {', '.join(p['technical_skills']['sales_customer_service'][:4])}",
        f"  IT Tools: {', '.join(p['technical_skills']['it_tools'])}",
        "",
        f"Publications: {len(p['publications'])}",
        f"Projects scanned: {len(projects)}",
        f"Skills in inventory: {len(skills)}",
        f"GitHub repos: {len(github)}",
        f"CV versions: {len(cv_keys)}",
        "",
        "Target Roles:",
        *[f"  - {r}" for r in p['target_roles']],
        "",
        "Preferences:",
        *summarize_preferences(p.get("preferences", {})),
    ]
    return "\n".join(lines)


def summarize_preferences(prefs: dict = None) -> list:
    if prefs is None:
        p = load_profile()
        prefs = p.get("preferences", {})
    if not prefs:
        return ["  (not set)"]
    lines = []
    label_map = {
        "remote": "Remote preferred",
        "min_salary_eur": "Min salary (EUR)",
        "eu_mobility": "EU mobility",
        "location_flexibility": "Location flexibility",
        "work_life_balance": "Work-life balance (1-5)",
        "stress_tolerance": "Stress tolerance (1-5)",
        "family_proximity": "Family proximity (1-5)",
        "travel_opportunity": "Travel opportunity (1-5)",
        "prefer_industry": "Prefer industry",
        "prefer_remote_first": "Remote-first preferred",
        "prefer_no_weekends": "No weekends",
        "prefer_flexible_hours": "Flexible hours",
        "max_commute_minutes": "Max commute (min)",
    }
    for key, label in label_map.items():
        val = prefs.get(key)
        if val is not None:
            icon = ""
            if isinstance(val, bool):
                icon = " ✅" if val else " ❌"
            elif isinstance(val, int) and key not in ("min_salary_eur", "max_commute_minutes"):
                icon = " 🔴🔶🟡🟢"[min(val, 4)]
            lines.append(f"  {label}: {val}{icon}")
    return lines


def get_preferences() -> dict:
    p = load_profile()
    return p.get("preferences", RAW_PROFILE.get("preferences", {}))


def set_preference(key: str, value) -> bool:
    p = load_profile()
    if "preferences" not in p:
        p["preferences"] = dict(RAW_PROFILE.get("preferences", {}))
    valid_keys = RAW_PROFILE.get("preferences", {}).keys()
    if key not in valid_keys:
        return False
    if isinstance(value, str):
        if value.lower() in ("true", "yes", "1", "on"):
            value = True
        elif value.lower() in ("false", "no", "0", "off"):
            value = False
        else:
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
    p["preferences"][key] = value
    save_profile(p)
    return True


DEFAULT_SEARCH_CONFIG = {
    "keywords": ["software engineer", "developer", "data scientist"],
    "location": "Remote",
    "enabled_sources": ["linkedin", "indeed", "remoteok", "himalayas", "remotive"],
    "remote_only": False,
}


def get_search_config() -> dict:
    p = load_profile()
    return p.get("search_config", dict(DEFAULT_SEARCH_CONFIG))


def save_search_config(config: dict) -> bool:
    p = load_profile()
    p["search_config"] = config
    save_profile(p)
    return True


if __name__ == "__main__":
    print(summarize())
