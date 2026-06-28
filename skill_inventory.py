"""Skill Inventory — merges all skill sources into a unified queryable database."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

SKILL_NORMALIZE = {
    "legal": "Legal Procedures",
    "legal procedures": "Legal Procedures",
    "administrative": "Administrative Skills",
    "administrative law": "Administrative Law",
    "sales": "Sales Management",
    "sales management": "Sales Management",
    "crm": "CRM",
    "customer relationship management": "CRM",
    "negotiation": "Negotiation",
    "customer service": "Customer Service",
    "customer loyalty": "Customer Loyalty",
    "after-sales support": "After-Sales Support",
    "supplier relations": "Supplier Relations",
    "order management": "Order Management",
    "sales targets": "Sales Targets Achievement",
    "microsoft office": "Microsoft Office",
    "office": "Microsoft Office",
    "excel": "Microsoft Excel",
    "word": "Microsoft Word",
    "powerpoint": "Microsoft PowerPoint",
    "windows": "Windows",
    "mac os": "Mac OS",
    "electronic invoicing": "Electronic Invoicing",
    "communication": "Communication",
    "problem-solving": "Problem Solving",
    "organization": "Organization",
    "time management": "Time Management",
    "multitasking": "Multitasking",
    "teamwork": "Teamwork",
    "certification": "Certification Services",
    "public records": "Public Records",
    "document analysis": "Document Analysis",
    "trial office": "Trial Office Operations",
    "compliance": "Compliance",
    "gdpr": "GDPR",
    "concorsi": "Public Administration Concorsi",
    "public administration": "Public Administration",
    "export": "Export Management",
    "account management": "Account Management",
    "bilingual": "Bilingual Skills",
    "trilingual": "Trilingual Skills",
    "german": "German Language",
    "english": "English Language",
    "italian": "Italian Language",
}

SKILL_CATEGORIES = {
    "legal_administrative": ["Legal Procedures", "Administrative Law", "Certification Services",
                             "Public Records", "Document Analysis", "Trial Office Operations",
                             "Compliance", "GDPR", "Public Administration",
                             "Public Administration Concorsi", "Contract Management"],
    "sales_customer_service": ["Sales Management", "CRM", "Negotiation", "Customer Service",
                                "Customer Loyalty", "After-Sales Support", "Supplier Relations",
                                "Order Management", "Sales Targets Achievement", "Account Management",
                                "Export Management"],
    "it_tools": ["Microsoft Office", "Microsoft Excel", "Microsoft Word", "Microsoft PowerPoint",
                 "Windows", "Mac OS", "Electronic Invoicing", "SAP"],
    "soft_skills": ["Communication", "Problem Solving", "Organization", "Time Management",
                    "Multitasking", "Teamwork", "Leadership", "Presentation"],
    "languages": ["Italian Language", "English Language", "German Language", "Bilingual Skills",
                  "Trilingual Skills"],
    "transportation": ["Driving License B", "Boating License"],
}


def normalize_skill(name: str) -> str:
    n = name.strip().lower()
    return SKILL_NORMALIZE.get(n, name.strip())


def load_projects() -> list:
    path = DATA_DIR / "projects_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def load_cvs() -> list:
    path = DATA_DIR / "cv_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def load_github() -> list:
    path = DATA_DIR / "github_repos.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def build_inventory() -> dict:
    projects = load_projects()
    cvs = load_cvs()
    github = load_github()

    skills = {}

    def add_skill(name: str, source_type: str, source_name: str, category: str = None):
        n = normalize_skill(name)
        if not n:
            return
        if n not in skills:
            skills[n] = {
                "name": n,
                "categories": set(),
                "sources": [],
                "project_count": 0,
                "cv_count": 0,
                "github_count": 0,
                "priority": 0,
            }
        if category:
            skills[n]["categories"].add(category)
        skills[n]["sources"].append({"type": source_type, "name": source_name})
        if source_type == "project":
            skills[n]["project_count"] += 1
        elif source_type == "cv":
            skills[n]["cv_count"] += 1
        elif source_type == "github":
            skills[n]["github_count"] += 1

    for p in projects:
        pname = p.get("name", "?")
        for tech in p.get("tech_stack", []):
            add_skill(tech, "project", pname)

    for cv in cvs:
        cv_key = cv.get("cv_key", "?")
        for cat, skill_list in cv.get("skills", {}).items():
            for s in skill_list:
                add_skill(s, "cv", cv_key, cat)

    for repo in github:
        rname = repo.get("name", "?")
        for lang in repo.get("languages", {}):
            add_skill(lang, "github", rname)

    for skill_name, data in skills.items():
        lower = skill_name.lower()
        for cat, members in SKILL_CATEGORIES.items():
            if any(m.lower() == lower for m in members):
                data["categories"].add(cat)

    for data in skills.values():
        data["priority"] = data["project_count"] * 3 + data["cv_count"] * 2 + data["github_count"]
        data["categories"] = sorted(data["categories"])

    return dict(sorted(skills.items(), key=lambda x: -x[1]["priority"]))


def save_inventory(inv: dict = None):
    if inv is None:
        inv = build_inventory()
    path = DATA_DIR / "skill_inventory.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2, default=str)
    print(f"Saved {len(inv)} skills to {path}")
    return path


def load_inventory() -> dict:
    path = DATA_DIR / "skill_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def get_skills_by_category(category: str = None) -> dict:
    inv = load_inventory()
    if not category:
        return inv
    return {k: v for k, v in inv.items() if category in v.get("categories", [])}


def match_job_skills(job_title: str, job_desc: str, inv: dict = None) -> dict:
    if inv is None:
        inv = load_inventory()
    text = (job_title + " " + job_desc).lower()
    matched = {}
    for skill_name, data in inv.items():
        if skill_name.lower() in text:
            matched[skill_name] = data
    return matched


def get_gaps(inv: dict = None) -> list:
    if inv is None:
        inv = load_inventory()
    gaps = []
    for name, data in inv.items():
        if data["project_count"] == 0 and data["cv_count"] > 0:
            gaps.append({"skill": name, "reason": "In CV but no project — consider building one"})
        if data["cv_count"] == 0 and data["project_count"] > 0:
            gaps.append({"skill": name, "reason": "In projects but not in CV — update your CV"})
    return gaps


def get_summary() -> str:
    inv = load_inventory()
    if not inv:
        return "No skill inventory yet."
    by_cat = {}
    for name, data in inv.items():
        for cat in data.get("categories", []):
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(name)
    lines = [f"Skill inventory: {len(inv)} skills"]
    for cat, skills in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        lines.append(f"  {cat}: {len(skills)} skills")
    lines.append("")
    lines.append("Top skills (by priority):")
    for name, data in list(inv.items())[:20]:
        c = data.get("project_count", 0)
        v = data.get("cv_count", 0)
        g = data.get("github_count", 0)
        lines.append(f"  {name}: {c} projects, {v} CVs, {g} GH repos")
    return "\n".join(lines)


if __name__ == "__main__":
    inv = build_inventory()
    save_inventory(inv)
    print(get_summary())
