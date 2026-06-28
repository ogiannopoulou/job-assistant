"""CV Parser — extracts text from PDF CV files for skill analysis."""

import os
import json
import re
from pathlib import Path
from pdfminer.high_level import extract_text

DATA_DIR = Path(__file__).parent / "data"
CV_TEXT_DIR = DATA_DIR / "cv_texts"
CV_TEXT_DIR.mkdir(parents=True, exist_ok=True)

CV_SOURCE_DIR = Path(os.path.expanduser("~/Downloads"))

SKILL_PATTERNS = {
    "legal_administrative": r"\b(Legal|Administrative|Law|Legal procedures|Certification|Public records|"
                            r"Trial office|Administrative law|Document analysis|Court|Justice|"
                            r"Cancelliere|Funzionario|Amministrativo|Giuridico|Normativa|"
                            r"Contratti|Procurement|Compliance|GDPR|AML|Antiriciclaggio)\b",
    "sales_customer_service": r"\b(Sales|Sales management|CRM|Customer service|Customer relationship|"
                              r"Negotiation|Account management|After-sales|Customer loyalty|"
                              r"Sales targets|Order management|Supplier relations|"
                              r"Business development|Key account|Retail|Commerciale|Vendite)\b",
    "it_tools": r"\b(Microsoft Office|Office|Excel|Word|PowerPoint|Windows|Mac OS|"
                r"Electronic invoicing|Fatturazione|SAP|Salesforce|HubSpot|Zendesk)\b",
    "soft_skills": r"\b(Communication|Problem.solving|Organization|Time management|"
                   r"Multitasking|Teamwork|Leadership|Negotiation|Presentation|"
                   r"Interpersonal|Analytical|Decision.making|Planning)\b",
    "languages": r"\b(Italian|English|German|French|Spanish|Greek|Native|B2|C1|C2|Fluente|Madrelingua)\b",
    "education": r"\b(Master|Bachelor|Degree|Laurea|Diploma|Law|Giurisprudenza|"
                 r"Academic exchange|Humboldt|Sapienza|University|Universit)\b",
    "sectors": r"\b(Justice|Public administration|PA|Ministry|Court|Tribunale|"
               r"Insurance|Finance|Banking|Tourism|Export|Legal|Law firm|"
               r"Consulting|HR|Recruitment|Events|Cultural heritage)\b",
}


def extract_text_from_pdf(path: str) -> str:
    try:
        text = extract_text(path)
        return text
    except Exception as e:
        print(f"  [!] Failed to extract {path}: {e}")
        return ""


def normalize_cv_key(filename: str) -> str:
    name = filename.replace(".pdf", "").replace(".PDF", "")
    name = re.sub(r'\s*\(\d+\)', '', name)
    return name.strip()


def extract_skills_from_text(text: str) -> dict:
    skills = {}
    for category, pattern in SKILL_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        unique = list(set(m.strip() for m in matches))
        skills[category] = sorted(unique)
    return skills


def extract_sections(text: str) -> dict:
    sections = {}
    current_section = "header"
    current_text = []
    section_keywords = [
        "education", "experience", "employment", "work experience",
        "professional experience", "professional profile",
        "skills", "key skills", "technical skills",
        "languages", "certifications", "training",
        "other information", "additional skills",
        "current position", "work experience",
    ]
    lines = text.split("\n")
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        lower = line_stripped.lower()
        is_section = False
        for kw in section_keywords:
            if lower.startswith(kw) or lower == kw or lower.startswith(kw + ":"):
                if current_text:
                    sections[current_section] = "\n".join(current_text)
                current_section = kw
                current_text = []
                is_section = True
                break
        if not is_section:
            current_text.append(line_stripped)
    if current_text:
        sections[current_section] = "\n".join(current_text)
    return sections


def scan_all_cvs() -> list:
    results = []
    for f in sorted(CV_SOURCE_DIR.glob("*_CV_*.pdf")):
        name = f.name
        key = normalize_cv_key(name)
        print(f"  Scanning: {name}")
        text = extract_text_from_pdf(str(f))
        if not text:
            continue
        out_path = CV_TEXT_DIR / f"{key}.txt"
        out_path.write_text(text, encoding="utf-8")
        skills = extract_skills_from_text(text)
        sections = extract_sections(text)
        results.append({
            "cv_key": key,
            "filename": name,
            "path": str(f),
            "text_path": str(out_path),
            "text_length": len(text),
            "skills": skills,
            "sections_found": list(sections.keys()),
            "has_experience": "experience" in sections or "employment" in sections or "work" in sections,
            "has_education": "education" in sections,
            "has_publications": "publications" in sections,
        })
    return results


def save_results(results: list):
    path = DATA_DIR / "cv_inventory.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved {len(results)} CVs to {path}")
    return path


def load_results() -> list:
    path = DATA_DIR / "cv_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def get_summary() -> str:
    cvs = load_results()
    if not cvs:
        return "No CVs parsed yet."
    all_skills = {}
    for cv in cvs:
        for cat, skills in cv.get("skills", {}).items():
            if cat not in all_skills:
                all_skills[cat] = set()
            all_skills[cat].update(skills)
    lines = [f"CVs parsed: {len(cvs)}"]
    for cat, skills in all_skills.items():
        lines.append(f"  {cat}: {', '.join(sorted(skills)[:10])}")
        if len(skills) > 10:
            lines[-1] += f" ... and {len(skills)-10} more"
    return "\n".join(lines)


if __name__ == "__main__":
    print("Scanning CVs...")
    results = scan_all_cvs()
    save_results(results)
    print(get_summary())
